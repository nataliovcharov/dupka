import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Report, ReportStatus, ReportVisibility
from app.services.detector import Detector
from app.services.issues import attach_to_issue
from app.services.moderation import confident, decide_visibility
from app.services.privacy import PrivacyDetector, anonymize
from app.services.safety import SafetyChecker
from app.services.severity import summarize
from app.storage import Storage, get_storage

logger = logging.getLogger("dupka.worker")
POLL_SECONDS = 2


def claim_next_report(db: Session) -> Report | None:
    """Take the oldest pending report and mark it as processing.

    SKIP LOCKED lets several workers run at once without taking the same report.
    """
    report = db.scalars(
        select(Report)
        .where(Report.status == ReportStatus.PENDING)
        .order_by(Report.created_at)
        .limit(1)
        .with_for_update(skip_locked=True)
    ).first()
    if report is not None:
        report.status = ReportStatus.PROCESSING
        db.commit()
    return report


def process_report(
    db: Session,
    report: Report,
    detector: Detector,
    safety_checker: SafetyChecker,
    storage: Storage,
    privacy_detector: PrivacyDetector,
) -> None:
    """Check one report's photo, look for damage, and save the result."""
    try:
        image = storage.load(report.photo_key)
        # blur first and keep only the blurred photo.
        # if this fails the report fails, so it never goes public unblurred
        image, report.privacy = anonymize(image, privacy_detector)
        storage.save(report.photo_key, image)
        safety = safety_checker.check(image)
        report.safety = safety.model_dump()
        # no need to look for damage in a photo that will be hidden anyway
        detections = [] if safety.unsafe else detector.detect(image)
        found = confident(detections, settings.min_detection_confidence)
        # keep every detection, low confidence ones help when tuning the threshold
        report.detections = [d.model_dump() for d in detections]
        report.damage_type, report.severity = summarize(found)
        report.visibility = decide_visibility(safety, found)
        if report.visibility == ReportVisibility.PUBLIC:
            attach_to_issue(db, report)
        report.status = ReportStatus.DONE
        logger.info(
            "report %s: %s, %s, %d detections",
            report.id,
            report.visibility,
            report.severity or "no severity",
            len(found),
        )
    except Exception:
        logger.exception("failed to process report %s", report.id)
        # a failed query leaves the transaction unusable, start clean
        db.rollback()
        report.status = ReportStatus.FAILED
    db.commit()


def run_once(
    detector: Detector,
    safety_checker: SafetyChecker,
    storage: Storage,
    privacy_detector: PrivacyDetector,
) -> bool:
    """Process one report if there is one. Returns False when the queue is empty."""
    with SessionLocal() as db:
        report = claim_next_report(db)
        if report is None:
            return False
        process_report(db, report, detector, safety_checker, storage, privacy_detector)
        return True


def run_forever(
    detector: Detector,
    safety_checker: SafetyChecker,
    storage: Storage,
    privacy_detector: PrivacyDetector,
) -> None:
    logger.info("worker started")
    while True:
        if not run_once(detector, safety_checker, storage, privacy_detector):
            time.sleep(POLL_SECONDS)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    # imported here so the API and the tests don't need PyTorch
    from app.services.clip_safety import ClipSafetyChecker
    from app.services.opencv_privacy import OpenCvPrivacyDetector
    from app.services.yolo_detector import YoloDetector

    logger.info("loading models")
    detector = YoloDetector(settings.model_path)
    safety_checker = ClipSafetyChecker()
    privacy_detector = OpenCvPrivacyDetector(
        settings.face_model_path,
        settings.plate_model_path,
        settings.face_threshold,
        settings.plate_threshold,
    )
    try:
        run_forever(detector, safety_checker, get_storage(), privacy_detector)
    except KeyboardInterrupt:
        logger.info("worker stopped")


if __name__ == "__main__":
    # uv run --group worker python -m app.worker
    main()

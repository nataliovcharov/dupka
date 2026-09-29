import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Report, ReportStatus
from app.services.detector import Detector
from app.services.moderation import confident, decide_visibility
from app.services.safety import SafetyChecker
from app.services.severity import summarize
from app.storage import Storage

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
) -> None:
    """Check one report's photo, look for damage, and save the result."""
    try:
        image = storage.load(report.photo_key)
        safety = safety_checker.check(image)
        report.safety = safety.model_dump()
        # no need to look for damage in a photo that will be hidden anyway
        detections = [] if safety.unsafe else detector.detect(image)
        found = confident(detections, settings.min_detection_confidence)
        # keep every detection, low confidence ones help when tuning the threshold
        report.detections = [d.model_dump() for d in detections]
        report.damage_type, report.severity = summarize(found)
        report.visibility = decide_visibility(safety, found)
        report.status = ReportStatus.DONE
    except Exception:
        logger.exception("failed to process report %s", report.id)
        report.status = ReportStatus.FAILED
    db.commit()


def run_once(
    detector: Detector, safety_checker: SafetyChecker, storage: Storage
) -> bool:
    """Process one report if there is one. Returns False when the queue is empty."""
    with SessionLocal() as db:
        report = claim_next_report(db)
        if report is None:
            return False
        process_report(db, report, detector, safety_checker, storage)
        return True


def run_forever(
    detector: Detector, safety_checker: SafetyChecker, storage: Storage
) -> None:
    logger.info("worker started")
    while True:
        if not run_once(detector, safety_checker, storage):
            time.sleep(POLL_SECONDS)

from app.db.session import SessionLocal
from app.models import Report, ReportStatus, ReportVisibility
from app.services.detector import Detection
from app.services.safety import SafetyResult
from app.services.severity import summarize
from app.storage import LocalStorage
from app.worker import claim_next_report, process_report

SKOPJE = "SRID=4326;POINT(21.4254 41.9965)"

SAFE_ROAD = SafetyResult(
    scores={"road": 0.9, "unsafe": 0.0, "other": 0.1}, unsafe=False, is_road=True
)
NOT_A_ROAD = SafetyResult(
    scores={"road": 0.1, "unsafe": 0.0, "other": 0.9}, unsafe=False, is_road=False
)
UNSAFE = SafetyResult(
    scores={"road": 0.1, "unsafe": 0.8, "other": 0.1}, unsafe=True, is_road=False
)


class FakeDetector:
    """Returns fixed detections, so tests don't need the real model."""

    def __init__(self, detections):
        self.detections = detections
        self.calls = 0

    def detect(self, image: bytes) -> list[Detection]:
        self.calls += 1
        return self.detections


class FakeSafetyChecker:
    """Returns a fixed result, so tests don't need CLIP."""

    def __init__(self, result=SAFE_ROAD):
        self.result = result

    def check(self, image: bytes) -> SafetyResult:
        return self.result


def crack(size=0.1):
    return Detection(damage_type="D00", confidence=0.8, box=(0.1, 0.1, 0.1 + size, 0.2))


def pothole(size=0.3):
    return Detection(
        damage_type="D40", confidence=0.9, box=(0.2, 0.2, 0.2 + size, 0.2 + size)
    )


def test_no_damage_gives_no_type_or_severity():
    assert summarize([]) == (None, None)


def test_pothole_outranks_crack():
    assert summarize([crack(), pothole()]) == ("D40", "high")


def test_small_pothole_is_medium():
    assert summarize([pothole(size=0.1)]) == ("D40", "medium")


def test_crack_only_is_low():
    assert summarize([crack()]) == ("D00", "low")


def process_with(tmp_path, detector, safety=SAFE_ROAD) -> Report:
    """Run the worker on one report with fake models."""
    storage = LocalStorage(tmp_path)
    storage.save("reports/test.jpg", b"photo bytes")

    with SessionLocal() as db:
        report = Report(
            photo_key="reports/test.jpg",
            location=SKOPJE,
            status=ReportStatus.PROCESSING,
        )
        db.add(report)
        db.commit()
        process_report(db, report, detector, FakeSafetyChecker(safety), storage)
        db.refresh(report)
        db.expunge(report)
        return report


def test_road_with_damage_becomes_public(tmp_path):
    report = process_with(tmp_path, FakeDetector([pothole()]))

    assert report.status == ReportStatus.DONE
    assert report.visibility == ReportVisibility.PUBLIC
    assert report.damage_type == "D40"
    assert report.severity == "high"
    assert len(report.detections) == 1
    assert report.safety["scores"]["road"] == 0.9


def test_photo_without_damage_goes_to_review(tmp_path):
    report = process_with(tmp_path, FakeDetector([]))

    assert report.status == ReportStatus.DONE
    assert report.visibility == ReportVisibility.NEEDS_REVIEW
    assert report.severity is None


def test_low_confidence_damage_goes_to_review(tmp_path):
    unsure = Detection(damage_type="D40", confidence=0.1, box=(0.2, 0.2, 0.6, 0.6))
    report = process_with(tmp_path, FakeDetector([unsure]))

    assert report.visibility == ReportVisibility.NEEDS_REVIEW
    assert report.severity is None
    assert len(report.detections) == 1  # still saved, for tuning the threshold


def test_photo_that_is_not_a_road_goes_to_review(tmp_path):
    report = process_with(tmp_path, FakeDetector([pothole()]), safety=NOT_A_ROAD)

    assert report.visibility == ReportVisibility.NEEDS_REVIEW


def test_unsafe_photo_is_hidden_without_running_detector(tmp_path):
    detector = FakeDetector([pothole()])
    report = process_with(tmp_path, detector, safety=UNSAFE)

    assert report.status == ReportStatus.DONE
    assert report.visibility == ReportVisibility.HIDDEN
    assert report.safety["unsafe"] is True
    assert detector.calls == 0
    assert report.detections == []


def test_process_report_marks_failure_when_photo_missing(tmp_path):
    storage = LocalStorage(tmp_path)  # empty, so loading the photo fails

    with SessionLocal() as db:
        report = Report(
            photo_key="reports/missing.jpg",
            location=SKOPJE,
            status=ReportStatus.PROCESSING,
        )
        db.add(report)
        db.commit()

        process_report(db, report, FakeDetector([]), FakeSafetyChecker(), storage)
        db.refresh(report)

        assert report.status == ReportStatus.FAILED
        assert report.visibility == ReportVisibility.PENDING


def test_claim_takes_oldest_pending_report_first():
    with SessionLocal() as db:
        first = Report(photo_key="reports/1.jpg", location=SKOPJE)
        db.add(first)
        db.commit()
        second = Report(photo_key="reports/2.jpg", location=SKOPJE)
        db.add(second)
        db.commit()

        claimed = claim_next_report(db)
        assert claimed.id == first.id
        assert claimed.status == ReportStatus.PROCESSING

        assert claim_next_report(db).id == second.id
        assert claim_next_report(db) is None  # queue is empty

from app.db.session import SessionLocal
from app.models import Report, ReportStatus
from app.services.detector import Detection
from app.services.severity import summarize
from app.storage import LocalStorage
from app.worker import process_report

SKOPJE = "SRID=4326;POINT(21.4254 41.9965)"


class FakeDetector:
    """Returns fixed detections, so tests don't need the real model."""

    def __init__(self, detections):
        self.detections = detections

    def detect(self, image: bytes) -> list[Detection]:
        return self.detections


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


def test_process_report_saves_results(tmp_path):
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

        process_report(db, report, FakeDetector([pothole()]), storage)
        db.refresh(report)

        assert report.status == ReportStatus.DONE
        assert report.damage_type == "D40"
        assert report.severity == "high"
        assert len(report.detections) == 1


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

        process_report(db, report, FakeDetector([]), storage)
        db.refresh(report)

        assert report.status == ReportStatus.FAILED

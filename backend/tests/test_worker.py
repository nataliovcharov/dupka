import io

from PIL import Image, ImageDraw, ImageStat

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


class FakePrivacyDetector:
    """Finds fixed faces and plates, so tests don't need the real models."""

    def __init__(self, faces=(), plates=(), error=None):
        self.faces, self.plates, self.error = list(faces), list(plates), error

    def find(self, photo):
        if self.error:
            raise self.error
        return self.faces, self.plates


def make_jpeg() -> bytes:
    """A black and white checkerboard, full of detail a blur would remove."""
    photo = Image.new("RGB", (64, 64), "white")
    draw = ImageDraw.Draw(photo)
    for x in range(0, 64, 8):
        for y in range(0, 64, 8):
            if (x + y) % 16 == 0:
                draw.rectangle((x, y, x + 7, y + 7), fill="black")
    buffer = io.BytesIO()
    photo.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def detail(data: bytes, box) -> float:
    photo = Image.open(io.BytesIO(data)).convert("L")
    return ImageStat.Stat(photo.crop(box)).stddev[0]


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


def process_with(tmp_path, detector, safety=SAFE_ROAD, privacy=None) -> Report:
    """Run the worker on one report with fake models."""
    storage = LocalStorage(tmp_path)
    storage.save("reports/test.jpg", make_jpeg())

    with SessionLocal() as db:
        report = Report(
            photo_key="reports/test.jpg",
            location=SKOPJE,
            status=ReportStatus.PROCESSING,
        )
        db.add(report)
        db.commit()
        process_report(
            db,
            report,
            detector,
            FakeSafetyChecker(safety),
            storage,
            privacy or FakePrivacyDetector(),
        )
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

        process_report(
            db,
            report,
            FakeDetector([]),
            FakeSafetyChecker(),
            storage,
            FakePrivacyDetector(),
        )
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


def test_public_report_joins_an_issue(tmp_path):
    report = process_with(tmp_path, FakeDetector([pothole()]))

    assert report.issue_id is not None


def test_report_in_review_has_no_issue(tmp_path):
    report = process_with(tmp_path, FakeDetector([]))

    assert report.issue_id is None


def test_only_the_blurred_photo_is_kept(tmp_path):
    privacy = FakePrivacyDetector(faces=[(5, 5, 30, 30)], plates=[(35, 40, 60, 50)])
    report = process_with(tmp_path, FakeDetector([pothole()]), privacy=privacy)

    assert report.privacy == {"faces": 1, "plates": 1}
    # the stored photo was replaced by the blurred one
    stored = (tmp_path / "reports" / "test.jpg").read_bytes()
    face = (8, 8, 28, 28)
    assert detail(stored, face) < detail(make_jpeg(), face) / 4


def test_report_fails_when_blurring_fails(tmp_path):
    privacy = FakePrivacyDetector(error=RuntimeError("model broke"))
    report = process_with(tmp_path, FakeDetector([pothole()]), privacy=privacy)

    assert report.status == ReportStatus.FAILED
    assert report.visibility == ReportVisibility.PENDING  # never public unblurred
    assert report.issue_id is None

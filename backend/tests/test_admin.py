import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models import Issue, Report, ReportStatus, ReportVisibility, Review
from app.storage import LocalStorage, get_storage

client = TestClient(app)

TOKEN = "test-admin-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
SKOPJE = "SRID=4326;POINT(21.4254 41.9965)"
START = datetime(2026, 9, 1, tzinfo=UTC)
PHOTO = b"\xff\xd8 not a real jpeg"


@pytest.fixture(autouse=True)
def admin_token(monkeypatch):
    # never read the real token from .env
    monkeypatch.setattr(settings, "admin_token", SecretStr(TOKEN))


@pytest.fixture(autouse=True)
def tmp_storage(tmp_path):
    storage = LocalStorage(tmp_path)
    app.dependency_overrides[get_storage] = lambda: storage
    yield storage
    app.dependency_overrides.clear()


def make_report(
    storage: LocalStorage | None = None,
    visibility: ReportVisibility = ReportVisibility.NEEDS_REVIEW,
    status: ReportStatus = ReportStatus.DONE,
    minutes: int = 0,
) -> uuid.UUID:
    """Save a report as if the worker had already checked it."""
    photo_key = f"reports/{uuid.uuid4()}.jpg"
    if storage:
        storage.save(photo_key, PHOTO)
    with SessionLocal() as db:
        report = Report(
            status=status,
            visibility=visibility,
            location=SKOPJE,
            photo_key=photo_key,
            detections=[
                {"damage_type": "D20", "confidence": 0.3, "box": [0.1, 0.2, 0.5, 0.6]}
            ],
            safety={"scores": {"road": 0.98}},
            privacy={"faces": 0, "plates": 0},
            damage_type="D20",
            severity="medium",
            # fixed times, so ordering tests don't depend on timing
            created_at=START + timedelta(minutes=minutes),
        )
        db.add(report)
        db.commit()
        return report.id


def review(report_id, **body):
    return client.post(f"/admin/reports/{report_id}/review", json=body, headers=AUTH)


# auth


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/admin/reports"),
        ("GET", "/admin/reports/{id}/photo"),
        ("POST", "/admin/reports/{id}/review"),
    ],
)
@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer wrong"}, {"Authorization": f"Basic {TOKEN}"}],
    ids=["no-header", "wrong-token", "basic-scheme"],
)
def test_admin_routes_need_the_token(method, path, headers):
    report_id = make_report()
    response = client.request(
        method,
        path.format(id=report_id),
        headers=headers,
        json={"decision": "reject"},
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("configured", [None, SecretStr("")], ids=["unset", "empty"])
def test_admin_is_off_without_a_configured_token(monkeypatch, configured):
    monkeypatch.setattr(settings, "admin_token", configured)
    assert client.get("/admin/reports", headers=AUTH).status_code == 401


# list


def test_list_filters_by_visibility_oldest_first():
    newer = make_report(minutes=2)
    older = make_report(minutes=1)
    make_report(visibility=ReportVisibility.PUBLIC)

    response = client.get(
        "/admin/reports", params={"visibility": "needs_review"}, headers=AUTH
    )
    assert response.status_code == 200
    assert [r["id"] for r in response.json()] == [str(older), str(newer)]


def test_list_filters_by_status():
    failed = make_report(
        status=ReportStatus.FAILED, visibility=ReportVisibility.PENDING
    )
    make_report()

    response = client.get("/admin/reports", params={"status": "failed"}, headers=AUTH)
    assert [r["id"] for r in response.json()] == [str(failed)]


def test_list_includes_what_a_reviewer_needs():
    make_report()

    report = client.get("/admin/reports", headers=AUTH).json()[0]
    assert report["detections"][0]["damage_type"] == "D20"
    assert report["safety"]["scores"]["road"] == 0.98
    assert report["last_review"] is None


def test_list_shows_last_review():
    report_id = make_report()
    review(report_id, decision="reject")

    response = client.get(
        "/admin/reports", params={"visibility": "hidden"}, headers=AUTH
    )
    report = response.json()[0]
    assert report["id"] == str(report_id)
    assert report["last_review"]["decision"] == "reject"


# photo


def test_photo_is_private(tmp_storage):
    report_id = make_report(tmp_storage)

    response = client.get(f"/admin/reports/{report_id}/photo", headers=AUTH)
    assert response.status_code == 200
    assert response.content == PHOTO
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["cache-control"] == "private, no-store"


def test_photo_missing_from_storage_returns_404():
    report_id = make_report()  # nothing saved in storage

    response = client.get(f"/admin/reports/{report_id}/photo", headers=AUTH)
    assert response.status_code == 404


def test_unknown_report_returns_404():
    unknown = uuid.uuid4()
    assert (
        client.get(f"/admin/reports/{unknown}/photo", headers=AUTH).status_code == 404
    )
    assert review(unknown, decision="reject").status_code == 404


# review


def test_approve_publishes_with_corrections():
    report_id = make_report()

    response = review(report_id, decision="approve", damage_type="D40", severity="high")
    assert response.status_code == 200
    body = response.json()
    assert body["visibility"] == "public"
    assert (body["damage_type"], body["severity"]) == ("D40", "high")
    # the model's answer is kept for training
    assert body["last_review"]["model_damage_type"] == "D20"
    assert body["last_review"]["model_severity"] == "medium"
    # and the public api shows it now
    assert client.get(f"/reports/{report_id}").status_code == 200


def test_reject_hides_report():
    report_id = make_report()

    body = review(
        report_id, decision="reject", damage_type="D40", severity="high"
    ).json()
    assert body["visibility"] == "hidden"
    assert body["last_review"]["decision"] == "reject"
    assert body["last_review"]["damage_type"] is None
    assert client.get(f"/reports/{report_id}").status_code == 404


def test_second_review_keeps_the_models_first_answer():
    report_id = make_report()
    review(report_id, decision="approve", damage_type="D40", severity="high")
    review(report_id, decision="approve", damage_type="D00", severity="low")

    with SessionLocal() as db:
        rows = db.scalars(
            select(Review)
            .where(Review.report_id == report_id)
            .order_by(Review.created_at)
        ).all()
    assert len(rows) == 2
    assert all(
        (r.model_damage_type, r.model_severity) == ("D20", "medium") for r in rows
    )
    assert rows[-1].damage_type == "D00"


@pytest.mark.parametrize(
    "body",
    [
        {"decision": "approve"},
        {"decision": "approve", "damage_type": "D40"},
        {"decision": "approve", "damage_type": "D99", "severity": "high"},
        {"decision": "approve", "damage_type": "D40", "severity": "huge"},
        {"decision": "maybe"},
    ],
)
def test_invalid_review_returns_422(body):
    assert review(make_report(), **body).status_code == 422


@pytest.mark.parametrize("status", [ReportStatus.PENDING, ReportStatus.PROCESSING])
def test_cannot_review_while_processing(status):
    report_id = make_report(status=status, visibility=ReportVisibility.PENDING)
    assert review(report_id, decision="reject").status_code == 409


def test_approve_and_reject_keep_issues_in_step():
    report_id = make_report()

    review(report_id, decision="approve", damage_type="D40", severity="high")
    with SessionLocal() as db:
        issue_id = db.get(Report, report_id).issue_id
        assert issue_id is not None
        assert db.get(Issue, issue_id).severity == "high"

    review(report_id, decision="reject")
    with SessionLocal() as db:
        assert db.get(Report, report_id).issue_id is None
        assert db.get(Issue, issue_id) is None  # it had no other reports


def test_unblurred_report_cannot_be_approved():
    report_id = make_report(status=ReportStatus.FAILED)
    with SessionLocal() as db:
        db.get(Report, report_id).privacy = None  # blurring never ran
        db.commit()

    response = review(report_id, decision="approve", damage_type="D40", severity="high")
    assert response.status_code == 409
    # rejecting is still fine
    assert review(report_id, decision="reject").status_code == 200

import io
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.db.session import SessionLocal
from app.main import app
from app.models import Report, ReportVisibility
from app.storage import LocalStorage, get_storage

client = TestClient(app)

SKOPJE = {"latitude": "41.9965", "longitude": "21.4254"}


def make_jpeg() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), "gray").save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def tmp_storage(tmp_path):
    # save photos in a temporary folder instead of the real storage
    app.dependency_overrides[get_storage] = lambda: LocalStorage(tmp_path)
    yield tmp_path
    app.dependency_overrides.clear()


def test_create_report(tmp_storage):
    response = client.post(
        "/reports",
        data=SKOPJE,
        files={"photo": ("road.jpg", make_jpeg(), "image/jpeg")},
    )
    assert response.status_code == 201
    report = response.json()
    assert report["status"] == "pending"
    assert report["visibility"] == "pending"
    assert report["latitude"] == pytest.approx(41.9965)
    assert report["longitude"] == pytest.approx(21.4254)
    assert (tmp_storage / "reports" / f"{report['id']}.jpg").exists()

    # not public yet, so it can't be fetched by id
    assert client.get(f"/reports/{report['id']}").status_code == 404


def test_rejects_location_outside_north_macedonia():
    paris = {"latitude": "48.8566", "longitude": "2.3522"}
    response = client.post(
        "/reports", data=paris, files={"photo": ("road.jpg", make_jpeg(), "image/jpeg")}
    )
    assert response.status_code == 422


def test_rejects_file_that_is_not_an_image():
    response = client.post(
        "/reports",
        data=SKOPJE,
        files={"photo": ("road.jpg", b"not an image", "image/jpeg")},
    )
    assert response.status_code == 422


def test_rejects_unsupported_file_type():
    response = client.post(
        "/reports",
        data=SKOPJE,
        files={"photo": ("notes.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 415


def test_unknown_report_returns_404():
    response = client.get(f"/reports/{uuid.uuid4()}")
    assert response.status_code == 404


# bbox strings: min_lon,min_lat,max_lon,max_lat
CENTRAL_SKOPJE = "21.38,41.97,21.47,42.02"
BITOLA = "21.30,41.00,21.37,41.05"


def create_report_in_skopje(visibility=ReportVisibility.PUBLIC) -> str:
    response = client.post(
        "/reports",
        data=SKOPJE,
        files={"photo": ("road.jpg", make_jpeg(), "image/jpeg")},
    )
    report_id = response.json()["id"]
    # stand in for the worker, which decides the visibility
    with SessionLocal() as db:
        db.get(Report, uuid.UUID(report_id)).visibility = visibility
        db.commit()
    return report_id


def test_list_reports_returns_geojson_inside_bbox():
    report_id = create_report_in_skopje()

    response = client.get("/reports", params={"bbox": CENTRAL_SKOPJE})
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"

    ids = [f["properties"]["id"] for f in body["features"]]
    assert report_id in ids
    feature = body["features"][ids.index(report_id)]
    assert feature["geometry"]["coordinates"] == pytest.approx([21.4254, 41.9965])


def test_list_reports_excludes_reports_outside_bbox():
    report_id = create_report_in_skopje()

    response = client.get("/reports", params={"bbox": BITOLA})
    ids = [f["properties"]["id"] for f in response.json()["features"]]
    assert report_id not in ids


def test_list_reports_rejects_invalid_bbox():
    response = client.get("/reports", params={"bbox": "not,a,valid,bbox"})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "visibility",
    [
        ReportVisibility.PENDING,
        ReportVisibility.NEEDS_REVIEW,
        ReportVisibility.HIDDEN,
    ],
)
def test_list_reports_shows_only_public_reports(visibility):
    report_id = create_report_in_skopje(visibility)

    response = client.get("/reports", params={"bbox": CENTRAL_SKOPJE})
    ids = [f["properties"]["id"] for f in response.json()["features"]]
    assert report_id not in ids


def test_get_public_report_by_id():
    report_id = create_report_in_skopje()

    response = client.get(f"/reports/{report_id}")
    assert response.status_code == 200
    assert response.json()["id"] == report_id


@pytest.mark.parametrize(
    "visibility",
    [
        ReportVisibility.PENDING,
        ReportVisibility.NEEDS_REVIEW,
        ReportVisibility.HIDDEN,
    ],
)
def test_get_report_hides_non_public_reports(visibility):
    report_id = create_report_in_skopje(visibility)

    assert client.get(f"/reports/{report_id}").status_code == 404


def test_public_report_photo(tmp_storage):
    report_id = create_report_in_skopje()

    response = client.get(f"/reports/{report_id}/photo")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["cache-control"] == "public, max-age=300"
    saved = tmp_storage / "reports" / f"{report_id}.jpg"
    assert response.content == saved.read_bytes()


@pytest.mark.parametrize(
    "visibility",
    [
        ReportVisibility.PENDING,
        ReportVisibility.NEEDS_REVIEW,
        ReportVisibility.HIDDEN,
    ],
)
def test_photo_of_non_public_report_returns_404(visibility):
    report_id = create_report_in_skopje(visibility)

    assert client.get(f"/reports/{report_id}/photo").status_code == 404


def test_missing_photo_returns_404(tmp_storage):
    report_id = create_report_in_skopje()
    (tmp_storage / "reports" / f"{report_id}.jpg").unlink()

    assert client.get(f"/reports/{report_id}/photo").status_code == 404

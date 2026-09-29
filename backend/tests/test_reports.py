import io
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
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


def test_create_and_get_report(tmp_storage):
    response = client.post(
        "/reports",
        data=SKOPJE,
        files={"photo": ("road.jpg", make_jpeg(), "image/jpeg")},
    )
    assert response.status_code == 201
    report = response.json()
    assert report["status"] == "pending"
    assert report["latitude"] == pytest.approx(41.9965)
    assert report["longitude"] == pytest.approx(21.4254)
    assert (tmp_storage / "reports" / f"{report['id']}.jpg").exists()

    fetched = client.get(f"/reports/{report['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == report["id"]


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

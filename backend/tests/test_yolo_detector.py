"""Runs the real model on a real road photo.

Skipped unless the worker dependencies, the model and the dataset are on
this machine, so CI doesn't need them. Run it with:
uv run --group worker pytest tests/test_yolo_detector.py
"""

import io
from pathlib import Path

import pytest
from PIL import Image

from app.core.config import settings

pytest.importorskip("ultralytics")

ROAD_PHOTO = Path("../ml/data/yolo/images/test/Czech_000006.jpg")

pytestmark = pytest.mark.skipif(
    not settings.model_path.exists() or not ROAD_PHOTO.exists(),
    reason="needs the trained model and the dataset",
)


@pytest.fixture(scope="module")
def detector():
    from app.services.yolo_detector import YoloDetector

    return YoloDetector(settings.model_path)


def test_detections_have_known_types_and_valid_boxes(detector):
    detections = detector.detect(ROAD_PHOTO.read_bytes())

    for d in detections:
        assert d.damage_type in {"D00", "D10", "D20", "D40"}
        assert 0.1 <= d.confidence <= 1
        x1, y1, x2, y2 = d.box
        assert 0 <= x1 < x2 <= 1
        assert 0 <= y1 < y2 <= 1


def test_blank_image_has_no_damage(detector):
    buffer = io.BytesIO()
    Image.new("RGB", (640, 640), "gray").save(buffer, format="JPEG")

    assert detector.detect(buffer.getvalue()) == []

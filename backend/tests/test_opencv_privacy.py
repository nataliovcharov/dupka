"""Runs the real face and plate models.

Skipped unless the worker dependencies and both models are on this machine,
so CI doesn't need them. Run it with:
uv run --group worker pytest tests/test_opencv_privacy.py
"""

import pytest
from PIL import Image

from app.core.config import settings

pytest.importorskip("cv2")
pytest.importorskip("onnxruntime")

pytestmark = pytest.mark.skipif(
    not settings.face_model_path.exists() or not settings.plate_model_path.exists(),
    reason="needs the face and plate models",
)


@pytest.fixture(scope="module")
def detector():
    from app.services.opencv_privacy import OpenCvPrivacyDetector

    return OpenCvPrivacyDetector(
        settings.face_model_path,
        settings.plate_model_path,
        settings.face_threshold,
        settings.plate_threshold,
    )


@pytest.mark.parametrize("size", [(640, 480), (2048, 1152), (480, 900)])
def test_empty_photo_has_no_faces_or_plates(detector, size):
    faces, plates = detector.find(Image.new("RGB", size, "gray"))

    assert faces == []
    assert plates == []

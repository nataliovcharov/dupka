"""Face and license plate detection for blurring.

Faces: YuNet (OpenCV, MIT). Plates: YOLOv9 from open-image-models (MIT), run
with onnxruntime. Pre and post processing follow open-image-models, we don't
install the package because it pulls in a second copy of OpenCV.

Needs the worker dependencies: uv sync --group worker
"""

from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image

from app.services.privacy import Box

# yunet finds faces up to about 300 px, so close-ups are also looked for
# on a copy this size
SMALL_SIDE = 640


class OpenCvPrivacyDetector:
    def __init__(
        self,
        face_model_path: Path,
        plate_model_path: Path,
        face_threshold: float,
        plate_threshold: float,
    ) -> None:
        for path in (face_model_path, plate_model_path):
            if not path.exists():
                raise FileNotFoundError(f"model not found at {path}")
        self.faces = cv2.FaceDetectorYN.create(
            str(face_model_path), "", (320, 320), face_threshold
        )
        self.plates = ort.InferenceSession(
            str(plate_model_path), providers=["CPUExecutionProvider"]
        )
        model_input = self.plates.get_inputs()[0]
        self.plate_input = model_input.name
        self.plate_size = model_input.shape[2]  # square, e.g. 608
        self.plate_threshold = plate_threshold

    def find(self, photo: Image.Image) -> tuple[list[Box], list[Box]]:
        bgr = cv2.cvtColor(np.asarray(photo.convert("RGB")), cv2.COLOR_RGB2BGR)
        return self.find_faces(bgr), self.find_plates(bgr)

    def find_faces(self, bgr: np.ndarray) -> list[Box]:
        boxes = self._faces_at_scale(bgr, 1.0)
        scale = SMALL_SIDE / max(bgr.shape[:2])
        if scale < 1:
            small = cv2.resize(bgr, None, fx=scale, fy=scale)
            # the same face can come back twice, blurring it twice is fine
            boxes += self._faces_at_scale(small, scale)
        return boxes

    def _faces_at_scale(self, bgr: np.ndarray, scale: float) -> list[Box]:
        height, width = bgr.shape[:2]
        self.faces.setInputSize((width, height))
        _, found = self.faces.detect(bgr)
        if found is None:
            return []
        return [
            (x / scale, y / scale, (x + w) / scale, (y + h) / scale)
            for x, y, w, h in found[:, :4].tolist()
        ]

    def find_plates(self, bgr: np.ndarray) -> list[Box]:
        # letterbox: scale to fit the square input, pad the rest with grey
        size = self.plate_size
        height, width = bgr.shape[:2]
        ratio = min(size / height, size / width)
        new_w, new_h = round(width * ratio), round(height * ratio)
        pad_x, pad_y = (size - new_w) // 2, (size - new_h) // 2
        padded = np.full((size, size, 3), 114, np.uint8)
        padded[pad_y : pad_y + new_h, pad_x : pad_x + new_w] = cv2.resize(
            bgr, (new_w, new_h)
        )
        batch = padded[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255

        # each row: batch index, x1, y1, x2, y2, class, score (nms is in the model)
        rows = self.plates.run(None, {self.plate_input: batch})[0].reshape(-1, 7)
        return [
            (
                (x1 - pad_x) / ratio,
                (y1 - pad_y) / ratio,
                (x2 - pad_x) / ratio,
                (y2 - pad_y) / ratio,
            )
            for _, x1, y1, x2, y2, _, score in rows.tolist()
            if score >= self.plate_threshold
        ]

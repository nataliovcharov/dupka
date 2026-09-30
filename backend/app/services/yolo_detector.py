"""Road damage detector using our trained YOLO model.

Needs the worker dependencies: uv sync --group worker
"""

import io
from pathlib import Path

from PIL import Image
from ultralytics import YOLO

from app.services.detector import Detection
from app.services.images import to_rgb


class YoloDetector:
    def __init__(self, model_path: Path, min_confidence: float = 0.1) -> None:
        if not model_path.exists():
            raise FileNotFoundError(f"model not found at {model_path}")
        self.model = YOLO(str(model_path))
        # keep low confidence detections too, the worker decides what counts.
        # they are saved with the report and help when tuning the threshold
        self.min_confidence = min_confidence

    def detect(self, image: bytes) -> list[Detection]:
        photo = to_rgb(Image.open(io.BytesIO(image)))
        result = self.model.predict(
            photo, imgsz=640, conf=self.min_confidence, verbose=False
        )[0]

        boxes = result.boxes
        return [
            Detection(
                damage_type=result.names[int(class_id)],
                confidence=round(confidence, 4),
                box=tuple(round(v, 4) for v in box),  # normalized x1, y1, x2, y2
            )
            for class_id, confidence, box in zip(
                boxes.cls.tolist(),
                boxes.conf.tolist(),
                boxes.xyxyn.tolist(),
                strict=True,
            )
        ]

"""Safety check with CLIP, a model that matches images to text descriptions.

Needs the worker dependencies: uv sync --group worker
"""

import io
import sys
from pathlib import Path

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from app.core.config import settings
from app.services.images import to_rgb
from app.services.safety import LABELS, SafetyResult, assess


class ClipSafetyChecker:
    def __init__(self, model_name: str = settings.clip_model) -> None:
        # downloaded once, then loaded from the local Hugging Face cache
        self.model = CLIPModel.from_pretrained(model_name).eval()
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.prompts = [prompt for _, prompt in LABELS]

    def check(self, image: bytes) -> SafetyResult:
        photo = to_rgb(Image.open(io.BytesIO(image)))
        inputs = self.processor(
            text=self.prompts, images=photo, return_tensors="pt", padding=True
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
        probabilities = outputs.logits_per_image.softmax(dim=1)[0].tolist()
        return assess(
            probabilities,
            unsafe_threshold=settings.unsafe_threshold,
            road_threshold=settings.road_threshold,
        )


if __name__ == "__main__":
    # try it on your own photos:
    # uv run --group worker python -m app.services.clip_safety photo1.jpg photo2.jpg
    checker = ClipSafetyChecker()
    for path in sys.argv[1:]:
        result = checker.check(Path(path).read_bytes())
        print(f"{path}: {result.model_dump()}")

from typing import Protocol

from pydantic import BaseModel


class Detection(BaseModel):
    """One piece of damage found in a photo.

    The box is normalized (0-1): x1, y1 (top left) and x2, y2 (bottom right).
    """

    damage_type: str
    confidence: float
    box: tuple[float, float, float, float]


class Detector(Protocol):
    """Anything that finds road damage in a photo."""

    def detect(self, image: bytes) -> list[Detection]: ...

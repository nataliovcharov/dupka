from app.models import ReportVisibility
from app.services.detector import Detection


def confident(detections: list[Detection], min_confidence: float) -> list[Detection]:
    """Keep only the detections the model is sure enough about."""
    return [d for d in detections if d.confidence >= min_confidence]


def decide_visibility(found: list[Detection]) -> ReportVisibility:
    """Public if the photo shows road damage, otherwise a person should check it.

    Selfies, memes, and blurry or dark photos end up in review.
    """
    return ReportVisibility.PUBLIC if found else ReportVisibility.NEEDS_REVIEW

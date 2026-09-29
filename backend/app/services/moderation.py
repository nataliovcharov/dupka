from app.models import ReportVisibility
from app.services.detector import Detection
from app.services.safety import SafetyResult


def confident(detections: list[Detection], min_confidence: float) -> list[Detection]:
    """Keep only the detections the model is sure enough about."""
    return [d for d in detections if d.confidence >= min_confidence]


def decide_visibility(safety: SafetyResult, found: list[Detection]) -> ReportVisibility:
    """Decide who can see a report.

    Unsafe photos are hidden. Photos that don't look like a road, or where
    no damage was found, wait for a person. Everything else is public.
    """
    if safety.unsafe:
        return ReportVisibility.HIDDEN
    if not safety.is_road or not found:
        return ReportVisibility.NEEDS_REVIEW
    return ReportVisibility.PUBLIC

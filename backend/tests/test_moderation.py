import pytest

from app.models import ReportVisibility
from app.services.detector import Detection
from app.services.moderation import decide_visibility
from app.services.safety import SafetyResult

DAMAGE = [Detection(damage_type="D40", confidence=0.9, box=(0.2, 0.2, 0.5, 0.5))]


def safety(unsafe: bool, is_road: bool) -> SafetyResult:
    return SafetyResult(scores={}, unsafe=unsafe, is_road=is_road)


@pytest.mark.parametrize(
    ("unsafe", "is_road", "found", "expected"),
    [
        (False, True, DAMAGE, ReportVisibility.PUBLIC),
        (False, True, [], ReportVisibility.NEEDS_REVIEW),
        (False, False, DAMAGE, ReportVisibility.NEEDS_REVIEW),
        (False, False, [], ReportVisibility.NEEDS_REVIEW),
        (True, True, DAMAGE, ReportVisibility.HIDDEN),
        (True, False, [], ReportVisibility.HIDDEN),
    ],
)
def test_decide_visibility(unsafe, is_road, found, expected):
    assert decide_visibility(safety(unsafe, is_road), found) == expected

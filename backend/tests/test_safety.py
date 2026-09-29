import pytest

from app.services.safety import LABELS, assess


def probabilities_for(**group_totals: float) -> list[float]:
    """Spread each group's total evenly over its prompts."""
    counts = {group: 0 for group in group_totals}
    for group, _ in LABELS:
        counts[group] += 1
    return [group_totals[group] / counts[group] for group, _ in LABELS]


def test_scores_add_up_per_group():
    result = assess(
        probabilities_for(road=0.7, unsafe=0.1, other=0.2),
        unsafe_threshold=0.2,
        road_threshold=0.5,
    )
    assert result.scores == pytest.approx({"road": 0.7, "unsafe": 0.1, "other": 0.2})


def test_clear_road_photo_is_safe_and_a_road():
    result = assess(
        probabilities_for(road=0.9, unsafe=0.01, other=0.09),
        unsafe_threshold=0.2,
        road_threshold=0.5,
    )
    assert not result.unsafe
    assert result.is_road


def test_unsafe_wins_even_when_it_looks_like_a_road():
    result = assess(
        probabilities_for(road=0.6, unsafe=0.3, other=0.1),
        unsafe_threshold=0.2,
        road_threshold=0.5,
    )
    assert result.unsafe


def test_selfie_is_not_a_road():
    result = assess(
        probabilities_for(road=0.1, unsafe=0.0, other=0.9),
        unsafe_threshold=0.2,
        road_threshold=0.5,
    )
    assert not result.is_road


def test_rejects_wrong_number_of_probabilities():
    with pytest.raises(ValueError):
        assess([0.5, 0.5], unsafe_threshold=0.2, road_threshold=0.5)

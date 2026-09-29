from typing import Protocol

from pydantic import BaseModel

# what CLIP compares each photo against, grouped by what we care about.
# the "other" group gives non-road photos somewhere to go, so they don't
# get counted as roads just because road was the closest match
PROMPTS: dict[str, list[str]] = {
    "road": [
        "a photo of a road",
        "a photo of a street",
        "a photo of a pothole in the road",
        "a photo of cracked asphalt",
        "a photo of a damaged road surface",
    ],
    "unsafe": [
        "a photo containing nudity",
        "a sexually explicit photo",
        "a photo of graphic violence",
        "a photo of blood and gore",
        "a photo of a dead body",
    ],
    "other": [
        "a selfie",
        "a photo of a person",
        "a screenshot of a phone screen",
        "a meme with text",
        "a logo or an icon",
        "a cartoon or a drawing",
        "a photo of an animal",
        "a photo of food",
        "a photo of the inside of a room",
        "a blank or very dark photo",
    ],
}

# flat list in a fixed order, matched to the model's output
LABELS: list[tuple[str, str]] = [
    (group, prompt) for group, prompts in PROMPTS.items() for prompt in prompts
]


class SafetyResult(BaseModel):
    """What the safety check thinks a photo shows."""

    scores: dict[str, float]  # road, unsafe, other; they add up to 1
    unsafe: bool
    is_road: bool


class SafetyChecker(Protocol):
    """Anything that checks if a photo is safe to show and shows a road."""

    def check(self, image: bytes) -> SafetyResult: ...


def assess(
    probabilities: list[float], unsafe_threshold: float, road_threshold: float
) -> SafetyResult:
    """Turn one probability per prompt into a decision.

    Probabilities are added up per group. The unsafe threshold is kept low
    on purpose: hiding a good photo is much better than showing a bad one.
    """
    if len(probabilities) != len(LABELS):
        raise ValueError(f"expected {len(LABELS)} probabilities")

    scores = dict.fromkeys(PROMPTS, 0.0)
    for (group, _), probability in zip(LABELS, probabilities, strict=True):
        scores[group] += probability

    return SafetyResult(
        scores={group: round(score, 4) for group, score in scores.items()},
        unsafe=scores["unsafe"] >= unsafe_threshold,
        is_road=scores["road"] >= road_threshold,
    )

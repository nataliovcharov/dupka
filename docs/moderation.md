# Moderation

Every photo is checked before it can show up on the public map.

## How a report gets its visibility

1. **Safety check (CLIP).** If the photo looks unsafe (nudity, violence, gore), the report is `hidden`. We don't look for damage.
2. **Road check (CLIP).** If the photo doesn't look like a road, the report goes to `needs_review`.
3. **Damage check (YOLO).** If no damage is found above `min_detection_confidence`, the report goes to `needs_review`.
4. Otherwise the report is `public`.

When unsure, we hide or review. A good photo waiting in review is fine, a bad photo on the map is not.

## Why CLIP

CLIP ([openai/clip-vit-base-patch32](https://huggingface.co/openai/clip-vit-base-patch32), MIT) scores how well a photo matches text descriptions without extra training. One small model covers both checks and runs on a CPU, and it's free to run on our own server.

Prompts are in `backend/app/services/safety.py`, grouped into `road`, `unsafe` and `other`. Probabilities are added up per group.

Known weakness: dedicated nudity classifiers are more accurate. If testing shows CLIP misses too much, add one behind the same `SafetyChecker` interface.

## Thresholds

Set in `backend/app/core/config.py`, can be changed with environment variables.

| Setting | Value | Meaning |
|---|---|---|
| `UNSAFE_THRESHOLD` | 0.2 | unsafe score at or above this hides the photo |
| `ROAD_THRESHOLD` | 0.5 | road score below this sends the photo to review |
| `MIN_DETECTION_CONFIDENCE` | 0.4 | detections below this don't count as damage |

## Tuning log

Try the check on photos:

~~~bash
cd backend
uv run --group worker python -m app.services.clip_safety path/to/photo.jpg
~~~

| Date | Photos | Result | Change |
|---|---|---|---|
| 2026-09-29 | 30 RDD2022 Czech road photos | 0 flagged unsafe, 0 missed as roads. Road scores around 0.98, unsafe below 0.01 | none |
| 2026-09-29 | GitHub logo (transparent PNG) | unsafe 0.36, flagged. Transparent areas turned black and no prompt fit a logo | transparent areas now go on white; added "a logo or an icon" and "a cartoon or a drawing". Unsafe dropped to 0.02 |
| 2026-09-29 | 1 non-road PNG | other 0.97, not a road | none |

Next: run on real Skopje photos, and on a public benchmark for unsafe content.

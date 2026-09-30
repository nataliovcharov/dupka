# Moderation

Every photo is checked before it can show up on the public map.

## How a report gets its visibility

0. **Blurring.** Faces and license plates are blurred first, and only the blurred photo is kept. If blurring fails, the report fails and never goes public. See [Blurring faces and plates](#blurring-faces-and-plates).
1. **Safety check (CLIP).** If the photo looks unsafe (nudity, violence, gore), the report is `hidden`. We don't look for damage.
2. **Road check (CLIP).** If the photo doesn't look like a road, the report goes to `needs_review`.
3. **Damage check (YOLO).** If no damage is found above `min_detection_confidence`, the report goes to `needs_review`.
4. Otherwise the report is `public`.

When unsure, we hide or review. A good photo waiting in review is fine, a bad photo on the map is not.

## Why CLIP

CLIP ([openai/clip-vit-base-patch32](https://huggingface.co/openai/clip-vit-base-patch32), MIT) scores how well a photo matches text descriptions without extra training. One small model covers both checks and runs on a CPU, and it's free to run on our own server.

Prompts are in `backend/app/services/safety.py`, grouped into `road`, `unsafe` and `other`. Probabilities are added up per group.

Known weakness: dedicated nudity classifiers are more accurate. If testing shows CLIP misses too much, add one behind the same `SafetyChecker` interface.

## Blurring faces and plates

Street photos often show people and number plates. Both are personal data, so they are blurred before a photo can be public, the same as Street View and Mapillary do.

| What | Model | License | Format |
|---|---|---|---|
| Faces | [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) (OpenCV) | MIT | ONNX, 230 KB, runs with `cv2.FaceDetectorYN` |
| Plates | YOLOv9-s 608 from [open-image-models](https://github.com/ankandrew/open-image-models) | MIT | ONNX, runs with onnxruntime |

Both run on our own server, photos are never sent to an outside service. Together they take about 0.1 to 0.2 s per photo on a laptop CPU.

Choices:
- **Blur, not reject.** Most street photos have someone in them somewhere, rejecting those would lose many good reports.
- **Keep only the blurred photo.** No unblurred copy to leak, and blurring doesn't affect finding road damage.
- **Low thresholds.** A blurred patch of wall is fine, a missed face is not.
- **Faces are looked for twice**, on the full photo and on a 640 px copy, because YuNet only finds faces up to about 300 px.
- **Strong blur.** Each box is grown by 20%, shrunk to a few pixels and scaled back up, so the original can't be recovered.
- We don't install the open-image-models package, it depends on `opencv-python-headless`, which clashes with the `opencv-python` Ultralytics installs. Its pre and post processing is copied in `backend/app/services/opencv_privacy.py`.
- We tried Meta's EgoBlur first (Apache 2.0, faces and plates). It needs about 15 files of Detectron2 code copied in, TorchScript (deprecated), and 2 x 400 MB models at about 3 s per photo, so we went with the two small models.

Get the models (kept out of Git):

~~~bash
cd backend
curl -L -o ../ml/models/face_detection_yunet_2023mar.onnx https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
curl -L -o ../ml/models/yolo-v9-s-608-license-plates-end2end.onnx https://github.com/ankandrew/open-image-models/releases/download/assets/yolo-v9-s-608-license-plates-end2end.onnx
~~~

## Thresholds

Set in `backend/app/core/config.py`, can be changed with environment variables.

| Setting | Value | Meaning |
|---|---|---|
| `UNSAFE_THRESHOLD` | 0.2 | unsafe score at or above this hides the photo |
| `ROAD_THRESHOLD` | 0.5 | road score below this sends the photo to review |
| `MIN_DETECTION_CONFIDENCE` | 0.28 | detections below this don't count as damage |
| `FACE_THRESHOLD` | 0.6 | faces at or above this are blurred (YuNet's own default is 0.9) |
| `PLATE_THRESHOLD` | 0.25 | plates at or above this are blurred (open-image-models default) |

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
| 2026-09-30 | 4 report photos (dashcam and street) | plates: 3 found, 0 missed, 0 false. No faces in these photos | none, faces still to test on photos with people |
| 2026-09-30 | e001 val split (2,783 images) | F1 peak 0.62 at 0.281 for all classes, pothole peak around 0.25 | `MIN_DETECTION_CONFIDENCE` 0.4 to 0.28 |

Next: run on real Skopje photos, and on a public benchmark for unsafe content.

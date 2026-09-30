# How it works

~~~
phone (React app)
      |
      v
FastAPI  ------------------------  photos on disk
      |
      v
Postgres + PostGIS  <----  worker: blur faces and plates
      ^                            -> CLIP road and safety check
      |                            -> YOLO damage detection
review page (/admin)               -> severity -> group into issues
~~~

1. The app resizes the photo and sends it with its location. The API strips all metadata (EXIF, GPS), saves the photo and creates a report waiting for the worker.
2. The worker blurs faces and number plates and keeps only the blurred photo.
3. CLIP checks if the photo is a road and if it's safe to show. My YOLO model finds the damage, and I turn the detections into a damage type and a severity.
4. Confident reports go on the map. Unsure ones go to the review page, where my decisions are saved next to what the model said, so they become training data.
5. Public reports less than 15 m apart are grouped into one issue. The map shows issues, with a count and a gallery of photos.

## Decisions

- **Postgres as the job queue** (`SELECT ... FOR UPDATE SKIP LOCKED`) instead of Redis or Celery. One less service to run, and the queue is transactional with the reports.
- **CLIP for the safety check** instead of a paid image moderation API. It's free, runs on my own server, and the photos never leave it. See [moderation.md](moderation.md).
- **Blur faces and plates instead of rejecting those photos.** Most street photos have someone in them. YuNet and a YOLOv9 plate model, both MIT and both local. I tried Meta's EgoBlur first, the reasons I dropped it are in [moderation.md](moderation.md).
- **Detection threshold from the F1 curve** on the validation split (0.28), not from a few photos.
- **Reviews in their own table**, keeping what the model said next to my decision, so every review is a labeled example.
- **Training data:** [decisions/0001-training-data.md](decisions/0001-training-data.md).
- **Hosting on free tiers:** [decisions/0002-hosting.md](decisions/0002-hosting.md).

## Stack

| | |
|---|---|
| Frontend | React 19, TypeScript, Vite, MapLibre GL with OpenFreeMap tiles, react-i18next |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, slowapi |
| Database | PostgreSQL 17 with PostGIS |
| ML | Ultralytics YOLO26s, CLIP ViT-B/32, YuNet, YOLOv9 plate detector |
| Tooling | uv, Ruff, pytest, ESLint, GitHub Actions, Docker Compose |

## Repo

~~~
backend/    FastAPI API, worker, migrations and tests
frontend/   React app
ml/         data conversion scripts, training notebook, experiment log
deploy/     production database image and Caddy config
docs/       decisions, moderation, deployment
~~~

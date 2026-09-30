# Dupka

Dupka (Macedonian for pothole) is a web app for reporting road damage in Skopje. You take a photo, check the spot on the map and send it. A model looks at the photo, finds the damage and how bad it is, and the report shows up on a public map.

I'm building it because road damage in Skopje gets reported in Facebook groups, in emails to the city, or not at all. Nobody can see what's already been reported, and the same pothole gets reported again and again.

## What it does

- Report from a phone: take a photo, the location comes from GPS or a pin you drag, send. Photos are resized in the browser, and the server strips all metadata (EXIF, GPS) before saving.
- Faces and number plates are blurred before anything else happens. Only the blurred photo is kept.
- A worker checks every photo. CLIP decides if it's a road and if it's safe to show, then my YOLO model finds the damage and I turn that into a type and a severity.
- When the model isn't sure, the report goes to a review page instead of the map. My decisions are saved next to what the model said, so they become training data.
- Reports less than 15 m apart are grouped into one issue. The map shows one dot with a count, and a gallery of its photos.
- The map has clustering and severity filters, and the app is in Macedonian and English.

## How it works

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

The job queue is a Postgres table read with `SELECT ... FOR UPDATE SKIP LOCKED`, so there's no Redis or Celery to run.

## The model

YOLO26s trained on RDD2022 (Czech, Japan, India, United States, China motorbike), 30 epochs on a free Colab T4. Results on the test split:

| Class | Precision | Recall | mAP50 |
|---|---|---|---|
| all | 0.656 | 0.591 | 0.637 |
| longitudinal crack | 0.662 | 0.649 | 0.691 |
| transverse crack | 0.620 | 0.580 | 0.615 |
| alligator crack | 0.713 | 0.666 | 0.729 |
| pothole | 0.631 | 0.469 | 0.513 |

Potholes are the weakest class and the one that matters most. RDD2022 is dashcam footage with small, far away damage, and people take close-ups with their phones, so the next experiment adds a pothole dataset and my own Skopje photos. The detection threshold (0.28) comes from the F1 curve on the validation split. Everything is in [ml/EXPERIMENTS.md](ml/EXPERIMENTS.md).

## Decisions

A few choices and why I made them:

- **Postgres as the job queue.** One less service to run and keep in sync, and the queue is transactional with the reports.
- **CLIP for the safety check** instead of a paid image moderation API. It's free, runs on my own server, and the photos never leave it. Tuning notes are in [docs/moderation.md](docs/moderation.md).
- **Blur faces and plates instead of rejecting those photos.** Most street photos have someone in them. I use YuNet (OpenCV) and a YOLOv9 plate model through onnxruntime, both MIT and both local. I tried Meta's EgoBlur first and dropped it, the reasons are in the moderation doc.
- **Training data:** [docs/decisions/0001-training-data.md](docs/decisions/0001-training-data.md).
- **Hosting on free tiers:** [docs/decisions/0002-hosting.md](docs/decisions/0002-hosting.md).

## Stack

| | |
|---|---|
| Frontend | React 19, TypeScript, Vite, MapLibre GL with OpenFreeMap tiles, react-i18next |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, slowapi |
| Database | PostgreSQL 17 with PostGIS |
| ML | Ultralytics YOLO26s, CLIP ViT-B/32, YuNet, YOLOv9 plate detector |
| Tooling | uv, Ruff, pytest, ESLint, GitHub Actions, Docker Compose |

## Running it locally

You need Docker, [uv](https://docs.astral.sh/uv/) and Node (version in `frontend/.nvmrc`).

~~~bash
cp .env.example .env
docker compose up -d
cd backend
uv sync --group worker
uv run alembic upgrade head
uv run fastapi dev app/main.py
~~~

In a second terminal:

~~~bash
cd frontend
npm ci
npm run dev
~~~

The worker needs the model files in `ml/models/`. The blur models can be downloaded with the commands in [docs/moderation.md](docs/moderation.md). The YOLO weights aren't in the repo, you can train them with the notebook in `ml/notebooks/`. Then, in a third terminal:

~~~bash
cd backend
uv run --group worker python -m app.worker
~~~

The app runs at http://localhost:5173. Tests: `cd backend && uv run --group worker pytest`.

## Repo

~~~
backend/    FastAPI API, worker, migrations and tests
frontend/   React app
ml/         data conversion scripts, training notebook, experiment log
deploy/     production database image and Caddy config
docs/       decisions, moderation, deployment
~~~

## Status

It works end to end on my machine. It isn't deployed yet: the production setup (`compose.prod.yaml`) is tested locally and the steps are in [docs/deployment.md](docs/deployment.md).

Next:
- a test set of my own Skopje photos
- e002, with more pothole data
- deploying it
- Albanian

## License

[GNU GPL-3.0](LICENSE)

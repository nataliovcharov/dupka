# Dupka

**AI-powered road damage reporting for North Macedonia. Launching in Skopje.**

Residents report road damage with a single photo. A computer vision model detects the damage and rates its severity, duplicate reports are merged automatically, and every report appears on a public map in Macedonian, Albanian and English.

> **Status:** in active development. See the [roadmap](#roadmap).

## Why
Road damage in Skopje is reported through scattered channels (email, social media, or not at all). Residents can't see what's already been reported, the same pothole is reported many times, and there is no public, data-backed view of where the worst roads are. See the [product brief](docs/product-brief.md).

## How it works
~~~
Browser (React) --> FastAPI --> Cloud Storage (photos)
                       |
                       v
            PostgreSQL + PostGIS  <--  Worker: YOLO detection -> severity -> privacy blur -> duplicate merge
                       |
                       v
             Public map (MapLibre + OpenStreetMap)
~~~

## Tech stack
| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, MapLibre, react-i18next |
| Backend | Python, FastAPI |
| Background jobs | Python worker, Postgres-backed job queue |
| Database | PostgreSQL + PostGIS |
| ML | PyTorch, YOLO (Ultralytics), trained on RDD2022 and fine-tuned on local photos |
| DevOps | Docker, Docker Compose, GitHub Actions, Google Cloud Run |

## Repository structure
~~~
backend/    FastAPI API and background worker
frontend/   React web app
ml/         Training, data preparation and evaluation
docs/       Product brief, architecture and decision records
~~~

## Getting started
Setup instructions will be added as each part is built.

## Roadmap
- [ ] Baseline road damage detection model and evaluation
- [ ] Backend API, database and background worker
- [ ] Web app: report flow and public map
- [ ] Duplicate merging, severity and privacy blurring
- [ ] Deployment and CI/CD
- [ ] Fine-tuning on Skopje photos and public launch

## License
[GNU AGPL-3.0](LICENSE)

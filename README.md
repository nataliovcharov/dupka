# Dupka

Dupka (Macedonian for pothole) is a web app for reporting road damage in Skopje. You take a photo, check the spot on the map and send it. A model finds the damage and how bad it is, and the report shows up on a public map.

Road damage in Skopje gets reported in Facebook groups, in emails to the city, or not at all. Nobody can see what's already been reported, and the same pothole gets reported again and again.

<p align="center">
  <video src="https://github.com/user-attachments/assets/273a10f8-ae59-4ba9-bc73-795e52255291" width="300" controls muted></video>
</p>
<p align="center"><sub>A report from my phone, start to finish.</sub></p>

## What it does

- Report from a phone in a few taps, in Macedonian or English.
- Faces and number plates are blurred before anyone sees the photo.
- My YOLO model finds the damage type and severity. Unsure reports go to a review page instead of the map.
- Reports of the same spot are grouped, so the map shows one dot with all its photos.

## The model

YOLO26s trained on RDD2022, a public road damage dataset. On the test split it gets 0.64 mAP50 overall and 0.51 on potholes.

Potholes are the weakest class, and I know why: RDD2022 is dashcam footage, so the potholes in it are small and far away, while people using Dupka take close-ups with their phones. Even so, it found the pothole in most of the real phone photos I've tried. The next step is training on more close-up pothole photos, including my own from Skopje. Full results are in [ml/EXPERIMENTS.md](ml/EXPERIMENTS.md).

## Built with

React, TypeScript and MapLibre on the frontend. FastAPI, PostgreSQL with PostGIS, and a Python worker on the backend. PyTorch with YOLO and CLIP for the models. Docker, GitHub Actions, uv and Ruff for the rest.

## More

- [How it works and why I built it this way](docs/architecture.md)
- [Running it locally](docs/development.md)
- [Moderation and blurring](docs/moderation.md)
- [Deployment](docs/deployment.md)

## Status

Works end to end on my machine. The production setup is ready and tested locally, hosting is next.

## License

[GNU GPL-3.0](LICENSE)

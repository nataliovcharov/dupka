# Running it locally

You need Docker, [uv](https://docs.astral.sh/uv/) and Node (version in `frontend/.nvmrc`).

## Database and API

~~~bash
cp .env.example .env
docker compose up -d
cd backend
uv sync --group worker
uv run alembic upgrade head
uv run fastapi dev app/main.py
~~~

## Frontend

In a second terminal:

~~~bash
cd frontend
npm ci
npm run dev
~~~

The app runs at http://localhost:5173. The Vite dev server sends `/api` to the API.

## Worker

The worker needs the model files in `ml/models/`. The blur models can be downloaded with the commands in [moderation.md](moderation.md). The YOLO weights aren't in the repo, they can be trained with the notebook in `ml/notebooks/`.

In a third terminal:

~~~bash
cd backend
uv run --group worker python -m app.worker
~~~

## Tests and checks

~~~bash
cd backend
uv run --group worker pytest
uv run ruff check .
uv run ruff format --check .
~~~

~~~bash
cd frontend
npm run lint
npm run build
~~~

## Admin page

Set `ADMIN_TOKEN` in `.env` (generate one with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`), restart the API and open http://localhost:5173/admin.

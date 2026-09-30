# one file for the api and the worker, pick with --target api or --target worker
FROM python:3.13-slim-bookworm AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app
# don't run as root. the folders volumes mount on are made here, so the
# volumes start out owned by this user
RUN useradd --create-home --uid 1000 dupka \
    && mkdir -p /data/photos /cache/huggingface \
    && chown -R dupka /data /cache


FROM base AS api
COPY pyproject.toml uv.lock ./
# dependencies first, so code changes don't reinstall them
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
USER dupka
EXPOSE 8000
# only caddy can reach the api, so trusting any proxy's headers is safe here
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]


FROM base AS worker
# opencv needs these system libraries
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --group worker --no-install-project
COPY app ./app
USER dupka
ENV HF_HOME=/cache/huggingface
CMD ["python", "-m", "app.worker"]

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.db.session import DbSession

app = FastAPI(title="Dupka API", version="0.1.0")


@app.get("/health")
def health():
    """Liveness check used by Docker and Cloud Run."""
    return {"status": "ok"}


@app.get("/ready")
def ready(db: DbSession):
    """Readiness check: the API can reach the database and PostGIS."""
    try:
        postgis = db.execute(text("SELECT PostGIS_Version()")).scalar_one()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ready", "postgis": postgis}

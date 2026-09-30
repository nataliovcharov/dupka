from fastapi import FastAPI, HTTPException
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api import admin, issues, reports
from app.core.rate_limit import limiter, rate_limit_exceeded
from app.db.session import DbSession

app = FastAPI(title="Dupka API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded)
app.include_router(reports.router)
app.include_router(issues.router)
app.include_router(admin.router)


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

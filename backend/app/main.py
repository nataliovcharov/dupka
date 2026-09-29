from fastapi import FastAPI

app = FastAPI(title="Dupka API", version="0.1.0")


@app.get("/health")
def health():
    """Liveness check used by Docker and Cloud Run."""
    return {"status": "ok"}

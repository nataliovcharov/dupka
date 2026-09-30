from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str
    storage_dir: Path = Path("storage")  # local photo storage in development
    max_upload_mb: int = 10
    # detections below this are ignored when deciding if a photo shows road damage
    min_detection_confidence: float = 0.4
    # trained weights, kept out of Git (see ml/EXPERIMENTS.md)
    model_path: Path = Path("../ml/models/e001-best.pt")
    # safety check, tuned on sample photos (see docs/moderation.md)
    clip_model: str = "openai/clip-vit-base-patch32"
    unsafe_threshold: float = 0.2
    road_threshold: float = 0.5


settings = Settings()

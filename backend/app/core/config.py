from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str
    storage_dir: Path = Path("storage")  # local photo storage in development
    max_upload_mb: int = 10
    # detections below this are ignored when deciding if a photo shows road damage
    # f1 peak on val for e001 (0.62 at 0.281), see ml/EXPERIMENTS.md
    min_detection_confidence: float = 0.28
    # trained weights, kept out of Git (see ml/EXPERIMENTS.md)
    model_path: Path = Path("../ml/models/e001-best.pt")
    # safety check, tuned on sample photos (see docs/moderation.md)
    clip_model: str = "openai/clip-vit-base-patch32"
    unsafe_threshold: float = 0.2
    road_threshold: float = 0.5
    # public reports this close (meters) are grouped into one issue
    duplicate_radius_m: float = 15
    # admin endpoints are off when this is empty
    admin_token: SecretStr | None = None


settings = Settings()

from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables or a .env file."""

    # empty values count as unset, docker compose passes unset variables as ""
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), extra="ignore", env_ignore_empty=True
    )

    database_url: str
    storage_dir: Path = Path("storage")  # local photo storage in development
    max_upload_mb: int = 10
    # per IP address, in the format slowapi understands
    upload_rate_limit: str = "10/hour;30/day"
    # photos of hidden reports are deleted after this (see the privacy page)
    hidden_photo_days: int = 30
    # detections below this are ignored when deciding if a photo shows road damage
    # f1 peak on val for e001 (0.62 at 0.281), see ml/EXPERIMENTS.md
    min_detection_confidence: float = 0.28
    # trained weights, kept out of Git (see ml/EXPERIMENTS.md)
    model_path: Path = Path("../ml/models/e001-best.pt")
    # safety check, tuned on sample photos (see docs/moderation.md)
    clip_model: str = "openai/clip-vit-base-patch32"
    unsafe_threshold: float = 0.2
    road_threshold: float = 0.5
    # face and plate blurring, low thresholds because a missed face is worse
    # than a blurred patch of wall (see docs/moderation.md)
    face_model_path: Path = Path("../ml/models/face_detection_yunet_2023mar.onnx")
    plate_model_path: Path = Path(
        "../ml/models/yolo-v9-s-608-license-plates-end2end.onnx"
    )
    face_threshold: float = 0.6
    plate_threshold: float = 0.25
    # public reports this close (meters) are grouped into one issue
    duplicate_radius_m: float = 15
    # frontend addresses allowed to call the api from a browser, e.g.
    # ["https://dupka.pages.dev"]. empty in development, the vite proxy is used
    cors_origins: list[str] = []
    # admin endpoints are off when this is empty
    admin_token: SecretStr | None = None


settings = Settings()

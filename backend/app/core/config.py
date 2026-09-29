from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings, read from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str
    storage_dir: Path = Path("storage")  # local photo storage in development
    max_upload_mb: int = 10


settings = Settings()

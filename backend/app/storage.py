from pathlib import Path
from typing import Protocol

from app.core.config import settings


class Storage(Protocol):
    """Anything that can save a file under a key."""

    def save(self, key: str, data: bytes) -> None: ...


class LocalStorage:
    """Saves files on disk. Used in development and tests.

    Production will use cloud storage through the same interface.
    """

    def __init__(self, root: Path):
        self.root = root

    def save(self, key: str, data: bytes) -> None:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def get_storage() -> Storage:
    return LocalStorage(settings.storage_dir)

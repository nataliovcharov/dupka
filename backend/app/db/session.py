from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# pool_pre_ping drops dead connections, e.g. after the database restarts
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    """Give each request its own session and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# endpoints use this type to get a session: def endpoint(db: DbSession)
DbSession = Annotated[Session, Depends(get_db)]

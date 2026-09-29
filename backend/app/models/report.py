import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geography, WKBElement
from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReportStatus(enum.StrEnum):
    PENDING = "pending"  # uploaded, waiting for the worker
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(
            ReportStatus,
            native_enum=False,
            length=20,
            values_callable=lambda statuses: [s.value for s in statuses],
        ),
        default=ReportStatus.PENDING,
        index=True,
    )
    # geography, so distances come out in meters
    location: Mapped[WKBElement] = mapped_column(
        Geography(geometry_type="POINT", srid=4326)
    )
    photo_key: Mapped[str] = mapped_column(String(255))
    detections: Mapped[list | None] = mapped_column(JSONB)
    damage_type: Mapped[str | None] = mapped_column(String(10))
    severity: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

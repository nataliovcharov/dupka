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


class ReportVisibility(enum.StrEnum):
    PENDING = "pending"  # not checked yet
    PUBLIC = "public"  # shown on the map
    NEEDS_REVIEW = "needs_review"  # no damage found, a person should look at it
    HIDDEN = "hidden"  # never shown


def enum_column(enum_class: type[enum.StrEnum]) -> Enum:
    """Store enums as their string values, e.g. "needs_review"."""
    return Enum(
        enum_class,
        native_enum=False,
        length=20,
        values_callable=lambda members: [m.value for m in members],
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[ReportStatus] = mapped_column(
        enum_column(ReportStatus), default=ReportStatus.PENDING, index=True
    )
    # status says if the worker ran, visibility says who can see the report
    visibility: Mapped[ReportVisibility] = mapped_column(
        enum_column(ReportVisibility),
        default=ReportVisibility.PENDING,
        server_default=ReportVisibility.PENDING.value,
        index=True,
    )
    # geography, so distances come out in meters
    location: Mapped[WKBElement] = mapped_column(
        Geography(geometry_type="POINT", srid=4326)
    )
    photo_key: Mapped[str] = mapped_column(String(255))
    detections: Mapped[list | None] = mapped_column(JSONB)
    # safety check scores, kept for reviewing reports and tuning thresholds
    safety: Mapped[dict | None] = mapped_column(JSONB)
    damage_type: Mapped[str | None] = mapped_column(String(10))
    severity: Mapped[str | None] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

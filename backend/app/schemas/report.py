import uuid
from datetime import datetime

from geoalchemy2.shape import to_shape
from pydantic import BaseModel

from app.models import Report, ReportStatus


class ReportOut(BaseModel):
    """A report as returned by the API."""

    id: uuid.UUID
    status: ReportStatus
    latitude: float
    longitude: float
    damage_type: str | None
    severity: str | None
    created_at: datetime

    @classmethod
    def from_model(cls, report: Report) -> "ReportOut":
        point = to_shape(
            report.location
        )  # PostGIS point -> x (longitude), y (latitude)
        return cls(
            id=report.id,
            status=report.status,
            latitude=point.y,
            longitude=point.x,
            damage_type=report.damage_type,
            severity=report.severity,
            created_at=report.created_at,
        )

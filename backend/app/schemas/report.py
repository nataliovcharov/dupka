import uuid
from datetime import datetime
from typing import Literal

from geoalchemy2.shape import to_shape
from pydantic import BaseModel

from app.models import Report, ReportStatus, ReportVisibility


class ReportOut(BaseModel):
    """A report as returned by the API."""

    id: uuid.UUID
    status: ReportStatus
    visibility: ReportVisibility
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
            visibility=report.visibility,
            latitude=point.y,
            longitude=point.x,
            damage_type=report.damage_type,
            severity=report.severity,
            created_at=report.created_at,
        )


# GeoJSON (RFC 7946), the format the map reads directly


class PointGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]  # longitude, latitude


class ReportProperties(BaseModel):
    id: uuid.UUID
    status: ReportStatus
    damage_type: str | None
    severity: str | None
    created_at: datetime


class ReportFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry
    properties: ReportProperties

    @classmethod
    def from_model(cls, report: Report) -> "ReportFeature":
        point = to_shape(report.location)
        return cls(
            geometry=PointGeometry(coordinates=(point.x, point.y)),
            properties=ReportProperties(
                id=report.id,
                status=report.status,
                damage_type=report.damage_type,
                severity=report.severity,
                created_at=report.created_at,
            ),
        )


class ReportCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[ReportFeature]

import uuid
from datetime import datetime
from typing import Literal, Self

from geoalchemy2.shape import to_shape
from pydantic import BaseModel

from app.models import Issue, Report
from app.schemas.report import PointGeometry


class IssueProperties(BaseModel):
    id: uuid.UUID
    damage_type: str | None
    severity: str | None
    report_count: int
    last_reported_at: datetime


class IssueFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: PointGeometry
    properties: IssueProperties

    @classmethod
    def from_model(cls, issue: Issue) -> Self:
        point = to_shape(issue.location)
        return cls(
            geometry=PointGeometry(coordinates=(point.x, point.y)),
            properties=IssueProperties(
                id=issue.id,
                damage_type=issue.damage_type,
                severity=issue.severity,
                report_count=issue.report_count,
                last_reported_at=issue.last_reported_at,
            ),
        )


class IssueCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[IssueFeature]


class IssueReport(BaseModel):
    """One public report of an issue, its photo is at /reports/{id}/photo."""

    id: uuid.UUID
    damage_type: str | None
    severity: str | None
    created_at: datetime


class IssueOut(BaseModel):
    """An issue with its public reports, newest first."""

    id: uuid.UUID
    latitude: float
    longitude: float
    damage_type: str | None
    severity: str | None
    report_count: int
    created_at: datetime
    last_reported_at: datetime
    reports: list[IssueReport]

    @classmethod
    def from_model(cls, issue: Issue, reports: list[Report]) -> Self:
        point = to_shape(issue.location)
        return cls(
            id=issue.id,
            latitude=point.y,
            longitude=point.x,
            damage_type=issue.damage_type,
            severity=issue.severity,
            report_count=issue.report_count,
            created_at=issue.created_at,
            last_reported_at=issue.last_reported_at,
            reports=[
                IssueReport(
                    id=r.id,
                    damage_type=r.damage_type,
                    severity=r.severity,
                    created_at=r.created_at,
                )
                for r in reports
            ],
        )

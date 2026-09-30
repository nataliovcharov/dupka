from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator

from app.models import Report, Review, ReviewDecision
from app.schemas.report import ReportOut
from app.services.detector import Detection

DamageType = Literal["D00", "D10", "D20", "D40"]
Severity = Literal["low", "medium", "high"]


class ReviewIn(BaseModel):
    """A reviewer's decision. Approving needs the damage type and severity."""

    decision: ReviewDecision
    damage_type: DamageType | None = None
    severity: Severity | None = None

    @model_validator(mode="after")
    def check_approve_has_labels(self) -> Self:
        approve = self.decision == ReviewDecision.APPROVE
        if approve and (self.damage_type is None or self.severity is None):
            raise ValueError("approving needs damage_type and severity")
        return self


class ReviewOut(BaseModel):
    # allow field names that start with "model_"
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    decision: ReviewDecision
    damage_type: str | None
    severity: str | None
    model_damage_type: str | None
    model_severity: str | None
    reviewer: str
    created_at: datetime


class AdminReportOut(ReportOut):
    """A report with everything a reviewer needs."""

    detections: list[Detection] | None
    safety: dict | None
    privacy: dict | None
    last_review: ReviewOut | None

    @classmethod
    def from_report(cls, report: Report, last_review: Review | None = None) -> Self:
        return cls(
            **ReportOut.from_model(report).model_dump(),
            detections=report.detections,
            safety=report.safety,
            privacy=report.privacy,
            last_review=(
                ReviewOut.model_validate(last_review) if last_review else None
            ),
        )

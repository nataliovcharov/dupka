import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.report import enum_column


class ReviewDecision(enum.StrEnum):
    APPROVE = "approve"  # report goes on the map
    REJECT = "reject"  # report is hidden


class Review(Base):
    """A person's decision on a report.

    The model's answer is kept next to it, so reviews can be used as training labels.
    """

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )
    decision: Mapped[ReviewDecision] = mapped_column(enum_column(ReviewDecision))
    # the reviewer's answer, empty when rejected
    damage_type: Mapped[str | None] = mapped_column(String(10))
    severity: Mapped[str | None] = mapped_column(String(10))
    # what the model said before the review
    model_damage_type: Mapped[str | None] = mapped_column(String(10))
    model_severity: Mapped[str | None] = mapped_column(String(10))
    reviewer: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

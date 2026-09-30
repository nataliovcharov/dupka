from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Report, ReportVisibility
from app.storage import Storage


def delete_old_hidden_photos(
    db: Session, storage: Storage, now: datetime | None = None
) -> int:
    """Delete photos of reports hidden for longer than the retention period.

    The report row and its review stay, only the photo goes. Returns how many
    photos were deleted.
    """
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=settings.hidden_photo_days)
    reports = db.scalars(
        select(Report).where(
            Report.visibility == ReportVisibility.HIDDEN,
            # updated when the report was hidden, by the worker or a review
            Report.updated_at < cutoff,
            Report.photo_deleted_at.is_(None),
        )
    ).all()
    for report in reports:
        storage.delete(report.photo_key)
        report.photo_deleted_at = now
    db.commit()
    return len(reports)

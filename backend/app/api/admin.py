import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_admin
from app.db.session import DbSession
from app.models import Report, ReportStatus, ReportVisibility, Review, ReviewDecision
from app.schemas.admin import AdminReportOut, ReviewIn
from app.storage import Storage, get_storage

# every route here needs the admin token
router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)

REVIEWER = "admin"  # one admin for now


def get_report_or_404(db: Session, report_id: uuid.UUID) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "report not found")
    return report


def last_reviews(db: Session, report_ids: list[uuid.UUID]) -> dict[uuid.UUID, Review]:
    """The newest review of each report, in one query."""
    query = (
        select(Review)
        .where(Review.report_id.in_(report_ids))
        .order_by(Review.report_id, Review.created_at.desc())
        .distinct(Review.report_id)  # postgres DISTINCT ON
    )
    return {review.report_id: review for review in db.scalars(query)}


@router.get("/reports", response_model=list[AdminReportOut])
def list_reports(
    db: DbSession,
    visibility: ReportVisibility | None = None,
    report_status: Annotated[ReportStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """List reports for review, oldest first."""
    query = select(Report).order_by(Report.created_at).limit(limit)
    if visibility:
        query = query.where(Report.visibility == visibility)
    if report_status:
        query = query.where(Report.status == report_status)
    reports = db.scalars(query).all()
    reviews = last_reviews(db, [r.id for r in reports])
    return [AdminReportOut.from_report(r, reviews.get(r.id)) for r in reports]


@router.get(
    "/reports/{report_id}/photo",
    response_class=Response,
    responses={200: {"content": {"image/jpeg": {}}}},
)
def get_photo(
    report_id: uuid.UUID,
    db: DbSession,
    storage: Annotated[Storage, Depends(get_storage)],
):
    """The report's photo. Admins only, the report may not be public."""
    report = get_report_or_404(db, report_id)
    try:
        data = storage.load(report.photo_key)
    except FileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "photo not found") from exc
    # browsers and proxies shouldn't keep a copy
    return Response(
        data, media_type="image/jpeg", headers={"Cache-Control": "private, no-store"}
    )


@router.post("/reports/{report_id}/review", response_model=AdminReportOut)
def review_report(report_id: uuid.UUID, review_in: ReviewIn, db: DbSession):
    """Approve a report (goes on the map) or reject it (hidden)."""
    report = get_report_or_404(db, report_id)
    if report.status not in (ReportStatus.DONE, ReportStatus.FAILED):
        raise HTTPException(status.HTTP_409_CONFLICT, "report is still being processed")

    # approving overwrites the report's type and severity,
    # so the model's answer comes from the first review when there is one
    previous = last_reviews(db, [report.id]).get(report.id)
    if previous:
        model_type, model_severity = previous.model_damage_type, previous.model_severity
    else:
        model_type, model_severity = report.damage_type, report.severity

    approve = review_in.decision == ReviewDecision.APPROVE
    review = Review(
        report_id=report.id,
        decision=review_in.decision,
        damage_type=review_in.damage_type if approve else None,
        severity=review_in.severity if approve else None,
        model_damage_type=model_type,
        model_severity=model_severity,
        reviewer=REVIEWER,
    )
    if approve:
        report.visibility = ReportVisibility.PUBLIC
        report.damage_type = review_in.damage_type
        report.severity = review_in.severity
    else:
        report.visibility = ReportVisibility.HIDDEN
    db.add(review)
    db.commit()
    db.refresh(review)
    return AdminReportOut.from_report(report, review)

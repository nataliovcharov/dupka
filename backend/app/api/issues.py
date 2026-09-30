import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from geoalchemy2 import Geography
from sqlalchemy import cast, func, select

from app.api.reports import parse_bbox
from app.db.session import DbSession
from app.models import Issue, Report, ReportVisibility
from app.schemas.issue import IssueCollection, IssueFeature, IssueOut

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("", response_model=IssueCollection)
def list_issues(
    db: DbSession,
    bbox: Annotated[
        str | None,
        Query(description="Visible map area: min_lon,min_lat,max_lon,max_lat"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
):
    """List issues for the map as GeoJSON, most recently reported first."""
    query = select(Issue).order_by(Issue.last_reported_at.desc()).limit(limit)
    if bbox:
        min_lon, min_lat, max_lon, max_lat = parse_bbox(bbox)
        area = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        query = query.where(func.ST_Intersects(Issue.location, cast(area, Geography)))

    issues = db.scalars(query).all()
    return IssueCollection(features=[IssueFeature.from_model(i) for i in issues])


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: uuid.UUID, db: DbSession):
    """One issue with its public reports, newest first."""
    issue = db.get(Issue, issue_id)
    if issue is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "issue not found")
    reports = db.scalars(
        select(Report)
        .where(
            Report.issue_id == issue.id,
            Report.visibility == ReportVisibility.PUBLIC,
        )
        .order_by(Report.created_at.desc())
    ).all()
    return IssueOut.from_model(issue, list(reports))

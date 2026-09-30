from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Issue, Report, ReportVisibility
from app.services.severity import PRIORITY

SEVERITY_ORDER = ["high", "medium", "low"]  # worst first
# any fixed number, it just has to be the same everywhere reports get grouped
ISSUE_LOCK_ID = 4_815_162_342


def attach_to_issue(db: Session, report: Report) -> Issue:
    """Put a public report in the nearest issue within the radius, or start one."""
    if report.issue_id is not None:
        # already grouped, e.g. approved again with a new severity
        db.flush()
        issue = db.get_one(Issue, report.issue_id)
        refresh_issue(db, issue)
        return issue

    # one at a time, so two reports of the same pothole can't both start an issue.
    # released on commit
    db.execute(select(func.pg_advisory_xact_lock(ISSUE_LOCK_ID)))

    point = select(Report.location).where(Report.id == report.id).scalar_subquery()
    issue = db.scalars(
        select(Issue)
        .where(func.ST_DWithin(Issue.location, point, settings.duplicate_radius_m))
        .order_by(Issue.location.op("<->")(point))  # nearest first
        .limit(1)
    ).first()
    if issue is None:
        issue = Issue(location=report.location)
        db.add(issue)
        db.flush()

    report.issue_id = issue.id
    db.flush()
    refresh_issue(db, issue)
    return issue


def detach_from_issue(db: Session, report: Report) -> None:
    """Take a report out of its issue, e.g. when it gets hidden."""
    if report.issue_id is None:
        return
    issue = db.get_one(Issue, report.issue_id)
    report.issue_id = None
    db.flush()
    refresh_issue(db, issue)


def refresh_issue(db: Session, issue: Issue) -> None:
    """Recount the issue and take the worst type and severity of its reports.

    An issue with no public reports left is deleted.
    """
    reports = db.scalars(
        select(Report).where(
            Report.issue_id == issue.id, Report.visibility == ReportVisibility.PUBLIC
        )
    ).all()
    if not reports:
        db.delete(issue)
        db.flush()
        return

    types = [r.damage_type for r in reports if r.damage_type in PRIORITY]
    severities = [r.severity for r in reports if r.severity in SEVERITY_ORDER]
    issue.damage_type = min(types, key=PRIORITY.index) if types else None
    issue.severity = min(severities, key=SEVERITY_ORDER.index) if severities else None
    issue.report_count = len(reports)
    issue.last_reported_at = max(r.created_at for r in reports)
    db.flush()

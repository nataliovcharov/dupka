import pytest
from geoalchemy2.shape import to_shape
from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import Issue, Report, ReportStatus, ReportVisibility
from app.services.issues import attach_to_issue, detach_from_issue

# one degree of latitude is about 111 km, so these are ~5 m and ~30 m north of BASE
BASE = (21.4254, 41.9965)
NEAR = (21.4254, 41.99655)
FAR = (21.4254, 41.99677)


def add_public_report(db, point, damage_type="D40", severity="medium") -> Report:
    lon, lat = point
    report = Report(
        photo_key="reports/test.jpg",
        location=f"SRID=4326;POINT({lon} {lat})",
        status=ReportStatus.DONE,
        visibility=ReportVisibility.PUBLIC,
        damage_type=damage_type,
        severity=severity,
    )
    db.add(report)
    db.flush()
    return report


def count_issues(db) -> int:
    return db.scalar(select(func.count()).select_from(Issue))


def test_nearby_reports_share_an_issue():
    with SessionLocal() as db:
        first = attach_to_issue(db, add_public_report(db, BASE))
        second = attach_to_issue(db, add_public_report(db, NEAR))
        db.commit()

        assert first.id == second.id
        assert second.report_count == 2
        assert count_issues(db) == 1


def test_far_reports_get_separate_issues():
    with SessionLocal() as db:
        first = attach_to_issue(db, add_public_report(db, BASE))
        second = attach_to_issue(db, add_public_report(db, FAR))
        db.commit()

        assert first.id != second.id
        assert count_issues(db) == 2


def test_issue_takes_the_worst_type_and_severity():
    with SessionLocal() as db:
        attach_to_issue(db, add_public_report(db, BASE, "D00", "low"))
        attach_to_issue(db, add_public_report(db, NEAR, "D40", "medium"))
        issue = attach_to_issue(db, add_public_report(db, NEAR, "D20", "high"))
        db.commit()

        assert issue.damage_type == "D40"
        assert issue.severity == "high"
        assert issue.report_count == 3


def test_issue_keeps_the_first_location():
    with SessionLocal() as db:
        attach_to_issue(db, add_public_report(db, BASE))
        issue = attach_to_issue(db, add_public_report(db, NEAR))
        db.commit()
        db.refresh(issue)

        point = to_shape(issue.location)
        assert (point.x, point.y) == pytest.approx(BASE)


def test_attaching_twice_does_not_count_twice():
    with SessionLocal() as db:
        report = add_public_report(db, BASE)
        attach_to_issue(db, report)
        issue = attach_to_issue(db, report)
        db.commit()

        assert issue.report_count == 1


def test_detaching_recounts_and_removes_empty_issues():
    with SessionLocal() as db:
        worst = add_public_report(db, BASE, severity="high")
        other = add_public_report(db, NEAR, severity="low")
        attach_to_issue(db, worst)
        issue = attach_to_issue(db, other)
        issue_id = issue.id

        # hidden reports leave their issue
        worst.visibility = ReportVisibility.HIDDEN
        detach_from_issue(db, worst)
        assert issue.report_count == 1
        assert issue.severity == "low"

        other.visibility = ReportVisibility.HIDDEN
        detach_from_issue(db, other)
        db.commit()

        assert db.get(Issue, issue_id) is None

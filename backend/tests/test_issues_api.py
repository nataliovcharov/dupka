import uuid

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models import Report, ReportStatus, ReportVisibility
from app.services.issues import attach_to_issue

client = TestClient(app)

# bbox strings: min_lon,min_lat,max_lon,max_lat
CENTRAL_SKOPJE = "21.38,41.97,21.47,42.02"
BITOLA = "21.30,41.00,21.37,41.05"


def add_report(visibility=ReportVisibility.PUBLIC, severity="medium", lat=41.9965):
    """Save a checked report, grouped into an issue when it's public."""
    with SessionLocal() as db:
        report = Report(
            photo_key="reports/test.jpg",
            location=f"SRID=4326;POINT(21.4254 {lat})",
            status=ReportStatus.DONE,
            visibility=visibility,
            damage_type="D40",
            severity=severity,
        )
        db.add(report)
        db.flush()
        issue_id = None
        if visibility == ReportVisibility.PUBLIC:
            issue_id = attach_to_issue(db, report).id
        db.commit()
        return report.id, issue_id


def test_list_issues_inside_bbox_with_count():
    _, issue_id = add_report(severity="low")
    add_report(severity="high", lat=41.99655)  # ~5 m away, same issue

    response = client.get("/issues", params={"bbox": CENTRAL_SKOPJE})
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 1
    feature = body["features"][0]
    assert feature["properties"]["id"] == str(issue_id)
    assert feature["properties"]["report_count"] == 2
    assert feature["properties"]["severity"] == "high"
    assert feature["geometry"]["coordinates"][1] == 41.9965  # first report's spot


def test_list_issues_excludes_issues_outside_bbox():
    add_report()

    response = client.get("/issues", params={"bbox": BITOLA})
    assert response.json()["features"] == []


def test_list_issues_rejects_invalid_bbox():
    response = client.get("/issues", params={"bbox": "not,a,valid,bbox"})
    assert response.status_code == 422


def test_issue_details_list_public_reports_newest_first():
    first, issue_id = add_report()
    second, _ = add_report(lat=41.99655)
    add_report(visibility=ReportVisibility.NEEDS_REVIEW, lat=41.99655)

    response = client.get(f"/issues/{issue_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["report_count"] == 2
    assert [r["id"] for r in body["reports"]] == [str(second), str(first)]


def test_unknown_issue_returns_404():
    assert client.get(f"/issues/{uuid.uuid4()}").status_code == 404

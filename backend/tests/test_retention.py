from datetime import UTC, datetime, timedelta

from app.db.session import SessionLocal
from app.models import Report, ReportStatus, ReportVisibility
from app.services.retention import delete_old_hidden_photos
from app.storage import LocalStorage

NOW = datetime(2026, 10, 1, tzinfo=UTC)


def add_report(storage, visibility, days_ago) -> Report:
    key = f"reports/{visibility}-{days_ago}.jpg"
    storage.save(key, b"photo")
    with SessionLocal() as db:
        report = Report(
            photo_key=key,
            location="SRID=4326;POINT(21.4254 41.9965)",
            status=ReportStatus.DONE,
            visibility=visibility,
            updated_at=NOW - timedelta(days=days_ago),
        )
        db.add(report)
        db.commit()
        return report.id


def test_old_hidden_photos_are_deleted(tmp_path):
    storage = LocalStorage(tmp_path)
    old_hidden = add_report(storage, ReportVisibility.HIDDEN, days_ago=31)
    new_hidden = add_report(storage, ReportVisibility.HIDDEN, days_ago=5)
    old_public = add_report(storage, ReportVisibility.PUBLIC, days_ago=100)

    with SessionLocal() as db:
        assert delete_old_hidden_photos(db, storage, now=NOW) == 1

        assert db.get(Report, old_hidden).photo_deleted_at == NOW
        assert not (tmp_path / "reports" / "hidden-31.jpg").exists()
        # the rest stays
        assert db.get(Report, new_hidden).photo_deleted_at is None
        assert db.get(Report, old_public).photo_deleted_at is None
        assert (tmp_path / "reports" / "hidden-5.jpg").exists()
        assert (tmp_path / "reports" / "public-100.jpg").exists()


def test_deleting_twice_does_nothing_more(tmp_path):
    storage = LocalStorage(tmp_path)
    add_report(storage, ReportVisibility.HIDDEN, days_ago=31)

    with SessionLocal() as db:
        assert delete_old_hidden_photos(db, storage, now=NOW) == 1
        assert delete_old_hidden_photos(db, storage, now=NOW) == 0

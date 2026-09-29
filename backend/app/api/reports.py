import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.config import settings
from app.db.session import DbSession
from app.models import Report
from app.schemas.report import ReportOut
from app.services.images import InvalidImageError, clean_photo
from app.storage import Storage, get_storage

router = APIRouter(prefix="/reports", tags=["reports"])

# rough bounding box around North Macedonia
MIN_LAT, MAX_LAT = 40.85, 42.37
MIN_LON, MAX_LON = 20.45, 23.04
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    db: DbSession,
    storage: Annotated[Storage, Depends(get_storage)],
    photo: Annotated[UploadFile, File(description="Photo of the road damage")],
    latitude: Annotated[float, Form(ge=MIN_LAT, le=MAX_LAT)],
    longitude: Annotated[float, Form(ge=MIN_LON, le=MAX_LON)],
):
    """Create a report from a photo and its location. The worker processes it later."""
    if photo.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "photo must be JPEG, PNG or WebP"
        )

    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = photo.file.read(
        max_bytes + 1
    )  # read one extra byte to detect oversized files
    if len(data) > max_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"photo is larger than {settings.max_upload_mb} MB",
        )

    try:
        cleaned = clean_photo(data)
    except InvalidImageError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    report_id = uuid.uuid4()
    photo_key = f"reports/{report_id}.jpg"
    storage.save(photo_key, cleaned)

    report = Report(
        id=report_id,
        photo_key=photo_key,
        location=f"SRID=4326;POINT({longitude} {latitude})",
    )
    db.add(report)
    db.commit()
    db.refresh(report)  # loads created_at, which the database sets
    return ReportOut.from_model(report)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: uuid.UUID, db: DbSession):
    """Get one report by its id."""
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "report not found")
    return ReportOut.from_model(report)

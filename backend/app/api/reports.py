import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import DbSession
from app.models import Report, ReportVisibility
from app.schemas.report import ReportCollection, ReportFeature, ReportOut
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


def get_public_report(db: Session, report_id: uuid.UUID) -> Report:
    """The report if it's public, otherwise 404."""
    report = db.get(Report, report_id)
    # same 404 for non-public reports, so hidden ones can't be found by id
    if report is None or report.visibility != ReportVisibility.PUBLIC:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "report not found")
    return report


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: uuid.UUID, db: DbSession):
    """Get one public report by its id."""
    return ReportOut.from_model(get_public_report(db, report_id))


@router.get(
    "/{report_id}/photo",
    response_class=Response,
    responses={200: {"content": {"image/jpeg": {}}}},
)
def get_report_photo(
    report_id: uuid.UUID,
    db: DbSession,
    storage: Annotated[Storage, Depends(get_storage)],
):
    """The photo of a public report, for the map."""
    report = get_public_report(db, report_id)
    try:
        data = storage.load(report.photo_key)
    except FileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "photo not found") from exc
    # short cache, a report can still be hidden later
    return Response(
        data, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=300"}
    )


def parse_bbox(bbox: str) -> tuple[float, float, float, float]:
    """Parse 'min_lon,min_lat,max_lon,max_lat' into four numbers."""
    try:
        min_lon, min_lat, max_lon, max_lat = (float(v) for v in bbox.split(","))
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "bbox must be min_lon,min_lat,max_lon,max_lat",
        ) from exc
    if not (-180 <= min_lon < max_lon <= 180 and -90 <= min_lat < max_lat <= 90):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "bbox coordinates are out of range"
        )
    return min_lon, min_lat, max_lon, max_lat


@router.get("", response_model=ReportCollection)
def list_reports(
    db: DbSession,
    bbox: Annotated[
        str | None,
        Query(description="Visible map area: min_lon,min_lat,max_lon,max_lat"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 500,
):
    """List public reports for the map as GeoJSON, newest first."""
    query = (
        select(Report)
        .where(Report.visibility == ReportVisibility.PUBLIC)
        .order_by(Report.created_at.desc())
        .limit(limit)
    )
    if bbox:
        min_lon, min_lat, max_lon, max_lat = parse_bbox(bbox)
        area = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
        query = query.where(func.ST_Intersects(Report.location, cast(area, Geography)))

    reports = db.scalars(query).all()
    return ReportCollection(features=[ReportFeature.from_model(r) for r in reports])

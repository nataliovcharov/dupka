import io
from typing import Protocol

from PIL import Image, ImageFilter

from app.services.images import to_rgb

Box = tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels


class PrivacyDetector(Protocol):
    """Anything that finds faces and license plates in a photo."""

    def find(self, photo: Image.Image) -> tuple[list[Box], list[Box]]:
        """Returns (faces, plates)."""
        ...


def blur_boxes(photo: Image.Image, boxes: list[Box], grow: float = 0.2) -> Image.Image:
    """Blur each box, made a bit bigger so the edges are covered too.

    The region is shrunk to a few pixels and scaled back up, so nothing of
    the original can be recovered, then smoothed so it looks like a blur.
    """
    result = photo.copy()
    width, height = photo.size
    for x1, y1, x2, y2 in boxes:
        pad_x, pad_y = (x2 - x1) * grow / 2, (y2 - y1) * grow / 2
        left = max(0, int(x1 - pad_x))
        top = max(0, int(y1 - pad_y))
        right = min(width, int(x2 + pad_x) + 1)
        bottom = min(height, int(y2 + pad_y) + 1)
        if right - left < 2 or bottom - top < 2:
            continue
        region = result.crop((left, top, right, bottom))
        tiny = region.resize((6, max(1, round(6 * region.height / region.width))))
        smooth = tiny.resize(region.size, Image.Resampling.BILINEAR)
        radius = max(region.size) / 10
        result.paste(smooth.filter(ImageFilter.GaussianBlur(radius)), (left, top))
    return result


def anonymize(image: bytes, detector: PrivacyDetector) -> tuple[bytes, dict]:
    """Blur faces and license plates. Returns the new JPEG and what was blurred."""
    photo = to_rgb(Image.open(io.BytesIO(image)))
    faces, plates = detector.find(photo)
    blurred = blur_boxes(photo, faces + plates)
    output = io.BytesIO()
    blurred.save(output, format="JPEG", quality=90)
    return output.getvalue(), {"faces": len(faces), "plates": len(plates)}

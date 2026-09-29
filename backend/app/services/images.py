import io

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_SIDE = 2048  # larger photos are scaled down, the model works at 640 anyway


class InvalidImageError(ValueError):
    """The uploaded file is not a usable image."""


def to_rgb(image: Image.Image) -> Image.Image:
    """Convert to RGB, putting see-through parts on white.

    A plain convert("RGB") turns transparent areas black, which changes
    what the photo looks like to people and to the models.
    """
    if image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def clean_photo(data: bytes) -> bytes:
    """Check the upload is a real image, fix its rotation and strip all metadata.

    Returns the photo as a JPEG without EXIF (which can include the user's GPS).
    """
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise InvalidImageError("file is not a valid image") from exc

    # phones store rotation in EXIF, apply it before the metadata is dropped
    image = ImageOps.exif_transpose(image)
    image = to_rgb(image)
    image.thumbnail((MAX_SIDE, MAX_SIDE))

    output = io.BytesIO()
    image.save(
        output, format="JPEG", quality=90
    )  # saved without exif=, so none is kept
    return output.getvalue()

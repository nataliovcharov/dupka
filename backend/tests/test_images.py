import io

from PIL import Image

from app.services.images import clean_photo, to_rgb


def test_transparent_parts_become_white():
    logo = Image.new("RGBA", (10, 10), (0, 0, 0, 0))  # fully see-through
    logo.putpixel((5, 5), (0, 0, 0, 255))  # one solid black pixel

    rgb = to_rgb(logo)

    assert rgb.mode == "RGB"
    assert rgb.getpixel((0, 0)) == (255, 255, 255)
    assert rgb.getpixel((5, 5)) == (0, 0, 0)


def test_clean_photo_keeps_transparent_png_readable():
    buffer = io.BytesIO()
    Image.new("RGBA", (64, 64), (0, 0, 0, 0)).save(buffer, format="PNG")

    cleaned = Image.open(io.BytesIO(clean_photo(buffer.getvalue())))

    assert cleaned.format == "JPEG"
    red, green, blue = cleaned.getpixel((32, 32))
    assert min(red, green, blue) > 240  # white, allowing for JPEG noise

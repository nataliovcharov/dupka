import io

from PIL import Image, ImageChops, ImageStat

from app.services.privacy import anonymize, blur_boxes


class FakePrivacyDetector:
    def __init__(self, faces=(), plates=()):
        self.faces, self.plates = list(faces), list(plates)

    def find(self, photo):
        return self.faces, self.plates


def noisy_photo() -> Image.Image:
    # detail everywhere, so a blur is easy to measure
    return Image.effect_noise((200, 100), 80).convert("RGB")


def detail(photo: Image.Image, box) -> float:
    """High where there's detail, close to zero where it's blurred."""
    return ImageStat.Stat(photo.crop(box).convert("L")).stddev[0]


def test_blur_removes_detail_inside_the_box():
    photo = noisy_photo()
    blurred = blur_boxes(photo, [(20, 20, 60, 60)])

    inside = (25, 25, 55, 55)
    assert detail(blurred, inside) < detail(photo, inside) / 4


def test_blur_covers_a_bit_more_than_the_box():
    photo = noisy_photo()
    blurred = blur_boxes(photo, [(20, 20, 60, 60)])

    just_above = (22, 17, 58, 20)  # the box grows by 20%, 4 px here
    assert detail(blurred, just_above) < detail(photo, just_above) / 4


def test_rest_of_the_photo_is_unchanged():
    photo = noisy_photo()
    blurred = blur_boxes(photo, [(20, 20, 60, 60)])

    far_away = (100, 0, 200, 100)
    diff = ImageChops.difference(blurred.crop(far_away), photo.crop(far_away))
    assert diff.getbbox() is None


def test_boxes_outside_the_photo_are_ignored():
    photo = noisy_photo()
    blurred = blur_boxes(photo, [(500, 500, 600, 600), (-10, -10, -5, -5)])

    assert ImageChops.difference(blurred, photo).getbbox() is None


def test_anonymize_blurs_faces_and_plates_and_counts_them():
    photo = noisy_photo()
    buffer = io.BytesIO()
    photo.save(buffer, format="JPEG", quality=95)
    detector = FakePrivacyDetector(
        faces=[(20, 20, 60, 60)], plates=[(120, 40, 170, 60)]
    )

    data, counts = anonymize(buffer.getvalue(), detector)

    assert counts == {"faces": 1, "plates": 1}
    result = Image.open(io.BytesIO(data))
    assert result.format == "JPEG"
    assert result.size == photo.size
    for box in [(25, 25, 55, 55), (125, 43, 165, 57)]:
        assert detail(result, box) < detail(photo, box) / 4

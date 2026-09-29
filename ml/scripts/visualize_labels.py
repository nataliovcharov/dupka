import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw

from convert_rdd_to_yolo import CLASSES

COLORS = ["#e6194b", "#3cb44b", "#4363d8", "#f58231"]  # D00, D10, D20, D40


def draw_boxes(img_path, label_path, out_path):
    """Draw YOLO boxes on an image so the conversion can be checked by eye."""
    img = Image.open(img_path).convert("RGB")
    img_w, img_h = img.size
    draw = ImageDraw.Draw(img)

    for line in label_path.read_text().splitlines():
        class_id, x, y, w, h = line.split()
        class_id = int(class_id)
        # back from normalized center + size to corner pixels
        x, w = float(x) * img_w, float(w) * img_w
        y, h = float(y) * img_h, float(h) * img_h
        box = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)

        draw.rectangle(box, outline=COLORS[class_id], width=3)
        draw.text(
            (box[0] + 3, max(0, box[1] - 12)), CLASSES[class_id], fill=COLORS[class_id]
        )

    img.save(out_path)


def main():
    parser = argparse.ArgumentParser(description="Draw YOLO labels on sample images.")
    parser.add_argument("--data", type=Path, default=Path("data/yolo"))
    parser.add_argument("--split", default="train")
    parser.add_argument("--n", type=int, default=12, help="number of images to draw")
    parser.add_argument("--out", type=Path, default=Path("data/viz"))
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    label_dir = args.data / "labels" / args.split
    # only images that actually have damage
    labeled = sorted(p for p in label_dir.glob("*.txt") if p.read_text().strip())
    chosen = random.Random(args.seed).sample(labeled, min(args.n, len(labeled)))

    args.out.mkdir(parents=True, exist_ok=True)
    for label_path in chosen:
        img_path = args.data / "images" / args.split / f"{label_path.stem}.jpg"
        draw_boxes(img_path, label_path, args.out / f"{label_path.stem}.jpg")

    print(f"saved {len(chosen)} images to {args.out}")


if __name__ == "__main__":
    main()

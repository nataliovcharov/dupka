import argparse
import random
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

# list position = YOLO class id (D00 -> 0, D10 -> 1, D20 -> 2, D40 -> 3)
CLASSES = ["D00", "D10", "D20", "D40"]
SPLITS = ("train", "val", "test")


def voc_to_yolo(xmin, ymin, xmax, ymax, img_w, img_h):
    """Convert a VOC box (corner pixels) to YOLO format (normalized center + size)."""
    # some RDD2022 boxes go slightly past the image edge
    xmin = max(0, xmin)
    ymin = max(0, ymin)
    xmax = min(img_w, xmax)
    ymax = min(img_h, ymax)

    x_center = (xmin + xmax) / 2 / img_w
    y_center = (ymin + ymax) / 2 / img_h
    width = (xmax - xmin) / img_w
    height = (ymax - ymin) / img_h

    return (x_center, y_center, width, height)


def parse_voc_xml(xml_path):
    """Read one VOC annotation file and return its boxes as YOLO label lines."""
    root = ET.parse(xml_path).getroot()

    size = root.find("size")
    img_w = int(size.find("width").text)
    img_h = int(size.find("height").text)
    if img_w <= 0 or img_h <= 0:
        raise ValueError(f"invalid image size in {xml_path}")

    lines = []
    for obj in root.findall("object"):
        name = obj.find("name").text.strip()
        if name not in CLASSES:
            continue  # skip block cracks, repairs etc.

        box = obj.find("bndbox")
        xmin = float(box.find("xmin").text)
        ymin = float(box.find("ymin").text)
        xmax = float(box.find("xmax").text)
        ymax = float(box.find("ymax").text)

        x, y, w, h = voc_to_yolo(xmin, ymin, xmax, ymax, img_w, img_h)
        if w <= 0 or h <= 0:
            continue  # nothing left after clipping

        class_id = CLASSES.index(name)
        lines.append(f"{class_id} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")

    return lines


def split_items(items, val_frac, test_frac, seed):
    """Shuffle with a fixed seed and split into train/val/test."""
    items = sorted(items)  # same starting order on every machine
    random.Random(seed).shuffle(items)
    n_val = round(len(items) * val_frac)
    n_test = round(len(items) * test_frac)
    return {
        "val": items[:n_val],
        "test": items[n_val : n_val + n_test],
        "train": items[n_val + n_test :],
    }


def convert(src, out, countries, val_frac, test_frac, seed):
    """Convert the chosen countries to YOLO format and return per-split stats."""
    splits = {split: [] for split in SPLITS}
    for country in countries:
        img_dir = src / country / "train" / "images"
        if not img_dir.is_dir():
            raise FileNotFoundError(f"missing folder: {img_dir}")
        names = [p.name for p in img_dir.glob("*.jpg")]
        # split each country separately so every split has the same country mix
        for split, chosen in split_items(names, val_frac, test_frac, seed).items():
            splits[split] += [(country, name) for name in chosen]

    stats = {split: Counter() for split in SPLITS}
    for split, items in splits.items():
        img_out = out / "images" / split
        lbl_out = out / "labels" / split
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        for country, name in items:
            stem = Path(name).stem
            img_path = src / country / "train" / "images" / name
            xml_path = src / country / "train" / "annotations" / "xmls" / f"{stem}.xml"
            lines = parse_voc_xml(xml_path) if xml_path.exists() else []

            shutil.copy2(img_path, img_out / name)
            # empty label file = no damage, YOLO still learns from it
            text = "\n".join(lines) + "\n" if lines else ""
            (lbl_out / f"{stem}.txt").write_text(text)

            stats[split]["images"] += 1
            stats[split]["with_damage"] += bool(lines)
            for line in lines:
                stats[split][CLASSES[int(line.split()[0])]] += 1

    return stats


def write_data_yaml(out):
    """Write the dataset config YOLO needs for training."""
    names = "\n".join(f"  {i}: {name}" for i, name in enumerate(CLASSES))
    (out / "data.yaml").write_text(
        f"path: {out.resolve()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n"
        f"names:\n{names}\n"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Convert RDD2022 (VOC) to YOLO format."
    )
    parser.add_argument(
        "--src", type=Path, required=True, help="folder with the country folders"
    )
    parser.add_argument("--out", type=Path, required=True, help="output folder")
    parser.add_argument(
        "--countries", nargs="+", required=True, help="e.g. Czech Japan India"
    )
    parser.add_argument("--val", type=float, default=0.1, help="validation fraction")
    parser.add_argument("--test", type=float, default=0.1, help="test fraction")
    parser.add_argument(
        "--seed", type=int, default=42, help="fixed seed so the split is reproducible"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="replace --out if it exists"
    )
    args = parser.parse_args()

    if args.out.exists():
        if not args.overwrite:
            parser.error(f"{args.out} already exists, use --overwrite to replace it")
        shutil.rmtree(args.out)

    stats = convert(args.src, args.out, args.countries, args.val, args.test, args.seed)
    write_data_yaml(args.out)

    for split in SPLITS:
        print(f"{split}: {dict(stats[split])}")


if __name__ == "__main__":
    main()

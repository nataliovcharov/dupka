# Dupka ML

Road damage detection model (YOLO), trained on RDD2022.

## Setup
~~~bash
cd ml
uv sync
~~~

## Get the data
RDD2022 is only available as one 13 GB zip on Figshare, so I download just the country zips I need.
~~~bash
mkdir -p data/raw && cd data/raw
uvx remotezip "https://ndownloader.figshare.com/files/38030910" RDD2022/Czech.zip
cd RDD2022 && unzip -q Czech.zip && cd ../../..
~~~
For full training, repeat for `Japan.zip`, `India.zip`, `United_States.zip` and `China_MotorBike.zip`.

## Convert to YOLO format
~~~bash
uv run python scripts/convert_rdd_to_yolo.py --src data/raw/RDD2022 --out data/yolo --countries Czech
~~~
Splits 80/10/10 per country with a fixed seed and writes `data/yolo/data.yaml`.

## Check the labels
~~~bash
uv run python scripts/visualize_labels.py
~~~
Draws the boxes on 12 random images in `data/viz/`.

## Data and license
RDD2022: Arya et al., "RDD2022: A multi-national image dataset for automatic road damage detection" (CC BY-SA 4.0). See `docs/decisions/0001-training-data.md`.

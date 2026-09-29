# 0001. Training data for the baseline model

**Status:** Accepted, 2026-09-29

## Context
The detector needs road photos with bounding boxes for each damage type, under a license that allows use in a public project. Most public road damage data is captured from vehicle-mounted cameras, while Dupka users will take close-up handheld photos.

## Decision
- Train the baseline on **RDD2022**, using five countries: Czech, Japan, India, United States and China (motorbike). That is about 27,800 labeled images.
- Skip **Norway** for now (10.6 GB, very wide high-resolution images that need tiling) and **China drone** (aerial view, not what a phone sees).
- Use four classes: D00 longitudinal crack, D10 transverse crack, D20 alligator crack, D40 pothole. Other classes are dropped.
- The official test labels aren't public, so I split the labeled data myself: 80/10/10 train/val/test, split per country with a fixed seed (42) so the split is reproducible and every split has the same country mix.
- The original per-country download links no longer work. I download only the needed country zips from the Figshare archive with `remotezip`, instead of the full 13 GB file.

## Consequences
- **Domain gap:** RDD2022 is dashcam footage with small, distant damage. A local Skopje test set is needed to measure real performance.
- **Class imbalance:** potholes are about 11% of boxes in the Czech data, the class that matters most for Dupka.
- **Label noise:** some boxes are loose or debatable (e.g. worn paint marked as a crack), which limits achievable accuracy.
- **License:** RDD2022 images are CC BY-SA 4.0 (the Figshare record says CC BY 4.0). I follow the stricter one and credit the dataset.

## Candidates for later experiments
| Dataset | What it adds | License | Plan |
|---|---|---|---|
| Stellenbosch pothole dataset | 7,588 pothole boxes, dashcam | CC0 | Pothole boost experiment |
| HRP4K (Scientific Data, 2026) | 7,217 pothole boxes, 4K vehicle view | CC BY 4.0 | Pothole boost experiment |
| Roboflow Pothole | 665 images, closer views | ODbL | Close-up evaluation set |
| Own Skopje photos | Handheld close-ups, local roads | Own | Local test set and fine-tuning |

Rejected: Kaggle "Pothole Image Dataset" (no boxes, web-scraped) and michelpf/dataset-pothole (no license).

Each candidate is added one at a time and kept only if it improves results on the same test set.

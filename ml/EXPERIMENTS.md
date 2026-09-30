# Experiments

One entry per training run. Change one thing at a time, so each result can be explained.

Weights and full run folders are on Google Drive (`MyDrive/dupka/runs/<name>`), not in Git.

## Summary

| ID | Model | Data | Epochs | Val mAP50 | Val mAP50-95 | Test mAP50 | Pothole (D40) mAP50 | Notes |
|---|---|---|---|---|---|---|---|---|
| e001 | YOLO26s | rdd5-v1 | 30 | 0.647 | 0.337 | 0.637 | 0.513 (test) | baseline |

## e001-yolo26s-rdd5-baseline

**Question:** how well does a small pretrained YOLO detect the four RDD2022 damage types on our 5-country dataset?

**Setup**
- Model: YOLO26s, COCO-pretrained (9.9M parameters), Ultralytics 8.4.165
- Data: `rdd5-v1` (Czech, Japan, India, United_States, China_MotorBike), 80/10/10 split per country, seed 42
  - train 22,257 images (7,133 without damage), val 2,783 images (860 without damage)
- Training: 30 epochs, imgsz 640, batch 16, optimizer auto (MuSGD, lr 0.01), mosaic off for the last 10 epochs, patience 10, seed 42, deterministic
- Hardware: Colab T4, 4.1 hours

**Validation results** (`best.pt`)

| Class | Images | Instances | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|---|---|
| all | 2,783 | 4,204 | 0.661 | 0.591 | 0.647 | 0.337 |
| D00 longitudinal crack | 1,040 | 1,661 | 0.645 | 0.636 | 0.671 | 0.392 |
| D10 transverse crack | 607 | 966 | 0.645 | 0.575 | 0.639 | 0.317 |
| D20 alligator crack | 784 | 976 | 0.721 | 0.665 | 0.724 | 0.403 |
| D40 pothole | 331 | 601 | 0.633 | 0.488 | 0.555 | 0.235 |

Speed on T4: 8.0 ms inference per image (plus 2.5 ms pre and post processing).

**Test results** (`best.pt`, run once)

| Class | Images | Instances | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|---|---|
| all | 2,783 | 3,966 | 0.656 | 0.591 | 0.637 | 0.330 |
| D00 longitudinal crack | 982 | 1,543 | 0.662 | 0.649 | 0.691 | 0.402 |
| D10 transverse crack | 561 | 853 | 0.620 | 0.580 | 0.615 | 0.304 |
| D20 alligator crack | 780 | 976 | 0.713 | 0.666 | 0.729 | 0.388 |
| D40 pothole | 328 | 594 | 0.631 | 0.469 | 0.513 | 0.226 |

Test split has 896 images without damage. Evaluated on Colab CPU (582 ms inference per image, not comparable to the T4 number).

**Observations**
- Potholes are the weakest class, and the most important one for Dupka. Recall 0.49 means about half the potholes in val are missed.
  - Likely causes: fewest examples (601 in val vs 1,661 for D00), and pothole shapes vary a lot.
- Val mAP50 rose fast until epoch ~23, then stayed flat around 0.647 for the last 6 epochs, while the learning rate was already low. More epochs alone may only help a little.
- `best.pt` was picked by its val score, so val numbers are slightly optimistic. The test set is the number to report.
- Test is 0.010 below val (pothole 0.042), so val was only a bit optimistic. Pothole recall on test is 0.469.
- F1 peaks at 0.62 at confidence 0.281 on val (pothole around 0.25).

**Next**
- Look at missed potholes (false negatives) to see what they have in common
- Ideas for e002, pick one: longer training (e.g. 60 epochs), larger model (YOLO26m), or more pothole examples (extra datasets under open licenses, see `docs/decisions/0001-training-data.md`)

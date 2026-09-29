# Labeling guidelines

How I capture and label Skopje road photos. Same rules every time, so the labels stay consistent.

## Capturing photos
- **Two views.** Most photos handheld, standing next to the damage, camera pointing down at 30-60 degrees, damage filling a good part of the frame (this is how users will take photos). Some photos from further away (3-10 m) along the road.
- **Variety:** different neighborhoods, times of day, dry and wet roads, sun and shade.
- **Also shoot undamaged road** (about 1 in 5 photos). The model needs to see normal roads too.
- **GPS on** in the camera settings.
- **Safety first:** shoot from the sidewalk or roadside, never stand in traffic.
- **Privacy:** avoid close shots of faces and license plates. Anything visible gets blurred before publishing.
- **Keep the originals.** Never edit or crop the source photos.

## File names
`skp_YYYYMMDD_NNN.jpg`, for example `skp_20261003_001.jpg`. Date taken, then a running number.

## Classes
Same four classes as RDD2022:

| ID | Code | Name | What it looks like |
|---|---|---|---|
| 0 | D00 | Longitudinal crack | Crack running along the direction of the road |
| 1 | D10 | Transverse crack | Crack running across the road |
| 2 | D20 | Alligator crack | Network of connected cracks, like a grid or scales |
| 3 | D40 | Pothole | A hole where asphalt is missing and there is visible depth |

## Box rules
1. **Tight boxes.** The box touches the outer edges of the damage, with no extra road around it.
2. **One box per damage.** A long crack gets one box. If it clearly splits into separate cracks, one box each.
3. **Potholes:** box the whole hole including broken edges, not the wet area or loose gravel around it.
4. **Alligator cracks:** one box around the whole connected area.
5. **Partly visible damage** (cut off by the frame or hidden by a car): label the visible part if more than about a third is visible, otherwise skip it.
6. **When unsure, skip it.** A missing label hurts less than a wrong one.

## Do not label
- Worn or faded road paint, road markings, manhole covers, drain grates
- Patched or repaired asphalt, unless it is broken again
- Shadows, stains, wet patches, leaves
- Joints between concrete slabs and tram tracks
- Damage on sidewalks (only the road surface counts)

## Tool
Label Studio, running locally in Docker. Export in YOLO format.

## Quality check
- After labeling each batch, look through all of it once with the boxes drawn.
- After the first 100 photos, re-label 10 of them without looking at the old labels and compare. If they differ a lot, tighten these rules.
- Update this document when a new edge case comes up.

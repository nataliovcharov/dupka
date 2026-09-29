from app.services.detector import Detection

# most urgent first: potholes, then alligator cracking, then single cracks
PRIORITY = ["D40", "D20", "D10", "D00"]


def box_area(detection: Detection) -> float:
    x1, y1, x2, y2 = detection.box
    return (x2 - x1) * (y2 - y1)


def summarize(detections: list[Detection]) -> tuple[str | None, str | None]:
    """Pick the report's main damage type and severity.

    First version of the rule. To be tuned once real Skopje reports come in.
    """
    if not detections:
        return None, None

    # most urgent type first, and the biggest one of that type
    main = min(detections, key=lambda d: (PRIORITY.index(d.damage_type), -box_area(d)))

    if main.damage_type == "D40":
        severity = "high" if box_area(main) >= 0.05 else "medium"
    elif main.damage_type == "D20":
        severity = "medium"
    else:
        severity = "low"
    return main.damage_type, severity

"""Lane ROI polygons — N/S/E/W regions of a camera frame (fractions 0..1).

Coordinates are configurable per camera; defaults assume a standard
four-way junction view. Detection centres falling inside a polygon count
toward that approach.
"""
from __future__ import annotations

DEFAULT_ROIS: dict[str, list[tuple[float, float]]] = {
    "N": [(0.35, 0.0), (0.65, 0.0), (0.65, 0.45), (0.35, 0.45)],
    "S": [(0.35, 0.55), (0.65, 0.55), (0.65, 1.0), (0.35, 1.0)],
    "E": [(0.55, 0.35), (1.0, 0.35), (1.0, 0.65), (0.55, 0.65)],
    "W": [(0.0, 0.35), (0.45, 0.35), (0.45, 0.65), (0.0, 0.65)],
}


def point_in_polygon(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xinters = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1
            if x < xinters:
                inside = not inside
    return inside


def approach_for_point(x: float, y: float, rois: dict | None = None) -> str | None:
    rois = rois or DEFAULT_ROIS
    for approach, poly in rois.items():
        if point_in_polygon(x, y, poly):
            return approach
    return None

from __future__ import annotations

import math
from typing import Any


def _ellipse(cx: float, cy: float, rx: float, ry: float, n: int = 72) -> list[list[float]]:
    ring: list[list[float]] = []
    for i in range(n):
        t = i / n * math.pi * 2
        ring.append([cx + rx * math.cos(t), cy + ry * math.sin(t)])
    ring.append(ring[0])
    return ring


def generate_water(layout: dict[str, Any], bbox: list[float]) -> dict[str, Any]:
    min_x, min_y, max_x, max_y = bbox
    lake = layout["lake"]
    cx, cy = lake["center"]
    if not (min_x - lake["rx"] <= cx <= max_x + lake["rx"] and min_y - lake["ry"] <= cy <= max_y + lake["ry"]):
        return {"type": "FeatureCollection", "features": []}

    ring = _ellipse(cx, cy, lake["rx"], lake["ry"], n=88)
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"kind": "lake", "name": "Lake Laogai Basin"},
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        ],
    }


def generate_open_spaces(layout: dict[str, Any], bbox: list[float]) -> dict[str, Any]:
    min_x, min_y, max_x, max_y = bbox
    features: list[dict[str, Any]] = []
    for p in layout["civic"]:
        cx, cy = p["center"]
        if not (min_x <= cx <= max_x and min_y <= cy <= max_y):
            continue
        rr = p["radius"]
        ring = _ellipse(cx, cy, layout["metro_scale"]["w"] * rr, layout["metro_scale"]["h"] * rr * 0.7, n=56)
        features.append(
            {
                "type": "Feature",
                "properties": {"kind": "park", "name": p["name"]},
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )

    return {"type": "FeatureCollection", "features": features}

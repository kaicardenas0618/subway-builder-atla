from __future__ import annotations

import math
from typing import Any


def generate_campuses(layout: dict[str, Any], bbox: list[float]) -> dict[str, Any]:
    min_x, min_y, max_x, max_y = bbox
    features: list[dict[str, Any]] = []

    for c in layout["campuses"]:
        cx, cy = c["center"]
        if not (min_x <= cx <= max_x and min_y <= cy <= max_y):
            continue
        rx = layout["metro_scale"]["w"] * c["radius"]
        ry = layout["metro_scale"]["h"] * c["radius"] * 0.8
        ring: list[list[float]] = []
        for i in range(48):
            t = i / 48 * math.pi * 2
            ring.append([cx + rx * math.cos(t), cy + ry * math.sin(t)])
        ring.append(ring[0])
        features.append(
            {
                "type": "Feature",
                "properties": {"kind": "campus", "name": c["name"]},
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )

    return {"type": "FeatureCollection", "features": features}

from __future__ import annotations

import math
from typing import Any


def _rect(center_x: float, center_y: float, width: float, height: float, angle: float) -> list[list[float]]:
    ca = math.cos(angle)
    sa = math.sin(angle)
    pts = [
        (-width / 2, -height / 2),
        (width / 2, -height / 2),
        (width / 2, height / 2),
        (-width / 2, height / 2),
    ]
    ring: list[list[float]] = []
    for x, y in pts:
        rx = center_x + x * ca - y * sa
        ry = center_y + x * sa + y * ca
        ring.append([rx, ry])
    ring.append(ring[0])
    return ring


def generate_runways_taxiways(layout: dict[str, Any], bbox: list[float]) -> dict[str, Any]:
    min_x, min_y, max_x, max_y = bbox
    w = max_x - min_x
    h = max_y - min_y

    features: list[dict[str, Any]] = []
    for idx, key in enumerate(["primary_airport", "secondary_airport"]):
        ap = layout[key]
        ax, ay = ap["center"]
        if not (min_x - 0.1 * w <= ax <= max_x + 0.1 * w and min_y - 0.1 * h <= ay <= max_y + 0.1 * h):
            continue

        base_len = w * (0.22 if key == "primary_airport" else 0.12)
        base_wid = h * (0.016 if key == "primary_airport" else 0.012)
        runway_count = 2 if key == "primary_airport" else 1

        for i in range(runway_count):
            shift = (i - (runway_count - 1) / 2) * base_wid * 2.8
            cx = ax + math.cos(ap["angle"] + math.pi / 2) * shift
            cy = ay + math.sin(ap["angle"] + math.pi / 2) * shift
            ring = _rect(cx, cy, base_len, base_wid, ap["angle"])
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "roadType": "runway",
                        "z_order": 0,
                        "osm_way_id": f"{key}-runway-{i+1}",
                        "area": 0,
                    },
                    "geometry": {"type": "Polygon", "coordinates": [ring]},
                }
            )

            taxi = _rect(cx, cy - base_wid * 2.4, base_len * 0.96, base_wid * 0.52, ap["angle"])
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "roadType": "taxiway",
                        "z_order": 0,
                        "osm_way_id": f"{key}-taxiway-{i+1}",
                        "area": 0,
                    },
                    "geometry": {"type": "Polygon", "coordinates": [taxi]},
                }
            )

    return {"type": "FeatureCollection", "features": features}

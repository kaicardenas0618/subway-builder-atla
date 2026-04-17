from __future__ import annotations

import math
from typing import Any

def generate_campuses(plan: dict[str, Any], bbox: list[float]) -> dict[str, Any]:
    min_x, min_y, max_x, max_y = bbox
    mw = plan["metro_scale"]["w"]
    mh = plan["metro_scale"]["h"]
    features: list[dict[str, Any]] = []

    for c in plan["campuses"]:
        cx, cy = c["center"]
        if not (min_x - mw * 0.05 <= cx <= max_x + mw * 0.05 and
                min_y - mh * 0.05 <= cy <= max_y + mh * 0.05):
            continue
        rx = mw * c["radius"]
        ry = mh * c["radius"] * 0.82
        ring: list[list[float]] = []
        for i in range(48):
            t = i / 48 * math.pi * 2
            wf = 1.0 + 0.05 * math.sin(t * 5)
            ring.append([cx + rx * wf * math.cos(t), cy + ry * wf * math.sin(t)])
        ring.append(ring[0])
        features.append({
            "type": "Feature",
            "properties": {"kind": "campus", "name": c["name"]},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })

    return {"type": "FeatureCollection", "features": features}

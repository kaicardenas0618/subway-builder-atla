from __future__ import annotations

import math
from typing import Any

def _rect(cx: float, cy: float, w: float, h: float, angle: float) -> list[list[float]]:
    ca, sa = math.cos(angle), math.sin(angle)
    pts = [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]
    ring = [[cx + x*ca - y*sa, cy + x*sa + y*ca] for x, y in pts]
    ring.append(ring[0])
    return ring

def _in_bbox(x: float, y: float, bbox: list[float], pad: float = 0.0) -> bool:
    return (bbox[0] - pad) <= x <= (bbox[2] + pad) and (bbox[1] - pad) <= y <= (bbox[3] + pad)

def generate_runways_taxiways(plan: dict[str, Any], bbox: list[float]) -> dict[str, Any]:
    features: list[dict[str, Any]] = []

    for key in ["primary_airport", "secondary_airport"]:
        ap = plan[key]
        cx, cy = ap["center"]
        if not _in_bbox(cx, cy, bbox, max(ap["size_x"], ap["size_y"])):
            continue

        n_runways = ap["runways"]
        runway_len = ap["size_x"] * 0.85
        runway_wid = ap["size_y"] * 0.12
        angle = ap["angle"]

        for i in range(n_runways):
            offset = (i - (n_runways - 1) / 2) * runway_wid * 3.5
            ox = math.cos(angle + math.pi/2) * offset
            oy = math.sin(angle + math.pi/2) * offset
            ring = _rect(cx + ox, cy + oy, runway_len, runway_wid, angle)
            features.append({
                "type": "Feature",
                "properties": {"roadType": "runway", "z_order": 0,
                               "osm_way_id": f"{key}-runway-{i+1}", "area": 0},
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            })
            taxi_off = runway_wid * 2.0
            tx = cx + ox + math.cos(angle + math.pi/2) * taxi_off
            ty = cy + oy + math.sin(angle + math.pi/2) * taxi_off
            taxi = _rect(tx, ty, runway_len * 0.92, runway_wid * 0.45, angle)
            features.append({
                "type": "Feature",
                "properties": {"roadType": "taxiway", "z_order": 0,
                               "osm_way_id": f"{key}-taxiway-{i+1}", "area": 0},
                "geometry": {"type": "Polygon", "coordinates": [taxi]},
            })

        terminal = _rect(cx, cy, ap["size_x"] * 0.3, ap["size_y"] * 0.25, angle + 0.1)
        features.append({
            "type": "Feature",
            "properties": {"roadType": "terminal", "z_order": 1,
                           "osm_way_id": f"{key}-terminal", "area": 0},
            "geometry": {"type": "Polygon", "coordinates": [terminal]},
        })

    return {"type": "FeatureCollection", "features": features}

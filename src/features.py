from __future__ import annotations

import math
from typing import Any

def _ellipse(cx: float, cy: float, rx: float, ry: float, n: int = 72,
             wobble: float = 0.0) -> list[list[float]]:
    ring: list[list[float]] = []
    for i in range(n):
        t = i / n * math.pi * 2
        wf = 1.0 + wobble * math.sin(t * 5) + wobble * 0.6 * math.cos(t * 7)
        ring.append([cx + rx * wf * math.cos(t), cy + ry * wf * math.sin(t)])
    ring.append(ring[0])
    return ring

def _in_bbox(x: float, y: float, bbox: list[float], pad: float = 0.0) -> bool:
    return (bbox[0] - pad) <= x <= (bbox[2] + pad) and (bbox[1] - pad) <= y <= (bbox[3] + pad)

def generate_water(plan: dict[str, Any], bbox: list[float]) -> dict[str, Any]:
    features: list[dict[str, Any]] = []

    lake = plan["lake"]
    cx, cy = lake["center"]
    if _in_bbox(cx, cy, bbox, max(lake["rx"], lake["ry"]) * 1.5):
        ring = _ellipse(cx, cy, lake["rx"], lake["ry"], n=96, wobble=0.04)
        features.append({
            "type": "Feature",
            "properties": {"kind": "lake", "name": lake["name"]},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })

    for seg in plan.get("river_segments", []):
        (x0, y0), (x1, y1) = seg
        if not (_in_bbox(x0, y0, bbox, 0.05) or _in_bbox(x1, y1, bbox, 0.05)):
            continue
        dx, dy = x1 - x0, y1 - y0
        length = math.sqrt(dx*dx + dy*dy)
        if length < 1e-9:
            continue
        nx, ny = -dy / length * 0.003, dx / length * 0.003
        ring = [
            [x0 + nx, y0 + ny], [x1 + nx, y1 + ny],
            [x1 - nx, y1 - ny], [x0 - nx, y0 - ny],
            [x0 + nx, y0 + ny],
        ]
        features.append({
            "type": "Feature",
            "properties": {"kind": "river", "name": "Canal"},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })

    return {"type": "FeatureCollection", "features": features}

def generate_open_spaces(plan: dict[str, Any], bbox: list[float]) -> dict[str, Any]:
    features: list[dict[str, Any]] = []

    for p in plan["parks"]:
        cx, cy = p["center"]
        if not _in_bbox(cx, cy, bbox, max(p["rx"], p["ry"]) * 1.5):
            continue
        wobble = 0.06 if p["kind"] in ("park", "forest") else 0.02
        ring = _ellipse(cx, cy, p["rx"], p["ry"], n=48, wobble=wobble)
        features.append({
            "type": "Feature",
            "properties": {"kind": p["kind"], "name": p["name"]},
            "geometry": {"type": "Polygon", "coordinates": [ring]},
        })

    return {"type": "FeatureCollection", "features": features}

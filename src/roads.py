from __future__ import annotations

import math
import random
from typing import Any

from .districts import classify_district


def _in_bbox(x: float, y: float, bbox: list[float], pad_frac: float = 0.0) -> bool:
    min_x, min_y, max_x, max_y = bbox
    w = max_x - min_x
    h = max_y - min_y
    return (min_x - w * pad_frac) <= x <= (max_x + w * pad_frac) and (min_y - h * pad_frac) <= y <= (max_y + h * pad_frac)


def _ring(center: tuple[float, float], rx: float, ry: float, n: int, wobble: float = 0.0) -> list[list[float]]:
    cx, cy = center
    pts: list[list[float]] = []
    for i in range(n):
        t = i / n * math.pi * 2
        wf = 1.0 + wobble * math.sin(t * 3) + wobble * 0.7 * math.cos(t * 5)
        pts.append([cx + rx * wf * math.cos(t), cy + ry * wf * math.sin(t)])
    pts.append(pts[0])
    return pts


def _curved_line(x0: float, y0: float, x1: float, y1: float, waviness: float, n: int = 24) -> list[list[float]]:
    dx = x1 - x0
    dy = y1 - y0
    l = math.sqrt(dx * dx + dy * dy)
    if l < 1e-9:
        return [[x0, y0], [x1, y1]]
    px = -dy / l
    py = dx / l
    coords: list[list[float]] = []
    for i in range(n + 1):
        t = i / n
        x = x0 + dx * t
        y = y0 + dy * t
        b = math.sin(t * math.pi * 2) * waviness + math.sin(t * math.pi * 4) * waviness * 0.35
        coords.append([x + px * b, y + py * b])
    return coords


def generate_roads(layout: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(int(cfg["build"]["seed"]) + 1201)
    bbox = cfg["map"]["bbox"]
    min_x, min_y, max_x, max_y = bbox
    w = max_x - min_x
    h = max_y - min_y
    cx, cy = layout["center"]
    mw = layout["metro_scale"]["w"]
    mh = layout["metro_scale"]["h"]

    features: list[dict[str, Any]] = []

    # Expressway and ring boulevards.
    for i, rr in enumerate(layout["ring_radii"]):
        ring = _ring((cx, cy), mw * rr, mh * rr * 0.92, n=120, wobble=0.04 if i > 0 else 0.02)
        if any(_in_bbox(p[0], p[1], bbox, pad_frac=0.02) for p in ring):
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "roadClass": "expressway" if i < 2 else "major",
                        "structure": "normal",
                        "name": f"Ring Corridor {i+1}",
                    },
                    "geometry": {"type": "LineString", "coordinates": ring},
                }
            )

    # Radial connectors.
    for i in range(20):
        ang = i * (math.pi * 2 / 20) + (0.03 if i % 2 == 0 else -0.02)
        x0 = cx - math.cos(ang) * mw * 0.55
        y0 = cy - math.sin(ang) * mh * 0.55
        x1 = cx + math.cos(ang) * mw * 0.55
        y1 = cy + math.sin(ang) * mh * 0.55
        coords = _curved_line(x0, y0, x1, y1, waviness=min(mw, mh) * 0.01, n=28)
        if any(_in_bbox(p[0], p[1], bbox) for p in coords):
            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "roadClass": "trunk" if i % 3 == 0 else "arterial",
                        "structure": "elevated" if i % 5 == 0 else "normal",
                        "name": f"Radial Spine {i+1}",
                    },
                    "geometry": {"type": "LineString", "coordinates": coords},
                }
            )

    # District local fabrics from neighborhood seeds (non-lattice).
    seed_count = int(max(120, cfg["build"]["building_rows"] * cfg["build"]["building_cols"] * 0.015))
    for i in range(seed_count):
        sx = min_x + rng.random() * w
        sy = min_y + rng.random() * h
        district = classify_district(sx, sy, layout)
        if district in {"water"}:
            continue

        if district in {"imperial_core", "cbd"}:
            segs, spacing, road_class = 8, min(w, h) * 0.010, "collector"
        elif district in {"inner_mixed", "inner_residential", "campus", "entertainment"}:
            segs, spacing, road_class = 6, min(w, h) * 0.014, "collector"
        elif district in {"industrial", "logistics", "airport"}:
            segs, spacing, road_class = 5, min(w, h) * 0.020, "major"
        else:
            segs, spacing, road_class = 4, min(w, h) * 0.022, "local"

        base_ang = rng.random() * math.pi
        for j in range(segs):
            a = base_ang + (j / max(1, segs - 1) - 0.5) * 1.8
            ln = spacing * (1.3 + rng.random() * 2.2)
            x0 = sx - math.cos(a) * ln
            y0 = sy - math.sin(a) * ln
            x1 = sx + math.cos(a) * ln
            y1 = sy + math.sin(a) * ln
            coords = _curved_line(x0, y0, x1, y1, waviness=spacing * (0.12 + rng.random() * 0.14), n=12)
            if any(_in_bbox(p[0], p[1], bbox) for p in coords):
                features.append(
                    {
                        "type": "Feature",
                        "properties": {
                            "roadClass": road_class,
                            "structure": "normal",
                            "name": f"{district.replace('_', ' ').title()} Link {i}-{j}",
                        },
                        "geometry": {"type": "LineString", "coordinates": coords},
                    }
                )

    return {"type": "FeatureCollection", "features": features}

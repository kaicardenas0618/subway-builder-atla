from __future__ import annotations

import math
import random
from typing import Any

from .blocks import generate_blocks
from .parcels import subdivide_block
from .districts import classify_district

def _centroid(ring: list[list[float]]) -> tuple[float, float]:
    n = len(ring) - 1
    if n <= 0:
        return ring[0][0], ring[0][1]
    return sum(p[0] for p in ring[:n]) / n, sum(p[1] for p in ring[:n]) / n

def _bbox(ring: list[list[float]]) -> list[float]:
    xs = [p[0] for p in ring[:-1]]
    ys = [p[1] for p in ring[:-1]]
    return [min(xs), min(ys), max(xs), max(ys)]

def _rect_footprint(cx: float, cy: float, w: float, h: float, a: float) -> list[list[float]]:
    ca, sa = math.cos(a), math.sin(a)
    pts = [(-w/2, -h/2), (w/2, -h/2), (w/2, h/2), (-w/2, h/2)]
    ring = [[cx + x*ca - y*sa, cy + x*sa + y*ca] for x, y in pts]
    ring.append(ring[0])
    return ring

def _l_shape(cx: float, cy: float, w: float, h: float, a: float, rng: random.Random) -> list[list[float]]:
    ca, sa = math.cos(a), math.sin(a)
    cut_x = 0.45 + rng.random() * 0.25
    cut_y = 0.35 + rng.random() * 0.30
    pts = [
        (-w/2, -h/2), (w/2, -h/2), (w/2, -h/2 + h*cut_y),
        (-w/2 + w*cut_x, -h/2 + h*cut_y), (-w/2 + w*cut_x, h/2),
        (-w/2, h/2),
    ]
    ring = [[cx + x*ca - y*sa, cy + x*sa + y*ca] for x, y in pts]
    ring.append(ring[0])
    return ring

def _u_shape(cx: float, cy: float, w: float, h: float, a: float, rng: random.Random) -> list[list[float]]:
    ca, sa = math.cos(a), math.sin(a)
    iw = w * (0.3 + rng.random() * 0.2)
    ih = h * (0.3 + rng.random() * 0.25)
    pts = [
        (-w/2, -h/2), (w/2, -h/2), (w/2, h/2),
        (iw/2, h/2), (iw/2, -h/2 + ih), (-iw/2, -h/2 + ih),
        (-iw/2, h/2), (-w/2, h/2),
    ]
    ring = [[cx + x*ca - y*sa, cy + x*sa + y*ca] for x, y in pts]
    ring.append(ring[0])
    return ring

def _podium_tower(cx: float, cy: float, w: float, h: float, a: float,
                  rng: random.Random) -> tuple[list[list[float]], int]:
    return _rect_footprint(cx, cy, w, h, a), rng.randint(8, 20)

def _building_height(district: str, core_dist: float, rng: random.Random) -> int:
    proximity = max(0.0, 1.0 - core_dist)

    if district == "cbd":
        return 20 + int(proximity * 55) + rng.randint(0, 18)
    if district == "subcenter":
        return 12 + int(proximity * 30) + rng.randint(0, 10)
    if district == "imperial_core":
        return 2 + rng.randint(0, 6)
    if district == "inner_mixed":
        return 8 + int(proximity * 18) + rng.randint(0, 8)
    if district == "inner_residential":
        return 5 + int(proximity * 12) + rng.randint(0, 6)
    if district == "entertainment":
        return 6 + int(proximity * 14) + rng.randint(0, 8)
    if district in ("outer_residential", "peri_urban_mixed"):
        return 3 + rng.randint(0, 7)
    if district == "peri_residential":
        return 2 + rng.randint(0, 4)
    if district in ("industrial", "logistics"):
        return 1 + rng.randint(0, 3)
    if district == "campus":
        return 3 + rng.randint(0, 6)
    if district == "airport":
        return 1 + rng.randint(0, 4)
    return 3 + rng.randint(0, 5)

def generate_buildings_index(plan: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(int(cfg["build"]["seed"]) + 3107)
    bbox = cfg["map"]["bbox"]
    min_x, min_y, max_x, max_y = bbox
    cx, cy = plan["center"]
    mw = plan["metro_scale"]["w"]
    mh = plan["metro_scale"]["h"]
    cell_size = float(cfg["build"]["building_cell_size_deg"])

    blocks = generate_blocks(plan, cfg)
    buildings: list[dict[str, Any]] = []
    district_counts: dict[str, int] = {}

    for block in blocks:
        parcels = subdivide_block(block, rng)
        for parcel in parcels:
            px, py = parcel["center"]
            pw, ph = parcel["width"], parcel["height"]
            pa = parcel["angle"]
            district = parcel["district"]

            core_dist = math.sqrt(((px - cx) / (mw * 0.28)) ** 2 + ((py - cy) / (mh * 0.28)) ** 2)
            core_dist = min(1.5, core_dist)

            if district == "imperial_core":
                if rng.random() < 0.4:
                    ring = _u_shape(px, py, pw * 0.85, ph * 0.85, pa, rng)
                else:
                    ring = _rect_footprint(px, py, pw * 0.80, ph * 0.80, pa)
                floors = _building_height(district, core_dist, rng)
            elif district == "cbd":
                if rng.random() < 0.35:
                    ring, tower_bonus = _podium_tower(px, py, pw * 0.90, ph * 0.90, pa, rng)
                    floors = _building_height(district, core_dist, rng) + tower_bonus
                elif rng.random() < 0.5:
                    ring = _l_shape(px, py, pw * 0.88, ph * 0.88, pa, rng)
                    floors = _building_height(district, core_dist, rng)
                else:
                    ring = _rect_footprint(px, py, pw * 0.90, ph * 0.90, pa)
                    floors = _building_height(district, core_dist, rng)
            elif district in ("inner_mixed", "inner_residential", "subcenter"):
                if rng.random() < 0.2:
                    ring = _l_shape(px, py, pw * 0.85, ph * 0.85, pa, rng)
                else:
                    ring = _rect_footprint(px, py, pw * 0.85, ph * 0.85, pa)
                floors = _building_height(district, core_dist, rng)
            elif district in ("industrial", "logistics"):
                ring = _rect_footprint(px, py, pw * 0.92, ph * 0.92, pa)
                floors = _building_height(district, core_dist, rng)
            elif district == "campus":
                ring = _rect_footprint(px, py, pw * 0.78, ph * 0.78, pa)
                floors = _building_height(district, core_dist, rng)
            elif district == "airport":
                ring = _rect_footprint(px, py, pw * 0.90, ph * 0.75, pa)
                floors = _building_height(district, core_dist, rng)
            else:
                shrink = 0.70 + rng.random() * 0.15
                ring = _rect_footprint(px, py, pw * shrink, ph * shrink, pa)
                floors = _building_height(district, core_dist, rng)

            buildings.append({"b": _bbox(ring), "f": max(1, floors), "p": [ring]})
            district_counts[district] = district_counts.get(district, 0) + 1

    cells_map: dict[tuple[int, int], list[int]] = {}
    for i, b in enumerate(buildings):
        bx = (b["b"][0] + b["b"][2]) / 2
        by = (b["b"][1] + b["b"][3]) / 2
        ix = int((bx - min_x) / max(1e-9, cell_size))
        iy = int((by - min_y) / max(1e-9, cell_size))
        cells_map.setdefault((ix, iy), []).append(i)

    max_ix = max((k[0] for k in cells_map), default=0) + 1
    max_iy = max((k[1] for k in cells_map), default=0) + 1
    cells = [[ix, iy, *ids] for (ix, iy), ids in sorted(cells_map.items())]

    return {
        "cs": cell_size,
        "bbox": bbox,
        "grid": [max_ix, max_iy],
        "cells": cells,
        "buildings": buildings,
        "stats": {
            "count": len(buildings),
            "maxDepth": max((len(c) - 2 for c in cells), default=0),
            "districtCounts": district_counts,
        },
    }

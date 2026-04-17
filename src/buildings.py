from __future__ import annotations

import math
import random
from typing import Any

from .blocks import generate_blocks
from .parcels import subdivide_block


def _centroid(ring: list[list[float]]) -> tuple[float, float]:
    x = sum(p[0] for p in ring[:-1]) / max(1, len(ring) - 1)
    y = sum(p[1] for p in ring[:-1]) / max(1, len(ring) - 1)
    return x, y


def _bbox_of_ring(ring: list[list[float]]) -> list[float]:
    xs = [p[0] for p in ring[:-1]]
    ys = [p[1] for p in ring[:-1]]
    return [min(xs), min(ys), max(xs), max(ys)]


def _building_height(district: str, core_r: float, rng: random.Random) -> int:
    if district == "imperial_core":
        return 30 + int((1 - core_r) * 48) + rng.randint(0, 15)
    if district == "cbd":
        return 22 + int((1 - core_r) * 44) + rng.randint(0, 13)
    if district == "inner_mixed":
        return 10 + int((1 - core_r) * 22) + rng.randint(0, 8)
    if district in {"inner_residential", "campus", "entertainment"}:
        return 6 + int((1 - core_r) * 12) + rng.randint(0, 6)
    if district in {"outer_residential", "peri_urban_mixed", "peri_residential"}:
        return 2 + rng.randint(0, 8)
    if district in {"industrial", "logistics", "airport"}:
        return 1 + rng.randint(0, 5)
    return 3 + rng.randint(0, 7)


def _shape_variant(parcel_ring: list[list[float]], district: str, rng: random.Random) -> list[list[float]]:
    if district in {"cbd", "imperial_core", "inner_mixed", "industrial"} and rng.random() < 0.27:
        b = _bbox_of_ring(parcel_ring)
        x0, y0, x1, y1 = b
        cutx = x0 + (x1 - x0) * (0.55 + rng.random() * 0.25)
        cuty = y0 + (y1 - y0) * (0.3 + rng.random() * 0.35)
        ring = [
            [x0, y0],
            [x1, y0],
            [x1, cuty],
            [cutx, cuty],
            [cutx, y1],
            [x0, y1],
            [x0, y0],
        ]
        return ring
    return parcel_ring


def generate_buildings_index(layout: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(int(cfg["build"]["seed"]) + 3107)
    bbox = cfg["map"]["bbox"]
    min_x, min_y, max_x, max_y = bbox
    mw = layout["metro_scale"]["w"]
    mh = layout["metro_scale"]["h"]
    cx, cy = layout["center"]

    cell_size = float(cfg["build"]["building_cell_size_deg"])

    blocks = generate_blocks(layout, cfg)
    buildings: list[dict[str, Any]] = []
    district_counts: dict[str, int] = {}

    for block in blocks:
        parcels = subdivide_block(block, rng)
        for parcel in parcels:
            ring = _shape_variant(parcel["polygon"], parcel["district"], rng)
            bx = _bbox_of_ring(ring)
            px, py = _centroid(ring)
            core_r = math.sqrt(((px - cx) / max(1e-9, mw * 0.4)) ** 2 + ((py - cy) / max(1e-9, mh * 0.4)) ** 2)
            floors = _building_height(parcel["district"], min(1.0, core_r), rng)
            buildings.append({"b": bx, "f": floors, "p": [ring]})
            district_counts[parcel["district"]] = district_counts.get(parcel["district"], 0) + 1

    cells_map: dict[tuple[int, int], list[int]] = {}
    for i, b in enumerate(buildings):
        x = (b["b"][0] + b["b"][2]) / 2
        y = (b["b"][1] + b["b"][3]) / 2
        ix = int((x - min_x) / max(1e-9, cell_size))
        iy = int((y - min_y) / max(1e-9, cell_size))
        cells_map.setdefault((ix, iy), []).append(i)

    max_ix = max((k[0] for k in cells_map.keys()), default=0) + 1
    max_iy = max((k[1] for k in cells_map.keys()), default=0) + 1
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

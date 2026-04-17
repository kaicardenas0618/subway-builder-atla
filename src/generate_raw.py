from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Any

from .utils import write_json


def _linspace(start: float, end: float, steps: int) -> list[float]:
    if steps <= 1:
        return [start]
    gap = (end - start) / (steps - 1)
    return [start + i * gap for i in range(steps)]


def _rect_ring(min_x: float, min_y: float, max_x: float, max_y: float) -> list[list[float]]:
    return [
        [min_x, min_y],
        [max_x, min_y],
        [max_x, max_y],
        [min_x, max_y],
        [min_x, min_y],
    ]


def generate_roads(cfg: dict[str, Any], out_path: Path) -> dict[str, Any]:
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]
    spacing = float(cfg["build"]["road_spacing_deg"])
    major_every = int(cfg["build"]["road_major_every"])

    features: list[dict[str, Any]] = []

    x_vals = []
    x = min_x
    while x <= max_x + 1e-9:
        x_vals.append(x)
        x += spacing

    y_vals = []
    y = min_y
    while y <= max_y + 1e-9:
        y_vals.append(y)
        y += spacing

    for i, xv in enumerate(x_vals):
        cls = "major" if i % major_every == 0 else "minor"
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "roadClass": cls,
                    "structure": "normal",
                    "name": f"{cls.title()} Ave {i + 1}",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[xv, min_y], [xv, max_y]],
                },
            }
        )

    for i, yv in enumerate(y_vals):
        cls = "major" if i % major_every == 0 else "minor"
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "roadClass": cls,
                    "structure": "normal",
                    "name": f"{cls.title()} St {i + 1}",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[min_x, yv], [max_x, yv]],
                },
            }
        )

    geo = {"type": "FeatureCollection", "features": features}
    write_json(out_path, geo)
    return geo


def generate_runways(cfg: dict[str, Any], out_path: Path) -> dict[str, Any]:
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]
    count = int(cfg["build"]["runways"])

    width = (max_x - min_x) * 0.07
    height = (max_y - min_y) * 0.02

    features: list[dict[str, Any]] = []
    for i in range(count):
        frac = (i + 1) / (count + 1)
        cx = min_x + (max_x - min_x) * frac
        cy = min_y + (max_y - min_y) * (0.14 + 0.04 * i)
        ring = _rect_ring(cx - width / 2, cy - height / 2, cx + width / 2, cy + height / 2)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "roadType": "runway",
                    "z_order": 0,
                    "osm_way_id": f"fictional-runway-{i + 1}",
                    "area": 0,
                },
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )

    geo = {"type": "FeatureCollection", "features": features}
    write_json(out_path, geo)
    return geo


def generate_buildings_index(cfg: dict[str, Any], out_path: Path) -> dict[str, Any]:
    rng = random.Random(int(cfg["build"]["seed"]))
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]

    rows = int(cfg["build"]["building_rows"])
    cols = int(cfg["build"]["building_cols"])
    size_factor = float(cfg["build"]["building_size_factor"])
    cell_size = float(cfg["build"]["building_cell_size_deg"])

    center_min_x = min_x + (max_x - min_x) * 0.22
    center_max_x = max_x - (max_x - min_x) * 0.22
    center_min_y = min_y + (max_y - min_y) * 0.22
    center_max_y = max_y - (max_y - min_y) * 0.22

    xs = _linspace(center_min_x, center_max_x, cols)
    ys = _linspace(center_min_y, center_max_y, rows)

    buildings: list[dict[str, Any]] = []
    cells_map: dict[tuple[int, int], list[int]] = {}

    for r, y in enumerate(ys):
        for c, x in enumerate(xs):
            jitter_x = (rng.random() - 0.5) * (max_x - min_x) * 0.0008
            jitter_y = (rng.random() - 0.5) * (max_y - min_y) * 0.0008
            lot_w = ((max_x - min_x) / (cols * 2.2)) * size_factor
            lot_h = ((max_y - min_y) / (rows * 2.2)) * size_factor

            bx0 = x - lot_w / 2 + jitter_x
            by0 = y - lot_h / 2 + jitter_y
            bx1 = x + lot_w / 2 + jitter_x
            by1 = y + lot_h / 2 + jitter_y

            ring = _rect_ring(bx0, by0, bx1, by1)
            floors = 2 + int(8 * math.exp(-(((r - rows / 2) ** 2 + (c - cols / 2) ** 2) / (rows * cols * 0.07))))
            building_index = len(buildings)
            buildings.append({"b": [bx0, by0, bx1, by1], "f": floors, "p": [ring]})

            cell_x = int((x - min_x) / cell_size)
            cell_y = int((y - min_y) / cell_size)
            cells_map.setdefault((cell_x, cell_y), []).append(building_index)

    max_cell_x = max(ix for ix, _ in cells_map.keys()) + 1 if cells_map else 0
    max_cell_y = max(iy for _, iy in cells_map.keys()) + 1 if cells_map else 0
    cells = [[ix, iy, *idxs] for (ix, iy), idxs in sorted(cells_map.items())]

    shape = {
        "cs": cell_size,
        "bbox": [min_x, min_y, max_x, max_y],
        "grid": [max_cell_x, max_cell_y],
        "cells": cells,
        "buildings": buildings,
        "stats": {
            "count": len(buildings),
            "maxDepth": max((len(c) - 2 for c in cells), default=0),
        },
    }

    write_json(out_path, shape)
    return shape


def generate_demand_data(cfg: dict[str, Any], buildings_index: dict[str, Any], out_path: Path) -> dict[str, Any]:
    rng = random.Random(int(cfg["build"]["seed"]) + 99)
    demand_points = int(cfg["build"]["demand_points"])
    links_per_point = int(cfg["build"]["pop_links_per_point"])

    buildings = buildings_index["buildings"]
    picks = [buildings[i * max(1, len(buildings) // demand_points)] for i in range(demand_points)]

    points: list[dict[str, Any]] = []
    pops: list[dict[str, Any]] = []

    pop_counter = 0
    for i, b in enumerate(picks):
        bx0, by0, bx1, by1 = b["b"]
        cx = (bx0 + bx1) / 2
        cy = (by0 + by1) / 2
        pid = f"merged_job_{i:04d}"
        pop_ids: list[str] = []

        jobs = 800 + rng.randint(0, 4500)
        residents = 40 + rng.randint(0, 300)

        for j in range(links_per_point):
            size = 12 + rng.randint(0, 160)
            seconds = 180 + rng.randint(0, 3600)
            distance = int(seconds * (7.5 + rng.random() * 7))
            pop_id = f"agg_{i}_{j}_{pop_counter}"
            pop_ids.append(pop_id)
            pops.append(
                {
                    "residenceId": f"merged_res_{i}_{j}",
                    "jobId": pid,
                    "drivingSeconds": seconds,
                    "drivingDistance": distance,
                    "size": size,
                    "id": pop_id,
                }
            )
            pop_counter += 1

        points.append(
            {
                "id": pid,
                "location": [cx, cy],
                "jobs": jobs,
                "residents": residents,
                "popIds": pop_ids,
            }
        )

    shape = {"points": points, "pops": pops}
    write_json(out_path, shape)
    return shape

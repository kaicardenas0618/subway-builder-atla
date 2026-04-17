from __future__ import annotations

import json
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


def _polygon_centroid(ring: list[list[float]]) -> tuple[float, float]:
    x = sum(pt[0] for pt in ring[:-1]) / max(1, len(ring) - 1)
    y = sum(pt[1] for pt in ring[:-1]) / max(1, len(ring) - 1)
    return x, y


def _district_at(x: float, y: float, bbox: list[float]) -> str:
    min_x, min_y, max_x, max_y = bbox
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    w = max_x - min_x
    h = max_y - min_y
    nx = (x - cx) / max(1e-9, w)
    ny = (y - cy) / max(1e-9, h)
    r = math.sqrt((nx * 1.25) ** 2 + (ny * 1.05) ** 2)

    if x > max_x - 0.18 * w and y < min_y + 0.25 * h:
        return "airport"
    if x < min_x + 0.22 * w and y < min_y + 0.30 * h:
        return "industrial"
    if x > max_x - 0.24 * w and y > max_y - 0.22 * h:
        return "university"
    if x < min_x + 0.22 * w and y > max_y - 0.22 * h:
        return "entertainment"
    if r < 0.11:
        return "cbd"
    if r < 0.23:
        return "inner_mixed"
    if r < 0.34:
        return "inner_residential"
    return "outer_residential"


def _create_irregular_line(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    waviness: float,
    steps: int,
) -> list[list[float]]:
    coords: list[list[float]] = []
    dx = x1 - x0
    dy = y1 - y0
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-12:
        return [[x0, y0], [x1, y1]]
    px = -dy / length
    py = dx / length
    for i in range(steps + 1):
        t = i / steps
        wx = x0 + dx * t
        wy = y0 + dy * t
        bend = math.sin(t * math.pi * 2) * waviness + math.sin(t * math.pi * 5) * waviness * 0.35
        coords.append([wx + px * bend, wy + py * bend])
    return coords


def generate_roads(cfg: dict[str, Any], out_path: Path) -> dict[str, Any]:
    rng = random.Random(int(cfg["build"]["seed"]) + 700)
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]
    spacing = float(cfg["build"]["road_spacing_deg"])
    major_every = int(cfg["build"]["road_major_every"])

    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    w = max_x - min_x
    h = max_y - min_y

    features: list[dict[str, Any]] = []

    # Ring roads around the city core.
    for ring_idx, frac in enumerate([0.13, 0.22, 0.32]):
        pts: list[list[float]] = []
        for k in range(0, 96):
            t = k / 96 * math.pi * 2
            rx = w * frac * (1.0 + 0.08 * math.sin(3 * t))
            ry = h * frac * (1.0 + 0.10 * math.cos(2 * t))
            pts.append([cx + rx * math.cos(t), cy + ry * math.sin(t)])
        pts.append(pts[0])
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "roadClass": "trunk" if ring_idx == 0 else "major",
                    "structure": "normal",
                    "name": f"Ring Road {ring_idx + 1}",
                },
                "geometry": {"type": "LineString", "coordinates": pts},
            }
        )

    # Radial arterials and offset diagonals.
    for i in range(12):
        ang = (math.pi * 2 / 12) * i + (0.04 if i % 2 == 0 else -0.03)
        x0 = cx - math.cos(ang) * w * 0.52
        y0 = cy - math.sin(ang) * h * 0.52
        x1 = cx + math.cos(ang) * w * 0.52
        y1 = cy + math.sin(ang) * h * 0.52
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "roadClass": "trunk" if i % 3 == 0 else "major",
                    "structure": "elevated" if i % 6 == 0 else "normal",
                    "name": f"Arterial Spine {i + 1}",
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": _create_irregular_line(x0, y0, x1, y1, waviness=min(w, h) * 0.01, steps=24),
                },
            }
        )

    # District-scale local fabrics with partial/faulted grids.
    y = min_y
    row = 0
    while y <= max_y + 1e-9:
        x = min_x
        col = 0
        while x <= max_x + 1e-9:
            district = _district_at(x, y, cfg["map"]["bbox"])
            if district in {"airport", "industrial"}:
                cell_spacing = spacing * 1.7
                angle = 0.09
            elif district == "cbd":
                cell_spacing = spacing * 0.55
                angle = 0.26
            elif district == "inner_mixed":
                cell_spacing = spacing * 0.75
                angle = -0.15
            elif district == "inner_residential":
                cell_spacing = spacing * 0.95
                angle = 0.08
            else:
                cell_spacing = spacing * 1.2
                angle = -0.05

            if rng.random() < (0.11 if district != "cbd" else 0.05):
                x += cell_spacing
                col += 1
                continue

            dx = math.cos(angle) * cell_spacing * 0.95
            dy = math.sin(angle) * cell_spacing * 0.95

            if row % major_every == 0:
                road_class = "major"
            elif district == "cbd":
                road_class = "minor"
            else:
                road_class = "local"

            features.append(
                {
                    "type": "Feature",
                    "properties": {
                        "roadClass": road_class,
                        "structure": "normal",
                        "name": f"{district.replace('_', ' ').title()} Street {row}-{col}",
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[x - dx, y - dy], [x + dx, y + dy]],
                    },
                }
            )

            if rng.random() < 0.17:
                diag_angle = angle + math.pi / 3.2
                ddx = math.cos(diag_angle) * cell_spacing * 0.82
                ddy = math.sin(diag_angle) * cell_spacing * 0.82
                features.append(
                    {
                        "type": "Feature",
                        "properties": {
                            "roadClass": "minor" if district in {"cbd", "inner_mixed"} else "local",
                            "structure": "normal",
                            "name": f"Diagonal Link {row}-{col}",
                        },
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[x - ddx, y - ddy], [x + ddx, y + ddy]],
                        },
                    }
                )

            x += cell_spacing
            col += 1
        y += spacing
        row += 1

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
                    "osm_way_id": f"ba-sing-se-runway-{i + 1}",
                    "area": 0,
                },
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )

    geo = {"type": "FeatureCollection", "features": features}
    write_json(out_path, geo)
    return geo


def generate_context_layers(cfg: dict[str, Any], output_dir: Path) -> None:
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]
    w = max_x - min_x
    h = max_y - min_y

    water_ring = [
        [min_x + 0.02 * w, min_y + 0.52 * h],
        [min_x + 0.26 * w, min_y + 0.62 * h],
        [min_x + 0.72 * w, min_y + 0.57 * h],
        [max_x - 0.01 * w, min_y + 0.63 * h],
        [max_x - 0.01 * w, min_y + 0.67 * h],
        [min_x + 0.71 * w, min_y + 0.61 * h],
        [min_x + 0.26 * w, min_y + 0.66 * h],
        [min_x + 0.02 * w, min_y + 0.56 * h],
        [min_x + 0.02 * w, min_y + 0.52 * h],
    ]

    park_ring = _rect_ring(min_x + 0.11 * w, min_y + 0.72 * h, min_x + 0.23 * w, min_y + 0.86 * h)

    water = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"kind": "river"},
                "geometry": {"type": "Polygon", "coordinates": [water_ring]},
            }
        ],
    }
    parks = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"kind": "park"},
                "geometry": {"type": "Polygon", "coordinates": [park_ring]},
            }
        ],
    }

    write_json(output_dir / "water.geojson", water)
    write_json(output_dir / "open_space.geojson", parks)


def generate_buildings_index(cfg: dict[str, Any], out_path: Path) -> dict[str, Any]:
    rng = random.Random(int(cfg["build"]["seed"]))
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]

    rows = int(cfg["build"]["building_rows"])
    cols = int(cfg["build"]["building_cols"])
    size_factor = float(cfg["build"]["building_size_factor"])
    cell_size = float(cfg["build"]["building_cell_size_deg"])

    center_min_x = min_x + (max_x - min_x) * 0.08
    center_max_x = max_x - (max_x - min_x) * 0.08
    center_min_y = min_y + (max_y - min_y) * 0.08
    center_max_y = max_y - (max_y - min_y) * 0.08

    xs = _linspace(center_min_x, center_max_x, cols)
    ys = _linspace(center_min_y, center_max_y, rows)

    buildings: list[dict[str, Any]] = []
    cells_map: dict[tuple[int, int], list[int]] = {}

    for r, y in enumerate(ys):
        for c, x in enumerate(xs):
            district = _district_at(x, y, cfg["map"]["bbox"])
            if district == "cbd":
                lot_scale = 1.45
                floor_base = 22
                floor_var = 44
            elif district == "inner_mixed":
                lot_scale = 1.0
                floor_base = 8
                floor_var = 18
            elif district == "inner_residential":
                lot_scale = 0.82
                floor_base = 4
                floor_var = 9
            elif district == "industrial":
                lot_scale = 2.2
                floor_base = 2
                floor_var = 5
            elif district == "airport":
                lot_scale = 2.6
                floor_base = 1
                floor_var = 4
            else:
                lot_scale = 0.76
                floor_base = 3
                floor_var = 8

            jitter_x = (rng.random() - 0.5) * (max_x - min_x) * 0.0012
            jitter_y = (rng.random() - 0.5) * (max_y - min_y) * 0.0012
            lot_w = ((max_x - min_x) / (cols * 2.5)) * size_factor * lot_scale
            lot_h = ((max_y - min_y) / (rows * 2.5)) * size_factor * lot_scale

            bx0 = x - lot_w / 2 + jitter_x
            by0 = y - lot_h / 2 + jitter_y
            bx1 = x + lot_w / 2 + jitter_x
            by1 = y + lot_h / 2 + jitter_y

            if rng.random() < 0.28 and district in {"cbd", "inner_mixed", "industrial"}:
                cut = 0.22 + rng.random() * 0.26
                ring = [
                    [bx0, by0],
                    [bx1, by0],
                    [bx1, by0 + (by1 - by0) * cut],
                    [bx0 + (bx1 - bx0) * 0.68, by0 + (by1 - by0) * cut],
                    [bx0 + (bx1 - bx0) * 0.68, by1],
                    [bx0, by1],
                    [bx0, by0],
                ]
            else:
                ring = _rect_ring(bx0, by0, bx1, by1)

            center_weight = math.exp(-(((r - rows / 2) ** 2 + (c - cols / 2) ** 2) / (rows * cols * 0.04)))
            floors = floor_base + int(floor_var * center_weight) + rng.randint(0, max(1, floor_var // 5))
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


def _estimate_travel(home: tuple[float, float], work: tuple[float, float]) -> tuple[int, int]:
    lon1, lat1 = home
    lon2, lat2 = work
    dx = (lon2 - lon1) * 111_000 * math.cos(math.radians((lat1 + lat2) / 2))
    dy = (lat2 - lat1) * 111_000
    distance = int(max(400, math.sqrt(dx * dx + dy * dy) * 1.25))
    speed_mps = 9.0
    seconds = int(max(180, distance / speed_mps))
    return seconds, distance


def _sample_job_points(
    rng: random.Random,
    home_loc: tuple[float, float],
    job_points: list[dict[str, Any]],
    picks: int,
) -> list[dict[str, Any]]:
    weighted: list[tuple[float, dict[str, Any]]] = []
    for p in job_points:
        jx, jy = p["location"]
        dx = jx - home_loc[0]
        dy = jy - home_loc[1]
        dist = math.sqrt(dx * dx + dy * dy)
        attractiveness = p["jobs"] / max(0.0025, dist ** 1.25)
        weighted.append((max(1e-6, attractiveness), p))

    chosen: list[dict[str, Any]] = []
    pool = weighted[:]
    for _ in range(min(picks, len(pool))):
        total = sum(w for w, _ in pool)
        t = rng.random() * total
        c = 0.0
        idx = 0
        for i, (w, _) in enumerate(pool):
            c += w
            if c >= t:
                idx = i
                break
        _, pick = pool.pop(idx)
        chosen.append(pick)
    return chosen


def generate_demand_data(cfg: dict[str, Any], buildings_index: dict[str, Any], out_path: Path) -> dict[str, Any]:
    rng = random.Random(int(cfg["build"]["seed"]) + 99)
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]
    w = max_x - min_x
    h = max_y - min_y

    target_population = int(cfg["build"]["target_population"])
    max_pop_size = int(cfg["build"].get("max_pop_size", 220))
    commute_share = float(cfg["build"].get("commute_share", 0.8))

    district_fabric = {
        "cbd": {"cell": min(w, h) * 0.010, "job_bias": 1.85, "res_bias": 0.45},
        "inner_mixed": {"cell": min(w, h) * 0.014, "job_bias": 1.2, "res_bias": 1.0},
        "inner_residential": {"cell": min(w, h) * 0.018, "job_bias": 0.85, "res_bias": 1.4},
        "outer_residential": {"cell": min(w, h) * 0.024, "job_bias": 0.6, "res_bias": 1.3},
        "industrial": {"cell": min(w, h) * 0.020, "job_bias": 1.5, "res_bias": 0.4},
        "airport": {"cell": min(w, h) * 0.022, "job_bias": 1.65, "res_bias": 0.35},
        "university": {"cell": min(w, h) * 0.014, "job_bias": 1.1, "res_bias": 1.1},
        "entertainment": {"cell": min(w, h) * 0.016, "job_bias": 1.0, "res_bias": 0.9},
    }

    cluster: dict[tuple[str, int, int], dict[str, Any]] = {}
    for b in buildings_index["buildings"]:
        ring = b["p"][0]
        cx, cy = _polygon_centroid(ring)
        district = _district_at(cx, cy, cfg["map"]["bbox"])
        params = district_fabric[district]
        cell = max(1e-8, params["cell"])
        ix = int((cx - min_x) / cell)
        iy = int((cy - min_y) / cell)
        key = (district, ix, iy)

        area = max(1e-10, (b["b"][2] - b["b"][0]) * (b["b"][3] - b["b"][1]))
        intensity = area * max(1.0, b["f"])
        e = cluster.setdefault(
            key,
            {
                "district": district,
                "sum_x": 0.0,
                "sum_y": 0.0,
                "sum_w": 0.0,
                "intensity": 0.0,
            },
        )
        e["sum_x"] += cx * intensity
        e["sum_y"] += cy * intensity
        e["sum_w"] += intensity
        e["intensity"] += intensity

    points: list[dict[str, Any]] = []
    for i, (_, c) in enumerate(sorted(cluster.items(), key=lambda kv: kv[1]["intensity"], reverse=True)):
        if c["sum_w"] <= 0:
            continue
        district = c["district"]
        params = district_fabric[district]
        px = c["sum_x"] / c["sum_w"]
        py = c["sum_y"] / c["sum_w"]

        jobs = int(max(10, c["intensity"] * params["job_bias"] * 3100))
        residents = int(max(10, c["intensity"] * params["res_bias"] * 2900))
        points.append(
            {
                "id": f"merged_dp_{i:05d}",
                "location": [px, py],
                "jobs": jobs,
                "residents": residents,
                "popIds": [],
            }
        )

    if not points:
        shape = {"points": [], "pops": []}
        write_json(out_path, shape)
        return shape

    # Scale residents toward configured represented population target.
    current_res = sum(p["residents"] for p in points)
    scale = target_population / max(1, current_res)
    for p in points:
        p["residents"] = int(max(1, round(p["residents"] * scale)))
        p["jobs"] = int(max(1, round(p["jobs"] * scale * 0.95)))

    points_by_id = {p["id"]: p for p in points}
    pops: list[dict[str, Any]] = []
    pop_counter = 0

    for home in points:
        home_loc = (home["location"][0], home["location"][1])
        commuters = int(home["residents"] * commute_share)
        if commuters <= 0:
            continue

        link_count = min(14, max(3, commuters // max_pop_size))
        job_candidates = _sample_job_points(rng, home_loc, points, picks=link_count)
        if not job_candidates:
            continue

        raw = [max(1.0, j["jobs"]) for j in job_candidates]
        s = sum(raw)
        assigned_total = 0
        for idx, job in enumerate(job_candidates):
            if idx == len(job_candidates) - 1:
                cohort = commuters - assigned_total
            else:
                cohort = int(commuters * raw[idx] / s)
                assigned_total += cohort
            cohort = max(1, cohort)

            remaining = cohort
            while remaining > 0:
                size = min(max_pop_size, remaining)
                remaining -= size
                secs, dist = _estimate_travel(home_loc, (job["location"][0], job["location"][1]))
                pop_id = f"agg_{pop_counter:07d}"
                pop_counter += 1
                pop = {
                    "residenceId": home["id"],
                    "jobId": job["id"],
                    "drivingSeconds": secs,
                    "drivingDistance": dist,
                    "size": size,
                    "id": pop_id,
                }
                pops.append(pop)
                points_by_id[home["id"]]["popIds"].append(pop_id)
                if job["id"] != home["id"]:
                    points_by_id[job["id"]]["popIds"].append(pop_id)

    # Deduplicate point pop references while preserving order.
    for p in points:
        seen: set[str] = set()
        uniq: list[str] = []
        for pid in p["popIds"]:
            if pid not in seen:
                uniq.append(pid)
                seen.add(pid)
        p["popIds"] = uniq

    shape = {"points": points, "pops": pops}
    write_json(out_path, shape)
    return shape

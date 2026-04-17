from __future__ import annotations

import math
import random
from typing import Any

from .districts import classify_district, BUILDABLE_DISTRICTS

DISTRICT_BLOCK_PARAMS: dict[str, dict[str, Any]] = {
    "imperial_core":    {"spacing": 0.004, "size": (0.0015, 0.004), "irreg": 0.35, "density": 1.6},
    "cbd":              {"spacing": 0.003, "size": (0.0012, 0.0035), "irreg": 0.15, "density": 2.0},
    "subcenter":        {"spacing": 0.004, "size": (0.0015, 0.0045), "irreg": 0.20, "density": 1.7},
    "inner_mixed":      {"spacing": 0.005, "size": (0.002, 0.006), "irreg": 0.30, "density": 1.3},
    "inner_residential":{"spacing": 0.006, "size": (0.003, 0.007), "irreg": 0.25, "density": 1.1},
    "outer_residential":{"spacing": 0.008, "size": (0.004, 0.010), "irreg": 0.20, "density": 0.85},
    "peri_urban_mixed": {"spacing": 0.012, "size": (0.005, 0.014), "irreg": 0.25, "density": 0.6},
    "peri_residential": {"spacing": 0.014, "size": (0.006, 0.016), "irreg": 0.30, "density": 0.5},
    "industrial":       {"spacing": 0.016, "size": (0.010, 0.025), "irreg": 0.12, "density": 0.4},
    "logistics":        {"spacing": 0.018, "size": (0.012, 0.028), "irreg": 0.10, "density": 0.35},
    "entertainment":    {"spacing": 0.007, "size": (0.004, 0.010), "irreg": 0.22, "density": 0.8},
    "campus":           {"spacing": 0.008, "size": (0.005, 0.012), "irreg": 0.18, "density": 0.6},
    "airport":          {"spacing": 0.020, "size": (0.010, 0.030), "irreg": 0.08, "density": 0.2},
}

DEFAULT_PARAMS = {"spacing": 0.010, "size": (0.005, 0.012), "irreg": 0.20, "density": 0.5}

def _block_polygon(cx: float, cy: float, hw: float, hh: float,
                   angle: float, irreg: float, rng: random.Random) -> list[list[float]]:
    corners = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    ca, sa = math.cos(angle), math.sin(angle)
    ring: list[list[float]] = []
    for sx, sy in corners:
        dx = sx * hw * (1 + (rng.random() - 0.5) * irreg)
        dy = sy * hh * (1 + (rng.random() - 0.5) * irreg)
        rx = cx + dx * ca - dy * sa
        ry = cy + dx * sa + dy * ca
        ring.append([rx, ry])
    ring.append(ring[0])
    return ring

def generate_blocks(plan: dict[str, Any], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    rng = random.Random(int(cfg["build"]["seed"]) + 2203)
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]
    w = max_x - min_x
    h = max_y - min_y

    target_buildings = int(cfg["build"]["building_rows"] * cfg["build"]["building_cols"])
    avg_buildings_per_block = 5
    target_blocks = int(target_buildings / avg_buildings_per_block)

    blocks: list[dict[str, Any]] = []

    fine_step = 0.003
    nx_cells = max(1, int(w / fine_step))
    ny_cells = max(1, int(h / fine_step))
    step_x = w / nx_cells
    step_y = h / ny_cells

    for ix in range(nx_cells):
        for iy in range(ny_cells):
            cell_cx = min_x + (ix + 0.5) * step_x
            cell_cy = min_y + (iy + 0.5) * step_y

            district = classify_district(cell_cx, cell_cy, plan)
            if district not in BUILDABLE_DISTRICTS:
                continue

            params = DISTRICT_BLOCK_PARAMS.get(district, DEFAULT_PARAMS)

            if rng.random() > params["density"]:
                continue

            jx = (rng.random() - 0.5) * step_x * 0.8
            jy = (rng.random() - 0.5) * step_y * 0.8
            bcx = cell_cx + jx
            bcy = cell_cy + jy

            s0, s1 = params["size"]
            bw = s0 + rng.random() * (s1 - s0)
            bh = s0 + rng.random() * (s1 - s0)
            angle = (rng.random() - 0.5) * 0.5 if district != "cbd" else (rng.random() - 0.5) * 0.15
            irreg = params["irreg"]

            poly = _block_polygon(bcx, bcy, bw / 2, bh / 2, angle, irreg, rng)

            blocks.append({
                "center": [bcx, bcy],
                "width": bw,
                "height": bh,
                "angle": angle,
                "district": district,
                "polygon": poly,
            })

    if len(blocks) > target_blocks * 1.5:
        rng.shuffle(blocks)
        blocks = blocks[:int(target_blocks * 1.2)]

    return blocks

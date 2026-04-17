from __future__ import annotations

import math
import random
from typing import Any

from .districts import classify_district


DISTRICT_BLOCK_PARAMS = {
    "imperial_core": {"count_weight": 1.2, "size": (0.003, 0.008), "angle_jitter": 0.4},
    "cbd": {"count_weight": 1.5, "size": (0.0025, 0.007), "angle_jitter": 0.35},
    "inner_mixed": {"count_weight": 1.25, "size": (0.003, 0.009), "angle_jitter": 0.5},
    "inner_residential": {"count_weight": 1.1, "size": (0.0035, 0.010), "angle_jitter": 0.6},
    "outer_residential": {"count_weight": 0.9, "size": (0.004, 0.013), "angle_jitter": 0.8},
    "peri_urban_mixed": {"count_weight": 0.75, "size": (0.005, 0.015), "angle_jitter": 0.9},
    "peri_residential": {"count_weight": 0.68, "size": (0.0055, 0.016), "angle_jitter": 1.0},
    "industrial": {"count_weight": 0.5, "size": (0.010, 0.028), "angle_jitter": 0.45},
    "logistics": {"count_weight": 0.45, "size": (0.012, 0.032), "angle_jitter": 0.35},
    "airport": {"count_weight": 0.18, "size": (0.015, 0.040), "angle_jitter": 0.25},
    "campus": {"count_weight": 0.55, "size": (0.007, 0.016), "angle_jitter": 0.55},
    "entertainment": {"count_weight": 0.7, "size": (0.006, 0.017), "angle_jitter": 0.55},
}


def generate_blocks(layout: dict[str, Any], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    rng = random.Random(int(cfg["build"]["seed"]) + 2203)
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]
    w = max_x - min_x
    h = max_y - min_y

    desired = int(cfg["build"]["building_rows"] * cfg["build"]["building_cols"] * 0.62)
    blocks: list[dict[str, Any]] = []

    # Rejection sampling by district weights; no global row/col lattice.
    max_iter = desired * 30
    it = 0
    while len(blocks) < desired and it < max_iter:
        it += 1
        x = min_x + rng.random() * w
        y = min_y + rng.random() * h
        district = classify_district(x, y, layout)
        if district == "water":
            continue
        p = DISTRICT_BLOCK_PARAMS.get(district, DISTRICT_BLOCK_PARAMS["outer_residential"])
        if rng.random() > min(1.0, p["count_weight"]):
            continue

        s0, s1 = p["size"]
        bw = w * (s0 + rng.random() * (s1 - s0))
        bh = h * (s0 + rng.random() * (s1 - s0))
        angle = rng.random() * p["angle_jitter"] - p["angle_jitter"] / 2

        blocks.append({
            "center": [x, y],
            "width": bw,
            "height": bh,
            "angle": angle,
            "district": district,
        })

    return blocks

from __future__ import annotations

import math
import random
from typing import Any

def _rotate(x: float, y: float, cx: float, cy: float, a: float) -> tuple[float, float]:
    ca, sa = math.cos(a), math.sin(a)
    return cx + x * ca - y * sa, cy + x * sa + y * ca

def _rect_poly(cx: float, cy: float, w: float, h: float, a: float) -> list[list[float]]:
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    ring = [[_rotate(x, y, cx, cy, a)[0], _rotate(x, y, cx, cy, a)[1]] for x, y in pts]
    ring.append(ring[0])
    return ring

SUBDIV = {
    "imperial_core":     ((2, 5), (2, 4)),
    "cbd":               ((3, 7), (2, 6)),
    "subcenter":         ((2, 5), (2, 5)),
    "inner_mixed":       ((2, 5), (2, 4)),
    "inner_residential": ((2, 4), (2, 4)),
    "outer_residential": ((1, 3), (1, 3)),
    "peri_urban_mixed":  ((1, 3), (1, 2)),
    "peri_residential":  ((1, 2), (1, 2)),
    "industrial":        ((1, 2), (1, 2)),
    "logistics":         ((1, 2), (1, 2)),
    "entertainment":     ((2, 4), (2, 3)),
    "campus":            ((2, 4), (2, 3)),
    "airport":           ((1, 2), (1, 2)),
}

def subdivide_block(block: dict[str, Any], rng: random.Random) -> list[dict[str, Any]]:
    cx, cy = block["center"]
    bw, bh = block["width"], block["height"]
    a = block["angle"]
    district = block["district"]

    nx_range, ny_range = SUBDIV.get(district, ((1, 3), (1, 3)))
    nx = rng.randint(*nx_range)
    ny = rng.randint(*ny_range)

    parcels: list[dict[str, Any]] = []
    for ix in range(nx):
        for iy in range(ny):
            skip_chance = 0.05 if district in ("cbd", "imperial_core") else 0.12
            if rng.random() < skip_chance:
                continue

            fx = (ix + 0.5) / nx - 0.5
            fy = (iy + 0.5) / ny - 0.5
            local_x = fx * bw * 0.88
            local_y = fy * bh * 0.88

            pw = bw / nx * (0.75 + rng.random() * 0.20)
            ph = bh / ny * (0.75 + rng.random() * 0.20)

            setback = 0.85 + rng.random() * 0.12
            pw *= setback
            ph *= setback

            px, py = _rotate(local_x, local_y, cx, cy, a)
            pa = a + (rng.random() - 0.5) * 0.08

            poly = _rect_poly(px, py, pw, ph, pa)
            parcels.append({
                "center": [px, py],
                "width": pw,
                "height": ph,
                "angle": pa,
                "district": district,
                "polygon": poly,
            })
    return parcels

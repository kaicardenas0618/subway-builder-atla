from __future__ import annotations

import math
import random
from typing import Any


def _rotate(x: float, y: float, cx: float, cy: float, a: float) -> tuple[float, float]:
    ca = math.cos(a)
    sa = math.sin(a)
    rx = cx + x * ca - y * sa
    ry = cy + x * sa + y * ca
    return rx, ry


def _rect_poly(cx: float, cy: float, w: float, h: float, a: float) -> list[list[float]]:
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    ring = []
    for x, y in pts:
        rx, ry = _rotate(x, y, cx, cy, a)
        ring.append([rx, ry])
    ring.append(ring[0])
    return ring


def subdivide_block(block: dict[str, Any], rng: random.Random) -> list[dict[str, Any]]:
    cx, cy = block["center"]
    bw = block["width"]
    bh = block["height"]
    a = block["angle"]
    district = block["district"]

    if district in {"industrial", "logistics", "airport"}:
        nx = 1 + int(rng.random() * 2)
        ny = 1 + int(rng.random() * 2)
    elif district in {"cbd", "imperial_core", "inner_mixed"}:
        nx = 2 + int(rng.random() * 4)
        ny = 2 + int(rng.random() * 4)
    elif district in {"campus", "entertainment"}:
        nx = 2 + int(rng.random() * 3)
        ny = 2 + int(rng.random() * 3)
    else:
        nx = 2 + int(rng.random() * 3)
        ny = 1 + int(rng.random() * 3)

    parcels: list[dict[str, Any]] = []
    for ix in range(nx):
        for iy in range(ny):
            if rng.random() < 0.08 and district not in {"cbd", "imperial_core"}:
                continue
            fx = (ix + 0.5) / nx - 0.5
            fy = (iy + 0.5) / ny - 0.5
            local_cx = fx * bw * 0.92
            local_cy = fy * bh * 0.92
            pw = bw / nx * (0.72 + rng.random() * 0.35)
            ph = bh / ny * (0.72 + rng.random() * 0.35)
            px, py = _rotate(local_cx, local_cy, cx, cy, a)
            parcels.append(
                {
                    "center": [px, py],
                    "width": pw,
                    "height": ph,
                    "angle": a + (rng.random() - 0.5) * 0.14,
                    "district": district,
                    "polygon": _rect_poly(px, py, pw, ph, a + (rng.random() - 0.5) * 0.09),
                }
            )
    return parcels

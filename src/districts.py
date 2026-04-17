from __future__ import annotations

import math
from typing import Any


def _norm(x: float, y: float, layout: dict[str, Any]) -> tuple[float, float, float, float, float]:
    cx, cy = layout["center"]
    mw = layout["metro_scale"]["w"]
    mh = layout["metro_scale"]["h"]
    nx = (x - cx) / max(1e-9, mw)
    ny = (y - cy) / max(1e-9, mh)
    r = math.sqrt((nx * 1.2) ** 2 + (ny * 1.05) ** 2)
    ang = math.atan2(ny, nx)
    return nx, ny, r, ang, cx


def classify_district(x: float, y: float, layout: dict[str, Any]) -> str:
    nx, ny, r, ang, _ = _norm(x, y, layout)

    lake = layout["lake"]
    lcx, lcy = lake["center"]
    lrx, lry = lake["rx"], lake["ry"]
    if ((x - lcx) / max(1e-9, lrx)) ** 2 + ((y - lcy) / max(1e-9, lry)) ** 2 <= 1.0:
        return "water"

    for airport_key in ["primary_airport", "secondary_airport"]:
        ax, ay = layout[airport_key]["center"]
        if abs(x - ax) < layout["metro_scale"]["w"] * 0.08 and abs(y - ay) < layout["metro_scale"]["h"] * 0.06:
            return "airport"

    for c in layout["campuses"]:
        cx, cy = c["center"]
        rr = c["radius"]
        if ((x - cx) / max(1e-9, layout["metro_scale"]["w"] * rr)) ** 2 + ((y - cy) / max(1e-9, layout["metro_scale"]["h"] * rr)) ** 2 <= 1.0:
            return "campus"

    sx, sy = layout["sectors"]["industrial"]
    if abs(x - sx) < layout["metro_scale"]["w"] * 0.12 and abs(y - sy) < layout["metro_scale"]["h"] * 0.10:
        return "industrial"

    lx, ly = layout["sectors"]["logistics"]
    if abs(x - lx) < layout["metro_scale"]["w"] * 0.10 and abs(y - ly) < layout["metro_scale"]["h"] * 0.08:
        return "logistics"

    ex, ey = layout["sectors"]["entertainment"]
    if abs(x - ex) < layout["metro_scale"]["w"] * 0.07 and abs(y - ey) < layout["metro_scale"]["h"] * 0.06:
        return "entertainment"

    if r < 0.055:
        return "imperial_core"
    if r < 0.11:
        return "cbd"
    if r < 0.18:
        return "inner_mixed"
    if r < 0.27:
        return "inner_residential"
    if r < 0.39:
        return "outer_residential"

    if abs(math.sin(ang * 2.3)) < 0.18:
        return "peri_urban_mixed"
    return "peri_residential"

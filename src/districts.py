from __future__ import annotations

import math
from typing import Any

def _in_ellipse(x: float, y: float, cx: float, cy: float, rx: float, ry: float) -> bool:
    dx = (x - cx) / max(1e-9, rx)
    dy = (y - cy) / max(1e-9, ry)
    return dx * dx + dy * dy <= 1.0

def _in_rect(x: float, y: float, cx: float, cy: float, hx: float, hy: float) -> bool:
    return abs(x - cx) <= hx and abs(y - cy) <= hy

def classify_district(x: float, y: float, plan: dict[str, Any]) -> str:
    cx, cy = plan["center"]
    mw = plan["metro_scale"]["w"]
    mh = plan["metro_scale"]["h"]

    lake = plan["lake"]
    if _in_ellipse(x, y, *lake["center"], lake["rx"], lake["ry"]):
        return "water"

    for key in ["primary_airport", "secondary_airport"]:
        ap = plan[key]
        if _in_rect(x, y, *ap["center"], ap["size_x"] * 0.6, ap["size_y"] * 0.6):
            return "airport"

    for c in plan["campuses"]:
        cr = c["radius"]
        if _in_ellipse(x, y, *c["center"], mw * cr, mh * cr):
            return "campus"

    for z in plan["industrial_zones"]:
        if _in_ellipse(x, y, *z["center"], z["rx"], z["ry"]):
            return "industrial"

    for z in plan["logistics_zones"]:
        if _in_ellipse(x, y, *z["center"], z["rx"], z["ry"]):
            return "logistics"

    for z in plan["entertainment_zones"]:
        if _in_ellipse(x, y, *z["center"], z["rx"], z["ry"]):
            return "entertainment"

    for p in plan["parks"]:
        if _in_ellipse(x, y, *p["center"], p["rx"], p["ry"]):
            return "park"

    nx = (x - cx) / max(1e-9, mw * 0.5)
    ny = (y - cy) / max(1e-9, mh * 0.5)
    r = math.sqrt(nx * nx + ny * ny)
    ang = math.atan2(ny, nx)

    cbd = plan["cbd_crescent"]
    if _in_ellipse(x, y, *cbd["center"], cbd["rx"], cbd["ry"]):
        return "cbd"

    for sc in plan["secondary_centers"]:
        if _in_ellipse(x, y, *sc["center"], mw * sc["radius"], mh * sc["radius"]):
            return "subcenter"

    rf = plan["ring_radii_frac"]
    if r < rf[0]:
        return "imperial_core"
    if r < rf[1]:
        return "inner_mixed"
    if r < rf[2]:
        return "inner_residential"
    if r < rf[3]:
        return "outer_residential"

    if abs(math.sin(ang * 2.1)) < 0.22:
        return "peri_urban_mixed"
    return "peri_residential"

BUILDABLE_DISTRICTS = frozenset({
    "imperial_core", "cbd", "subcenter", "inner_mixed", "inner_residential",
    "outer_residential", "peri_urban_mixed", "peri_residential",
    "industrial", "logistics", "entertainment", "campus", "airport",
})

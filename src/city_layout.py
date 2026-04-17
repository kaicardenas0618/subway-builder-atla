from __future__ import annotations

from typing import Any


def build_city_layout(cfg: dict[str, Any]) -> dict[str, Any]:
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]

    # Canonical Ba Sing Se metro frame; dev/prod are slices of this same city logic.
    metro_bbox = [112.82, 39.60, 113.66, 40.20]
    mx0, my0, mx1, my1 = metro_bbox
    mcx = (mx0 + mx1) / 2
    mcy = (my0 + my1) / 2
    mw = mx1 - mx0
    mh = my1 - my0

    return {
        "bbox": [min_x, min_y, max_x, max_y],
        "metro_bbox": metro_bbox,
        "center": [mcx, mcy],
        "metro_scale": {"w": mw, "h": mh},
        "ring_radii": [0.07, 0.13, 0.21, 0.30],
        "lake": {
            "center": [mcx + 0.26 * mw, mcy + 0.16 * mh],
            "rx": 0.13 * mw,
            "ry": 0.10 * mh,
        },
        "primary_airport": {
            "name": "Upper Ring International",
            "center": [mcx + 0.23 * mw, mcy - 0.20 * mh],
            "angle": -0.44,
        },
        "secondary_airport": {
            "name": "West Wall Regional",
            "center": [mcx - 0.24 * mw, mcy - 0.13 * mh],
            "angle": 0.31,
        },
        "campuses": [
            {"name": "Royal University", "center": [mcx + 0.08 * mw, mcy + 0.12 * mh], "radius": 0.028},
            {"name": "Eastern Academy", "center": [mcx + 0.20 * mw, mcy + 0.03 * mh], "radius": 0.021},
            {"name": "Wall District Institute", "center": [mcx - 0.12 * mw, mcy + 0.08 * mh], "radius": 0.022},
        ],
        "civic": [
            {"name": "Imperial Green", "center": [mcx - 0.01 * mw, mcy + 0.01 * mh], "radius": 0.03},
            {"name": "Outer Promenade", "center": [mcx - 0.18 * mw, mcy + 0.18 * mh], "radius": 0.026},
            {"name": "Canal Garden", "center": [mcx + 0.18 * mw, mcy + 0.22 * mh], "radius": 0.024},
        ],
        "sectors": {
            "industrial": [mcx - 0.26 * mw, mcy - 0.06 * mh],
            "logistics": [mcx - 0.14 * mw, mcy - 0.22 * mh],
            "entertainment": [mcx + 0.05 * mw, mcy - 0.02 * mh],
        },
    }

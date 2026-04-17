from __future__ import annotations

import math
import random
from typing import Any

from .districts import classify_district

def _in_bbox(x: float, y: float, bbox: list[float], pad: float = 0.0) -> bool:
    return (bbox[0] - pad) <= x <= (bbox[2] + pad) and (bbox[1] - pad) <= y <= (bbox[3] + pad)

def _ring_coords(cx: float, cy: float, rx: float, ry: float, n: int,
                 wobble: float = 0.0, rng: random.Random | None = None) -> list[list[float]]:
    pts: list[list[float]] = []
    for i in range(n):
        t = i / n * math.pi * 2
        wf = 1.0
        if wobble > 0:
            wf += wobble * math.sin(t * 3.7) + wobble * 0.5 * math.cos(t * 6.3)
            if rng:
                wf += (rng.random() - 0.5) * wobble * 0.3
        pts.append([cx + rx * wf * math.cos(t), cy + ry * wf * math.sin(t)])
    pts.append(pts[0])
    return pts

def _line(x0: float, y0: float, x1: float, y1: float, n: int = 2) -> list[list[float]]:
    if n <= 2:
        return [[x0, y0], [x1, y1]]
    return [[x0 + (x1 - x0) * i / (n - 1), y0 + (y1 - y0) * i / (n - 1)] for i in range(n)]

def _curved_line(x0: float, y0: float, x1: float, y1: float,
                 wave: float, n: int = 20, rng: random.Random | None = None) -> list[list[float]]:
    dx, dy = x1 - x0, y1 - y0
    length = math.sqrt(dx * dx + dy * dy)
    if length < 1e-9:
        return [[x0, y0], [x1, y1]]
    px, py = -dy / length, dx / length
    coords: list[list[float]] = []
    for i in range(n + 1):
        t = i / n
        bx = x0 + dx * t
        by = y0 + dy * t
        bend = math.sin(t * math.pi) * wave
        if rng:
            bend += (rng.random() - 0.5) * wave * 0.3
        coords.append([bx + px * bend, by + py * bend])
    return coords

def _clip_to_bbox(coords: list[list[float]], bbox: list[float], pad: float = 0.02) -> list[list[float]]:
    out: list[list[float]] = []
    for p in coords:
        if _in_bbox(p[0], p[1], bbox, pad):
            out.append(p)
        elif out:
            break
    return out if len(out) >= 2 else []

def _feat(coords: list[list[float]], props: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "Feature",
        "properties": props,
        "geometry": {"type": "LineString", "coordinates": coords},
    }

ROAD_CLASSES = {
    "expressway": {"kind": "highway", "kind_detail": "motorway", "z_order": 6},
    "trunk": {"kind": "major_road", "kind_detail": "trunk", "z_order": 5},
    "arterial": {"kind": "major_road", "kind_detail": "primary", "z_order": 4},
    "secondary_arterial": {"kind": "major_road", "kind_detail": "secondary", "z_order": 3},
    "collector": {"kind": "minor_road", "kind_detail": "tertiary", "z_order": 2},
    "local": {"kind": "minor_road", "kind_detail": "residential", "z_order": 1},
    "service": {"kind": "minor_road", "kind_detail": "service", "z_order": 0},
}

def _road_props(road_class: str, name: str = "", **extra: Any) -> dict[str, Any]:
    base = dict(ROAD_CLASSES.get(road_class, ROAD_CLASSES["local"]))
    base["roadClass"] = road_class
    base["name"] = name
    base["structure"] = extra.get("structure", "normal")
    base["bridge"] = extra.get("bridge", False)
    base["tunnel"] = extra.get("tunnel", False)
    base["oneway"] = extra.get("oneway", False)
    return base

def _fabric_historic(cx: float, cy: float, radius: float, rng: random.Random,
                     bbox: list[float]) -> list[dict[str, Any]]:
    feats: list[dict[str, Any]] = []
    n_streets = int(radius * 8000)
    for i in range(n_streets):
        ang = rng.random() * math.pi * 2
        r = rng.random() * radius * 0.9
        sx = cx + math.cos(ang) * r
        sy = cy + math.sin(ang) * r
        for j in range(rng.randint(2, 5)):
            a2 = ang + (rng.random() - 0.5) * 2.2
            ln = radius * (0.03 + rng.random() * 0.08)
            ex = sx + math.cos(a2) * ln
            ey = sy + math.sin(a2) * ln
            coords = _clip_to_bbox([[sx, sy], [ex, ey]], bbox)
            if coords:
                feats.append(_feat(coords, _road_props("local", f"Old Quarter Lane {i}-{j}")))
            sx, sy = ex, ey
    return feats

def _fabric_cbd(cx: float, cy: float, rx: float, ry: float, rng: random.Random,
                bbox: list[float]) -> list[dict[str, Any]]:
    feats: list[dict[str, Any]] = []
    spacing = min(rx, ry) * 0.25
    n_ew = max(3, int(2 * ry / spacing))
    n_ns = max(3, int(2 * rx / spacing))
    base_ang = rng.random() * 0.3 - 0.15
    ca, sa = math.cos(base_ang), math.sin(base_ang)

    for i in range(n_ew + 1):
        t = (i / n_ew - 0.5) * 2
        oy = t * ry * 0.95
        x0 = cx - rx * 0.95
        x1 = cx + rx * 0.95
        ax0 = cx + (x0 - cx) * ca - oy * sa
        ay0 = cy + (x0 - cx) * sa + oy * ca
        ax1 = cx + (x1 - cx) * ca - oy * sa
        ay1 = cy + (x1 - cx) * sa + oy * ca
        rc = "arterial" if i % 4 == 0 else ("collector" if i % 2 == 0 else "local")
        coords = _clip_to_bbox(_line(ax0, ay0, ax1, ay1, 12), bbox)
        if coords:
            feats.append(_feat(coords, _road_props(rc, f"CBD Avenue {i}")))

    for j in range(n_ns + 1):
        t = (j / n_ns - 0.5) * 2
        ox = t * rx * 0.95
        y0 = cy - ry * 0.95
        y1 = cy + ry * 0.95
        ax0 = cx + ox * ca - (y0 - cy) * sa
        ay0 = cy + ox * sa + (y0 - cy) * ca
        ax1 = cx + ox * ca - (y1 - cy) * sa
        ay1 = cy + ox * sa + (y1 - cy) * ca
        rc = "arterial" if j % 4 == 0 else ("collector" if j % 2 == 0 else "local")
        coords = _clip_to_bbox(_line(ax0, ay0, ax1, ay1, 12), bbox)
        if coords:
            feats.append(_feat(coords, _road_props(rc, f"CBD Street {j}")))

    for d in range(2):
        sign = 1 if d == 0 else -1
        coords = _clip_to_bbox(
            _line(cx - rx * 0.8, cy - ry * 0.7 * sign, cx + rx * 0.8, cy + ry * 0.7 * sign, 16), bbox)
        if coords:
            feats.append(_feat(coords, _road_props("secondary_arterial", f"CBD Diagonal {d}")))
    return feats

def _fabric_grid(cx: float, cy: float, extent: float, spacing: float, jitter: float,
                 road_class: str, rng: random.Random, bbox: list[float],
                 angle: float = 0.0, label: str = "Grid") -> list[dict[str, Any]]:
    feats: list[dict[str, Any]] = []
    n = max(2, int(2 * extent / spacing))
    ca, sa = math.cos(angle), math.sin(angle)
    for axis in (0, 1):
        for i in range(n + 1):
            t = (i / n - 0.5) * 2 * extent
            offset = (rng.random() - 0.5) * jitter
            if axis == 0:
                lx0, ly0 = cx - extent, cy + t + offset
                lx1, ly1 = cx + extent, cy + t + offset
            else:
                lx0, ly0 = cx + t + offset, cy - extent
                lx1, ly1 = cx + t + offset, cy + extent
            rx0 = cx + (lx0 - cx) * ca - (ly0 - cy) * sa
            ry0 = cy + (lx0 - cx) * sa + (ly0 - cy) * ca
            rx1 = cx + (lx1 - cx) * ca - (ly1 - cy) * sa
            ry1 = cy + (lx1 - cx) * sa + (ly1 - cy) * ca
            rc = "collector" if i % 3 == 0 else road_class
            coords = _clip_to_bbox(_curved_line(rx0, ry0, rx1, ry1,
                                                wave=jitter * 0.5, n=10, rng=rng), bbox)
            if coords:
                feats.append(_feat(coords, _road_props(rc, f"{label} {axis}-{i}")))
    return feats

def _fabric_superblock(cx: float, cy: float, rx: float, ry: float,
                       rng: random.Random, bbox: list[float],
                       label: str = "Industrial") -> list[dict[str, Any]]:
    feats: list[dict[str, Any]] = []
    ring = _ring_coords(cx, cy, rx, ry, 32, wobble=0.03, rng=rng)
    clipped = _clip_to_bbox(ring, bbox)
    if len(clipped) >= 2:
        feats.append(_feat(clipped, _road_props("collector", f"{label} Perimeter")))
    for i in range(rng.randint(2, 4)):
        ang = rng.random() * math.pi
        x0 = cx + math.cos(ang) * rx * 0.9
        y0 = cy + math.sin(ang) * ry * 0.9
        x1 = cx - math.cos(ang) * rx * 0.9
        y1 = cy - math.sin(ang) * ry * 0.9
        coords = _clip_to_bbox(_line(x0, y0, x1, y1, 6), bbox)
        if coords:
            feats.append(_feat(coords, _road_props("service", f"{label} Spine {i}")))
    return feats

def _fabric_campus(cx: float, cy: float, radius_x: float, radius_y: float,
                   rng: random.Random, bbox: list[float],
                   name: str = "Campus") -> list[dict[str, Any]]:
    feats: list[dict[str, Any]] = []
    ring = _ring_coords(cx, cy, radius_x * 0.85, radius_y * 0.85, 40, wobble=0.06, rng=rng)
    clipped = _clip_to_bbox(ring, bbox)
    if len(clipped) >= 2:
        feats.append(_feat(clipped, _road_props("collector", f"{name} Loop")))
    for i in range(rng.randint(3, 6)):
        ang = rng.random() * math.pi * 2
        coords = _clip_to_bbox(_line(cx, cy, cx + math.cos(ang) * radius_x * 0.75,
                                     cy + math.sin(ang) * radius_y * 0.75, 4), bbox)
        if coords:
            feats.append(_feat(coords, _road_props("service", f"{name} Path {i}")))
    return feats

def _fabric_airport(ap: dict[str, Any], rng: random.Random, bbox: list[float]) -> list[dict[str, Any]]:
    feats: list[dict[str, Any]] = []
    cx, cy = ap["center"]
    sx, sy = ap["size_x"], ap["size_y"]
    ring = _ring_coords(cx, cy, sx * 0.55, sy * 0.55, 40, wobble=0.02, rng=rng)
    clipped = _clip_to_bbox(ring, bbox)
    if len(clipped) >= 2:
        feats.append(_feat(clipped, _road_props("collector", f"{ap['name']} Perimeter")))
    coords = _clip_to_bbox(_line(cx - sx * 0.5, cy, cx + sx * 0.5, cy, 8), bbox)
    if coords:
        feats.append(_feat(coords, _road_props("arterial", f"{ap['name']} Terminal Rd")))
    coords = _clip_to_bbox(_line(cx, cy - sy * 0.45, cx, cy + sy * 0.45, 6), bbox)
    if coords:
        feats.append(_feat(coords, _road_props("service", f"{ap['name']} Cargo Rd")))
    return feats

def generate_roads(plan: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(int(cfg["build"]["seed"]) + 1201)
    bbox = cfg["map"]["bbox"]
    min_x, min_y, max_x, max_y = bbox
    w = max_x - min_x
    h = max_y - min_y
    pad = max(w, h) * 0.02
    cx, cy = plan["center"]
    mw = plan["metro_scale"]["w"]
    mh = plan["metro_scale"]["h"]

    features: list[dict[str, Any]] = []

    ring_names = ["Inner Wall Boulevard", "Middle Ring Expressway", "Outer Ring Expressway", "Metropolitan Loop"]
    ring_classes = ["trunk", "expressway", "expressway", "expressway"]
    for i, rr in enumerate(plan["ring_radii"]):
        ring = _ring_coords(cx, cy, rr, rr * mh / mw * 0.96, n=160,
                            wobble=0.015 + 0.005 * i, rng=rng)
        clipped = _clip_to_bbox(ring, bbox, pad)
        if len(clipped) >= 2:
            features.append(_feat(clipped, _road_props(
                ring_classes[i], ring_names[i],
                oneway=True if ring_classes[i] == "expressway" else False,
                structure="elevated" if i >= 2 else "normal")))

    for i in range(10):
        ang = i * (math.pi * 2 / 10) + 0.1
        r_inner = plan["ring_radii"][0] * 0.3
        r_outer = plan["ring_radii"][-1] * 1.15
        x0 = cx + math.cos(ang) * r_inner
        y0 = cy + math.sin(ang) * r_inner * mh / mw
        x1 = cx + math.cos(ang) * r_outer
        y1 = cy + math.sin(ang) * r_outer * mh / mw
        rc = "trunk" if i % 3 == 0 else "arterial"
        coords = _clip_to_bbox(
            _curved_line(x0, y0, x1, y1, wave=mw * 0.003, n=28, rng=rng), bbox, pad)
        if coords:
            features.append(_feat(coords, _road_props(rc, f"Radial Avenue {i+1}",
                                                      oneway=rc == "trunk")))

    lake = plan["lake"]
    for ap_key in ["primary_airport", "secondary_airport"]:
        ap = plan[ap_key]
        coords = _clip_to_bbox(
            _curved_line(*ap["center"], *lake["center"],
                         wave=mw * 0.01, n=24, rng=rng), bbox, pad)
        if coords:
            features.append(_feat(coords, _road_props(
                "trunk", f"{ap['name']} Express Connector", structure="elevated")))

    for d in range(2):
        a = math.pi * 0.25 + d * math.pi * 0.5
        x0 = cx + math.cos(a) * mw * 0.35
        y0 = cy + math.sin(a) * mh * 0.35
        x1 = cx - math.cos(a) * mw * 0.35
        y1 = cy - math.sin(a) * mh * 0.35
        coords = _clip_to_bbox(_curved_line(x0, y0, x1, y1, wave=mw * 0.005, n=24, rng=rng), bbox, pad)
        if coords:
            features.append(_feat(coords, _road_props("arterial", f"Cross-City Diagonal {d+1}")))

    core_r = plan["ring_radii"][0]
    if any(_in_bbox(cx + dx, cy + dy, bbox, pad) for dx in [-core_r, core_r] for dy in [-core_r, core_r]):
        features.extend(_fabric_historic(cx, cy, core_r, rng, bbox))

    cbd = plan["cbd_crescent"]
    if any(_in_bbox(cbd["center"][0] + dx, cbd["center"][1] + dy, bbox, pad)
           for dx in [-cbd["rx"], cbd["rx"]] for dy in [-cbd["ry"], cbd["ry"]]):
        features.extend(_fabric_cbd(*cbd["center"], cbd["rx"], cbd["ry"], rng, bbox))

    for sc in plan["secondary_centers"]:
        sr = mw * sc["radius"]
        if _in_bbox(*sc["center"], bbox, pad + sr):
            features.extend(_fabric_grid(*sc["center"], sr, sr * 0.18,
                                         sr * 0.01, "collector", rng, bbox,
                                         angle=rng.random() * 0.4, label=sc["name"]))

    ring_bands = [
        (plan["ring_radii"][0], plan["ring_radii"][1], "inner_mixed", 0.008, "local"),
        (plan["ring_radii"][1], plan["ring_radii"][2], "inner_residential", 0.012, "local"),
        (plan["ring_radii"][2], plan["ring_radii"][3], "outer_residential", 0.018, "local"),
    ]
    for r_inner, r_outer, band_name, spacing_deg, default_class in ring_bands:
        n_sectors = max(4, int(math.pi * 2 * (r_inner + r_outer) / 2 / (spacing_deg * 8)))
        for s in range(n_sectors):
            ang = s * math.pi * 2 / n_sectors + rng.random() * 0.3
            r = (r_inner + r_outer) / 2 + (rng.random() - 0.5) * (r_outer - r_inner) * 0.4
            scx = cx + math.cos(ang) * r
            scy = cy + math.sin(ang) * r * mh / mw
            if not _in_bbox(scx, scy, bbox, pad):
                continue
            dist = classify_district(scx, scy, plan)
            if dist in ("water", "airport", "park"):
                continue
            extent = spacing_deg * 4
            jitter = spacing_deg * (0.3 if band_name == "inner_mixed" else 0.5)
            sector_angle = ang + (rng.random() - 0.5) * 0.6
            features.extend(_fabric_grid(scx, scy, extent, spacing_deg, jitter,
                                         default_class, rng, bbox, angle=sector_angle,
                                         label=f"{band_name.replace('_', ' ').title()} Sector {s}"))

    n_peri = max(6, int(w * h / (0.02 * 0.02) * 0.15))
    for i in range(n_peri):
        px = min_x + rng.random() * w
        py = min_y + rng.random() * h
        dist = classify_district(px, py, plan)
        if dist not in ("peri_urban_mixed", "peri_residential"):
            continue
        for j in range(rng.randint(2, 4)):
            ang = rng.random() * math.pi
            ln = 0.015 + rng.random() * 0.02
            coords = _clip_to_bbox(
                _curved_line(px, py, px + math.cos(ang) * ln, py + math.sin(ang) * ln,
                             wave=0.002, n=8, rng=rng), bbox)
            if coords:
                rc = "collector" if j == 0 else "local"
                features.append(_feat(coords, _road_props(rc, f"Peri {i}-{j}")))

    for z in plan["industrial_zones"]:
        if _in_bbox(*z["center"], bbox, pad + z["rx"]):
            features.extend(_fabric_superblock(*z["center"], z["rx"], z["ry"], rng, bbox, "Industrial"))
    for z in plan["logistics_zones"]:
        if _in_bbox(*z["center"], bbox, pad + z["rx"]):
            features.extend(_fabric_superblock(*z["center"], z["rx"], z["ry"], rng, bbox, "Logistics"))

    for c in plan["campuses"]:
        crx = mw * c["radius"]
        cry = mh * c["radius"]
        if _in_bbox(*c["center"], bbox, pad + crx):
            features.extend(_fabric_campus(*c["center"], crx, cry, rng, bbox, c["name"]))

    for ap_key in ["primary_airport", "secondary_airport"]:
        ap = plan[ap_key]
        if _in_bbox(*ap["center"], bbox, pad + ap["size_x"]):
            features.extend(_fabric_airport(ap, rng, bbox))

    return {"type": "FeatureCollection", "features": features}

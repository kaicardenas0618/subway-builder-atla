from __future__ import annotations

import math
import random
from typing import Any

from .districts import classify_district

ZONE_RESOLUTION = {
    "imperial_core": 0.005,
    "cbd": 0.004,
    "subcenter": 0.005,
    "inner_mixed": 0.007,
    "inner_residential": 0.009,
    "outer_residential": 0.013,
    "peri_urban_mixed": 0.018,
    "peri_residential": 0.022,
    "industrial": 0.016,
    "logistics": 0.020,
    "airport": 0.025,
    "campus": 0.008,
    "entertainment": 0.009,
}

JOB_BIAS = {
    "imperial_core": 1.8, "cbd": 2.8, "subcenter": 2.0,
    "inner_mixed": 1.4, "inner_residential": 0.6,
    "outer_residential": 0.5, "peri_urban_mixed": 0.7, "peri_residential": 0.4,
    "industrial": 2.0, "logistics": 2.2, "airport": 2.8,
    "campus": 1.6, "entertainment": 1.5,
}

RES_BIAS = {
    "imperial_core": 0.7, "cbd": 0.5, "subcenter": 0.9,
    "inner_mixed": 1.2, "inner_residential": 1.8,
    "outer_residential": 1.7, "peri_urban_mixed": 1.3, "peri_residential": 1.5,
    "industrial": 0.2, "logistics": 0.15, "airport": 0.1,
    "campus": 1.0, "entertainment": 0.6,
}

def _centroid(ring: list[list[float]]) -> tuple[float, float]:
    n = max(1, len(ring) - 1)
    return sum(p[0] for p in ring[:n]) / n, sum(p[1] for p in ring[:n]) / n

def _travel(hx: float, hy: float, jx: float, jy: float) -> tuple[int, int]:
    dx = (jx - hx) * 111_000 * math.cos(math.radians((hy + jy) / 2))
    dy = (jy - hy) * 111_000
    direct = math.sqrt(dx * dx + dy * dy)
    distance = int(max(500, direct * 1.30))
    seconds = int(max(180, distance / 8.5))
    return seconds, distance

def _lognormal_cohort_size(rng: random.Random, mu: float = 3.5, sigma: float = 0.8,
                           cap: int = 240) -> int:
    raw = math.exp(rng.gauss(mu, sigma))
    return max(1, min(cap, int(raw)))

def generate_demand(plan: dict[str, Any], cfg: dict[str, Any],
                    buildings_index: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(int(cfg["build"]["seed"]) + 4201)
    min_x, min_y = cfg["map"]["bbox"][0], cfg["map"]["bbox"][1]
    target_pop = int(cfg["build"]["target_population"])
    max_pop_size = int(cfg["build"].get("max_pop_size", 240))
    commute_share = float(cfg["build"].get("commute_share", 0.9))

    zones: dict[tuple[str, int, int], dict[str, Any]] = {}
    for b in buildings_index.get("buildings", []):
        ring = b["p"][0]
        x, y = _centroid(ring)
        district = classify_district(x, y, plan)
        if district in ("water", "park"):
            continue
        res = ZONE_RESOLUTION.get(district, 0.015)
        ix = int((x - min_x) / max(1e-9, res))
        iy = int((y - min_y) / max(1e-9, res))
        area = max(1e-12, (b["b"][2] - b["b"][0]) * (b["b"][3] - b["b"][1]))
        intensity = area * max(1, b["f"])
        k = (district, ix, iy)
        z = zones.setdefault(k, {"district": district, "sx": 0.0, "sy": 0.0, "sw": 0.0, "intensity": 0.0})
        z["sx"] += x * intensity
        z["sy"] += y * intensity
        z["sw"] += intensity
        z["intensity"] += intensity

    points: list[dict[str, Any]] = []
    for i, (_, z) in enumerate(sorted(zones.items(), key=lambda kv: kv[1]["intensity"], reverse=True)):
        x = z["sx"] / max(1e-9, z["sw"])
        y = z["sy"] / max(1e-9, z["sw"])
        district = z["district"]
        jobs = int(max(10, z["intensity"] * JOB_BIAS.get(district, 1.0) * 4500))
        residents = int(max(10, z["intensity"] * RES_BIAS.get(district, 1.0) * 4200))
        points.append({
            "id": f"mz_{i:05d}",
            "location": [x, y],
            "jobs": jobs,
            "residents": residents,
            "popIds": [],
            "_district": district,
        })

    if not points:
        return {"points": [], "pops": []}

    current_pop = sum(p["residents"] for p in points)
    if current_pop > 0:
        scale = target_pop / current_pop
        for p in points:
            p["residents"] = max(1, int(round(p["residents"] * scale)))
            p["jobs"] = max(1, int(round(p["jobs"] * scale * 0.90)))

    points_by_id = {p["id"]: p for p in points}
    pops: list[dict[str, Any]] = []
    pop_counter = 0

    for h in points:
        commuters = int(h["residents"] * commute_share)
        if commuters <= 0:
            continue

        scored: list[tuple[float, dict[str, Any]]] = []
        hx, hy = h["location"]
        for c in points:
            jx, jy = c["location"]
            d = math.sqrt((jx - hx)**2 + (jy - hy)**2)
            attract = c["jobs"] / max(0.002, d ** 1.3)
            if c["_district"] in ("cbd", "airport", "subcenter"):
                attract *= 1.4
            scored.append((max(1e-6, attract), c))

        n_dest = min(20, max(3, int(h["residents"] / 15000)))
        pool = scored[:]
        destinations: list[dict[str, Any]] = []
        for _ in range(min(n_dest, len(pool))):
            total = sum(w for w, _ in pool)
            t = rng.random() * total
            s = 0.0
            idx = 0
            for ii, (ww, _) in enumerate(pool):
                s += ww
                if s >= t:
                    idx = ii
                    break
            _, chosen = pool.pop(idx)
            destinations.append(chosen)

        if not destinations:
            continue

        weights = [max(1.0, j["jobs"]) for j in destinations]
        total_w = sum(weights)
        assigned = 0
        for di, dest in enumerate(destinations):
            if di == len(destinations) - 1:
                cohort_total = max(1, commuters - assigned)
            else:
                cohort_total = max(1, int(commuters * weights[di] / total_w))
                assigned += cohort_total

            remaining = cohort_total
            while remaining > 0:
                size = min(remaining, _lognormal_cohort_size(rng, cap=max_pop_size))
                remaining -= size
                sec, dist = _travel(hx, hy, *dest["location"])
                pid = f"pop_{pop_counter:07d}"
                pop_counter += 1
                pops.append({
                    "residenceId": h["id"],
                    "jobId": dest["id"],
                    "drivingSeconds": sec,
                    "drivingDistance": dist,
                    "size": size,
                    "id": pid,
                })
                points_by_id[h["id"]]["popIds"].append(pid)
                if dest["id"] != h["id"]:
                    points_by_id[dest["id"]]["popIds"].append(pid)

    for p in points:
        seen: set[str] = set()
        uniq: list[str] = []
        for pid in p["popIds"]:
            if pid not in seen:
                uniq.append(pid)
                seen.add(pid)
        p["popIds"] = uniq
        p.pop("_district", None)

    return {"points": points, "pops": pops}

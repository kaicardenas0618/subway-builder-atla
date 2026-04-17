from __future__ import annotations

import math
import random
from typing import Any

from .districts import classify_district


DISTRICT_RESOLUTION = {
    "imperial_core": 0.006,
    "cbd": 0.007,
    "inner_mixed": 0.009,
    "inner_residential": 0.011,
    "outer_residential": 0.014,
    "peri_urban_mixed": 0.017,
    "peri_residential": 0.020,
    "industrial": 0.018,
    "logistics": 0.020,
    "airport": 0.026,
    "campus": 0.010,
    "entertainment": 0.011,
}

DISTRICT_JOB_BIAS = {
    "imperial_core": 2.4,
    "cbd": 2.1,
    "inner_mixed": 1.3,
    "inner_residential": 0.7,
    "outer_residential": 0.55,
    "peri_urban_mixed": 0.75,
    "peri_residential": 0.45,
    "industrial": 1.7,
    "logistics": 1.8,
    "airport": 2.5,
    "campus": 1.4,
    "entertainment": 1.2,
}

DISTRICT_RES_BIAS = {
    "imperial_core": 0.8,
    "cbd": 0.7,
    "inner_mixed": 1.1,
    "inner_residential": 1.7,
    "outer_residential": 1.6,
    "peri_urban_mixed": 1.2,
    "peri_residential": 1.4,
    "industrial": 0.3,
    "logistics": 0.25,
    "airport": 0.2,
    "campus": 1.3,
    "entertainment": 0.8,
}


def _centroid(ring: list[list[float]]) -> tuple[float, float]:
    x = sum(p[0] for p in ring[:-1]) / max(1, len(ring) - 1)
    y = sum(p[1] for p in ring[:-1]) / max(1, len(ring) - 1)
    return x, y


def _travel(home: tuple[float, float], job: tuple[float, float]) -> tuple[int, int]:
    lon1, lat1 = home
    lon2, lat2 = job
    dx = (lon2 - lon1) * 111_000 * math.cos(math.radians((lat1 + lat2) / 2))
    dy = (lat2 - lat1) * 111_000
    direct = math.sqrt(dx * dx + dy * dy)
    distance = int(max(500, direct * 1.28))
    seconds = int(max(210, distance / 8.2))
    return seconds, distance


def _sample_jobs(rng: random.Random, home: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hx, hy = home["location"]
    scored: list[tuple[float, dict[str, Any]]] = []
    for c in candidates:
        jx, jy = c["location"]
        d = math.sqrt((jx - hx) ** 2 + (jy - hy) ** 2)
        attract = c["jobs"] / max(0.003, d ** 1.2)
        if c.get("district") in {"airport", "campus", "cbd", "imperial_core"}:
            attract *= 1.35
        scored.append((max(1e-6, attract), c))

    picks = min(16, max(4, int(home["residents"] / 22000)))
    out: list[dict[str, Any]] = []
    pool = scored[:]
    for _ in range(min(picks, len(pool))):
        total = sum(w for w, _ in pool)
        t = rng.random() * total
        s = 0.0
        idx = 0
        for i, (w, _) in enumerate(pool):
            s += w
            if s >= t:
                idx = i
                break
        _, chosen = pool.pop(idx)
        out.append(chosen)
    return out


def generate_demand(layout: dict[str, Any], cfg: dict[str, Any], buildings_index: dict[str, Any]) -> dict[str, Any]:
    rng = random.Random(int(cfg["build"]["seed"]) + 4201)
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]
    target_population = int(cfg["build"]["target_population"])
    max_pop_size = int(cfg["build"].get("max_pop_size", 240))
    commute_share = float(cfg["build"].get("commute_share", 0.9))

    agg: dict[tuple[str, int, int], dict[str, Any]] = {}
    for b in buildings_index.get("buildings", []):
        ring = b["p"][0]
        x, y = _centroid(ring)
        district = classify_district(x, y, layout)
        if district == "water":
            continue
        res = DISTRICT_RESOLUTION.get(district, 0.015)
        ix = int((x - min_x) / max(1e-9, res))
        iy = int((y - min_y) / max(1e-9, res))

        area = max(1e-12, (b["b"][2] - b["b"][0]) * (b["b"][3] - b["b"][1]))
        intensity = area * max(1.0, b["f"])
        k = (district, ix, iy)
        e = agg.setdefault(k, {"district": district, "sx": 0.0, "sy": 0.0, "sw": 0.0, "intensity": 0.0})
        e["sx"] += x * intensity
        e["sy"] += y * intensity
        e["sw"] += intensity
        e["intensity"] += intensity

    points: list[dict[str, Any]] = []
    for i, (_, e) in enumerate(sorted(agg.items(), key=lambda kv: kv[1]["intensity"], reverse=True)):
        x = e["sx"] / max(1e-9, e["sw"])
        y = e["sy"] / max(1e-9, e["sw"])
        district = e["district"]
        jobs = int(max(20, e["intensity"] * DISTRICT_JOB_BIAS.get(district, 1.0) * 4300))
        residents = int(max(20, e["intensity"] * DISTRICT_RES_BIAS.get(district, 1.0) * 3900))
        points.append(
            {
                "id": f"merged_dp_{i:05d}",
                "location": [x, y],
                "jobs": jobs,
                "residents": residents,
                "popIds": [],
                "district": district,
            }
        )

    if not points:
        return {"points": [], "pops": []}

    current_pop = sum(p["residents"] for p in points)
    scale = target_population / max(1, current_pop)
    for p in points:
        p["residents"] = max(1, int(round(p["residents"] * scale)))
        p["jobs"] = max(1, int(round(p["jobs"] * scale * 0.92)))

    points_by_id = {p["id"]: p for p in points}
    pops: list[dict[str, Any]] = []
    pop_counter = 0

    for h in points:
        commuters = int(h["residents"] * commute_share)
        if commuters <= 0:
            continue

        jobs = _sample_jobs(rng, h, points)
        if not jobs:
            continue

        weights = [max(1.0, j["jobs"]) for j in jobs]
        total_w = sum(weights)
        assigned = 0
        for i, j in enumerate(jobs):
            if i == len(jobs) - 1:
                cohort = max(1, commuters - assigned)
            else:
                cohort = max(1, int(commuters * weights[i] / total_w))
                assigned += cohort

            remaining = cohort
            while remaining > 0:
                size = min(max_pop_size, remaining)
                remaining -= size
                sec, dist = _travel((h["location"][0], h["location"][1]), (j["location"][0], j["location"][1]))
                pid = f"agg_{pop_counter:07d}"
                pop_counter += 1
                pops.append(
                    {
                        "residenceId": h["id"],
                        "jobId": j["id"],
                        "drivingSeconds": sec,
                        "drivingDistance": dist,
                        "size": size,
                        "id": pid,
                    }
                )
                points_by_id[h["id"]]["popIds"].append(pid)
                if j["id"] != h["id"]:
                    points_by_id[j["id"]]["popIds"].append(pid)

    for p in points:
        seen = set()
        uniq = []
        for pid in p["popIds"]:
            if pid not in seen:
                uniq.append(pid)
                seen.add(pid)
        p["popIds"] = uniq
        p.pop("district", None)

    return {"points": points, "pops": pops}

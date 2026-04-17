from __future__ import annotations

import json
import math
import subprocess
import zipfile
from pathlib import Path
from typing import Any


REQUIRED_CONFIG_KEYS = {
    "name",
    "code",
    "description",
    "population",
    "creator",
    "version",
    "initialViewState",
}
REQUIRED_INITIAL_VIEW_KEYS = {"latitude", "longitude", "zoom", "bearing"}
REQUIRED_ROOT_FILES = {
    "config.json",
    "demand_data.json",
    "roads.geojson",
    "runways_taxiways.geojson",
    "buildings_index.json",
}


def validate_demand_integrity(demand_data: dict[str, Any]) -> dict[str, Any]:
    points = demand_data.get("points", [])
    pops = demand_data.get("pops", [])

    point_ids = [p["id"] for p in points]
    pop_ids = [p["id"] for p in pops]
    if len(set(point_ids)) != len(point_ids):
        raise RuntimeError("demand integrity failed: duplicate point IDs")
    if len(set(pop_ids)) != len(pop_ids):
        raise RuntimeError("demand integrity failed: duplicate pop IDs")

    point_id_set = set(point_ids)
    pop_id_set = set(pop_ids)
    pops_by_id = {p["id"]: p for p in pops}

    for p in pops:
        if p["residenceId"] not in point_id_set:
            raise RuntimeError(f"demand integrity failed: unknown residenceId {p['residenceId']}")
        if p["jobId"] not in point_id_set:
            raise RuntimeError(f"demand integrity failed: unknown jobId {p['jobId']}")
        if p.get("size", 0) <= 0:
            raise RuntimeError(f"demand integrity failed: invalid pop size for {p['id']}")
        if p.get("drivingSeconds", 0) <= 0 or p.get("drivingDistance", 0) <= 0:
            raise RuntimeError(f"demand integrity failed: invalid travel metrics for {p['id']}")

    point_refs: dict[str, set[str]] = {}
    for point in points:
        refs = point.get("popIds", [])
        if len(set(refs)) != len(refs):
            raise RuntimeError(f"demand integrity failed: duplicate popIds in point {point['id']}")
        for rid in refs:
            if rid not in pop_id_set:
                raise RuntimeError(f"demand integrity failed: point {point['id']} references missing pop {rid}")
        point_refs[point["id"]] = set(refs)

    for pop in pops:
        pid = pop["id"]
        h = pop["residenceId"]
        j = pop["jobId"]
        if pid not in point_refs[h]:
            raise RuntimeError(f"demand integrity failed: pop {pid} missing from home point {h}")
        if pid not in point_refs[j]:
            raise RuntimeError(f"demand integrity failed: pop {pid} missing from job point {j}")

    total_pop_size = sum(int(p["size"]) for p in pops)
    return {
        "pointCount": len(points),
        "popCount": len(pops),
        "representedPopulation": total_pop_size,
    }


def _validate_realism_sanity(output_dir: Path, demand_data: dict[str, Any], cfg: dict[str, Any], mode: str) -> None:
    roads = json.loads((output_dir / "roads.geojson").read_text(encoding="utf-8"))
    buildings = json.loads((output_dir / "buildings_index.json").read_text(encoding="utf-8"))

    road_counts: dict[str, int] = {}
    for f in roads.get("features", []):
        rc = f.get("properties", {}).get("roadClass", "unknown")
        road_counts[rc] = road_counts.get(rc, 0) + 1

    if road_counts.get("trunk", 0) < (3 if mode == "dev" else 5):
        raise RuntimeError("realism validation failed: insufficient trunk road hierarchy")
    if road_counts.get("major", 0) < (20 if mode == "dev" else 80):
        raise RuntimeError("realism validation failed: insufficient major road coverage")

    floors = [float(b["f"]) for b in buildings.get("buildings", [])]
    if not floors:
        raise RuntimeError("realism validation failed: no buildings generated")
    floor_mean = sum(floors) / len(floors)
    floor_var = sum((f - floor_mean) ** 2 for f in floors) / len(floors)
    if floor_var < (6 if mode == "dev" else 10):
        raise RuntimeError("realism validation failed: building height variance too low")

    areas = [max(1e-10, (b["b"][2] - b["b"][0]) * (b["b"][3] - b["b"][1])) for b in buildings.get("buildings", [])]
    area_mean = sum(areas) / len(areas)
    area_var = sum((a - area_mean) ** 2 for a in areas) / len(areas)
    if area_var < area_mean * area_mean * 0.05:
        raise RuntimeError("realism validation failed: block/building size variability too low")

    bbox = cfg["map"]["bbox"]
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    core_points = 0
    outer_points = 0
    for p in demand_data.get("points", []):
        x, y = p["location"]
        if abs(x - cx) < (bbox[2] - bbox[0]) * 0.12 and abs(y - cy) < (bbox[3] - bbox[1]) * 0.12:
            core_points += 1
        else:
            outer_points += 1
    if core_points <= 0 or outer_points <= 0:
        raise RuntimeError("realism validation failed: demand point distribution lacks core/outer balance")


def _validate_prod_dev_differentiation(repo_root: Path) -> None:
    prod_cfg_path = repo_root / "outputs" / "prod" / "config.json"
    dev_cfg_path = repo_root / "outputs" / "dev" / "config.json"
    prod_roads_path = repo_root / "outputs" / "prod" / "roads.geojson"
    dev_roads_path = repo_root / "outputs" / "dev" / "roads.geojson"
    prod_buildings_path = repo_root / "outputs" / "prod" / "buildings_index.json"
    dev_buildings_path = repo_root / "outputs" / "dev" / "buildings_index.json"

    paths = [
        prod_cfg_path,
        dev_cfg_path,
        prod_roads_path,
        dev_roads_path,
        prod_buildings_path,
        dev_buildings_path,
    ]
    if not all(p.exists() for p in paths):
        return

    prod_cfg = json.loads(prod_cfg_path.read_text(encoding="utf-8"))
    dev_cfg = json.loads(dev_cfg_path.read_text(encoding="utf-8"))
    prod_roads = json.loads(prod_roads_path.read_text(encoding="utf-8"))
    dev_roads = json.loads(dev_roads_path.read_text(encoding="utf-8"))
    prod_buildings = json.loads(prod_buildings_path.read_text(encoding="utf-8"))
    dev_buildings = json.loads(dev_buildings_path.read_text(encoding="utf-8"))

    prod_bbox = prod_cfg.get("bbox")
    dev_bbox = dev_cfg.get("bbox")
    prod_area = max(1e-9, (prod_bbox[2] - prod_bbox[0]) * (prod_bbox[3] - prod_bbox[1]))
    dev_area = max(1e-9, (dev_bbox[2] - dev_bbox[0]) * (dev_bbox[3] - dev_bbox[1]))
    if prod_area / dev_area < 3.0:
        raise RuntimeError("prod/dev validation failed: prod bbox not materially larger than dev")

    if prod_cfg.get("population", 0) < dev_cfg.get("population", 0) * 2:
        raise RuntimeError("prod/dev validation failed: prod population not materially larger than dev")

    if len(prod_roads.get("features", [])) < len(dev_roads.get("features", [])) * 2:
        raise RuntimeError("prod/dev validation failed: prod road totals not materially larger than dev")

    if len(prod_buildings.get("buildings", [])) < len(dev_buildings.get("buildings", [])) * 2:
        raise RuntimeError("prod/dev validation failed: prod building totals not materially larger than dev")


def validate_outputs(
    output_dir: Path,
    archive_path: Path,
    cfg: dict[str, Any],
    mode: str,
    pmtiles_filename: str,
) -> dict[str, Any]:
    required_paths = [
        output_dir / "config.json",
        output_dir / "demand_data.json",
        output_dir / "roads.geojson",
        output_dir / "runways_taxiways.geojson",
        output_dir / "buildings_index.json",
        output_dir / pmtiles_filename,
        archive_path,
    ]
    for path in required_paths:
        if not path.exists():
            raise RuntimeError(f"Missing required output: {path}")

    demand_data = json.loads((output_dir / "demand_data.json").read_text(encoding="utf-8"))
    demand_summary = validate_demand_integrity(demand_data)
    _validate_realism_sanity(output_dir, demand_data, cfg, mode)

    cfg = json.loads((output_dir / "config.json").read_text(encoding="utf-8"))
    missing_cfg = REQUIRED_CONFIG_KEYS.difference(cfg.keys())
    if missing_cfg:
        raise RuntimeError(f"config.json missing keys: {sorted(missing_cfg)}")

    ivs = cfg.get("initialViewState", {})
    missing_ivs = REQUIRED_INITIAL_VIEW_KEYS.difference(ivs.keys())
    if missing_ivs:
        raise RuntimeError(f"config.json initialViewState missing keys: {sorted(missing_ivs)}")

    pmtiles_path = output_dir / pmtiles_filename
    if pmtiles_path.stat().st_size <= 0:
        raise RuntimeError(f"{pmtiles_filename} is empty")

    subprocess.run(["pmtiles", "verify", str(pmtiles_path)], check=True, capture_output=True)
    show = subprocess.run(["pmtiles", "show", str(pmtiles_path)], check=True, capture_output=True, text=True)
    meta = show.stdout.lower()
    for layer_name in ["roads", "buildings"]:
        if layer_name not in meta:
            raise RuntimeError(f"PMTiles missing expected layer: {layer_name}")

    with zipfile.ZipFile(archive_path, "r") as zf:
        names = [info.filename for info in zf.infolist() if not info.is_dir()]
        root_names = {n for n in names if "/" not in n}
        missing_root = REQUIRED_ROOT_FILES.difference(root_names)
        if missing_root:
            raise RuntimeError(f"Archive missing required root-level files: {sorted(missing_root)}")
        pmtiles = [name for name in root_names if name.endswith(".pmtiles")]
        if len(pmtiles) != 1:
            raise RuntimeError(f"Archive must contain exactly one .pmtiles file; found {len(pmtiles)}")

    _validate_prod_dev_differentiation(output_dir.parents[1])
    return demand_summary

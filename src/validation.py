from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path
from typing import Any

REQUIRED_CONFIG_KEYS = {"name", "code", "description", "population", "creator", "version", "initialViewState"}
REQUIRED_INITIAL_VIEW_KEYS = {"latitude", "longitude", "zoom", "bearing"}
REQUIRED_ROOT_FILES = {"config.json", "demand_data.json", "roads.geojson", "runways_taxiways.geojson", "buildings_index.json"}

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

    sizes = [p["size"] for p in pops]
    if len(set(sizes)) < min(5, len(sizes)):
        raise RuntimeError("demand integrity failed: pop sizes lack variation (variable cohorts required)")

    return {
        "pointCount": len(points),
        "popCount": len(pops),
        "representedPopulation": total_pop_size,
    }

def _validate_realism(output_dir: Path, demand_data: dict[str, Any], cfg: dict[str, Any], mode: str) -> None:
    roads = json.loads((output_dir / "roads.geojson").read_text(encoding="utf-8"))
    buildings = json.loads((output_dir / "buildings_index.json").read_text(encoding="utf-8"))
    runways = json.loads((output_dir / "runways_taxiways.geojson").read_text(encoding="utf-8"))
    water_path = output_dir / "water.geojson"
    water = json.loads(water_path.read_text(encoding="utf-8")) if water_path.exists() else {"features": []}
    parks_path = output_dir / "open_space.geojson"
    parks = json.loads(parks_path.read_text(encoding="utf-8")) if parks_path.exists() else {"features": []}
    campuses_path = output_dir / "campuses.geojson"
    campuses = json.loads(campuses_path.read_text(encoding="utf-8")) if campuses_path.exists() else {"features": []}

    road_counts: dict[str, int] = {}
    for f in roads.get("features", []):
        rc = f.get("properties", {}).get("roadClass", "unknown")
        road_counts[rc] = road_counts.get(rc, 0) + 1

    min_expressway = 1 if mode == "dev" else 2
    min_trunk = 2 if mode == "dev" else 4
    min_arterial = 4 if mode == "dev" else 10

    if road_counts.get("expressway", 0) < min_expressway:
        raise RuntimeError(f"realism: insufficient expressways ({road_counts.get('expressway', 0)} < {min_expressway})")
    if road_counts.get("trunk", 0) < min_trunk:
        raise RuntimeError(f"realism: insufficient trunk roads ({road_counts.get('trunk', 0)} < {min_trunk})")
    if road_counts.get("arterial", 0) + road_counts.get("secondary_arterial", 0) < min_arterial:
        raise RuntimeError(f"realism: insufficient arterials")

    sample_road = roads["features"][0]["properties"] if roads["features"] else {}
    for key in ("roadClass", "kind", "kind_detail", "name", "structure"):
        if key not in sample_road:
            raise RuntimeError(f"realism: road features missing property '{key}'")

    bldgs = buildings.get("buildings", [])
    if len(bldgs) < (500 if mode == "dev" else 2000):
        raise RuntimeError(f"realism: too few buildings ({len(bldgs)})")

    floors = [b["f"] for b in bldgs]
    floor_mean = sum(floors) / len(floors)
    floor_var = sum((f - floor_mean)**2 for f in floors) / len(floors)
    if floor_var < 5:
        raise RuntimeError(f"realism: building height variance too low ({floor_var:.1f})")

    dist_counts = buildings.get("stats", {}).get("districtCounts", {})
    active_districts = [k for k, v in dist_counts.items() if v > 0]
    if len(active_districts) < (4 if mode == "dev" else 7):
        raise RuntimeError(f"realism: district mix too shallow ({len(active_districts)} districts)")

    runway_count = sum(1 for f in runways.get("features", [])
                       if f.get("properties", {}).get("roadType") == "runway")
    if mode == "prod" and runway_count < 3:
        raise RuntimeError(f"realism: insufficient runways for prod ({runway_count})")

    if mode == "prod" and len(water.get("features", [])) < 1:
        raise RuntimeError("realism: missing water features for prod")

    if len(parks.get("features", [])) < (1 if mode == "dev" else 3):
        raise RuntimeError("realism: insufficient parks")

    if mode == "prod" and len(campuses.get("features", [])) < 2:
        raise RuntimeError("realism: insufficient campuses for prod")

    bbox = cfg["map"]["bbox"]
    map_cx = (bbox[0] + bbox[2]) / 2
    map_cy = (bbox[1] + bbox[3]) / 2
    core_pts = sum(1 for p in demand_data.get("points", [])
                   if abs(p["location"][0] - map_cx) < (bbox[2] - bbox[0]) * 0.15
                   and abs(p["location"][1] - map_cy) < (bbox[3] - bbox[1]) * 0.15)
    outer_pts = len(demand_data.get("points", [])) - core_pts
    if core_pts <= 0 or outer_pts <= 0:
        raise RuntimeError("realism: demand lacks core/outer balance")

def _validate_prod_dev_diff(repo_root: Path) -> None:
    prod_dir = repo_root / "outputs" / "prod"
    dev_dir = repo_root / "outputs" / "dev"
    paths_needed = [
        prod_dir / "config.json", dev_dir / "config.json",
        prod_dir / "roads.geojson", dev_dir / "roads.geojson",
        prod_dir / "buildings_index.json", dev_dir / "buildings_index.json",
    ]
    if not all(p.exists() for p in paths_needed):
        return

    prod_cfg = json.loads((prod_dir / "config.json").read_text(encoding="utf-8"))
    dev_cfg = json.loads((dev_dir / "config.json").read_text(encoding="utf-8"))

    prod_bbox = prod_cfg.get("bbox", [0, 0, 1, 1])
    dev_bbox = dev_cfg.get("bbox", [0, 0, 1, 1])
    prod_area = max(1e-9, (prod_bbox[2] - prod_bbox[0]) * (prod_bbox[3] - prod_bbox[1]))
    dev_area = max(1e-9, (dev_bbox[2] - dev_bbox[0]) * (dev_bbox[3] - dev_bbox[1]))
    if prod_area / dev_area < 3.0:
        raise RuntimeError("prod/dev: prod bbox not materially larger")

    if prod_cfg.get("population", 0) < dev_cfg.get("population", 0) * 2:
        raise RuntimeError("prod/dev: prod population not materially larger")

    prod_roads = json.loads((prod_dir / "roads.geojson").read_text(encoding="utf-8"))
    dev_roads = json.loads((dev_dir / "roads.geojson").read_text(encoding="utf-8"))
    if len(prod_roads.get("features", [])) < len(dev_roads.get("features", [])) * 1.3:
        raise RuntimeError("prod/dev: prod roads not materially more than dev")

    prod_bldgs = json.loads((prod_dir / "buildings_index.json").read_text(encoding="utf-8"))
    dev_bldgs = json.loads((dev_dir / "buildings_index.json").read_text(encoding="utf-8"))
    if len(prod_bldgs.get("buildings", [])) < len(dev_bldgs.get("buildings", [])) * 1.5:
        raise RuntimeError("prod/dev: prod buildings not materially more than dev")

def validate_outputs(
    output_dir: Path,
    archive_path: Path,
    cfg: dict[str, Any],
    mode: str,
    pmtiles_filename: str,
) -> dict[str, Any]:
    required = [
        output_dir / "config.json", output_dir / "demand_data.json",
        output_dir / "roads.geojson", output_dir / "runways_taxiways.geojson",
        output_dir / "buildings_index.json", output_dir / pmtiles_filename,
        archive_path,
    ]
    for p in required:
        if not p.exists():
            raise RuntimeError(f"Missing required output: {p}")

    demand_data = json.loads((output_dir / "demand_data.json").read_text(encoding="utf-8"))
    demand_summary = validate_demand_integrity(demand_data)
    _validate_realism(output_dir, demand_data, cfg, mode)

    config = json.loads((output_dir / "config.json").read_text(encoding="utf-8"))
    missing_cfg = REQUIRED_CONFIG_KEYS - set(config.keys())
    if missing_cfg:
        raise RuntimeError(f"config.json missing keys: {sorted(missing_cfg)}")
    ivs = config.get("initialViewState", {})
    missing_ivs = REQUIRED_INITIAL_VIEW_KEYS - set(ivs.keys())
    if missing_ivs:
        raise RuntimeError(f"config.json initialViewState missing keys: {sorted(missing_ivs)}")

    pmtiles_path = output_dir / pmtiles_filename
    if pmtiles_path.stat().st_size <= 0:
        raise RuntimeError(f"{pmtiles_filename} is empty")

    subprocess.run(["pmtiles", "verify", str(pmtiles_path)], check=True, capture_output=True)
    show = subprocess.run(["pmtiles", "show", str(pmtiles_path)], check=True, capture_output=True, text=True)
    meta = show.stdout.lower()
    for layer in ["roads", "buildings", "runways", "water", "open_space", "campuses"]:
        if layer not in meta:
            raise RuntimeError(f"PMTiles missing expected layer: {layer}")

    with zipfile.ZipFile(archive_path, "r") as zf:
        names = {i.filename for i in zf.infolist() if not i.is_dir()}
        root_names = {n for n in names if "/" not in n}
        missing_root = REQUIRED_ROOT_FILES - root_names
        if missing_root:
            raise RuntimeError(f"Archive missing root files: {sorted(missing_root)}")
        pmtiles_files = [n for n in root_names if n.endswith(".pmtiles")]
        if len(pmtiles_files) != 1:
            raise RuntimeError(f"Archive must have exactly one .pmtiles; found {len(pmtiles_files)}")

    if mode == "prod":
        _validate_prod_dev_diff(output_dir.parents[1])

    return demand_summary

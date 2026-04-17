from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .build_pmtiles import build_pmtiles
from .generate_raw import generate_buildings_index, generate_demand_data, generate_roads, generate_runways
from .package_map import package_map
from .utils import end_stage, ensure_dir, start_stage, write_json
from .validation import validate_outputs


def _load_config(config_path: Path) -> dict[str, Any]:
    # Config files are JSON-compatible YAML for zero-dependency parsing.
    return json.loads(config_path.read_text(encoding="utf-8"))


def _validate_map_code(code: str) -> None:
    if code != "BSS":
        raise RuntimeError("map code must be exactly BSS")


def _build_config_json(cfg: dict[str, Any], demand_data: dict[str, Any]) -> dict[str, Any]:
    map_cfg = cfg["map"]
    population = sum(int(p["size"]) for p in demand_data["pops"])

    return {
        "name": map_cfg["name"],
        "code": map_cfg["code"],
        "description": map_cfg["description"],
        "population": population,
        "creator": map_cfg["creator"],
        "version": map_cfg["version"],
        "bbox": map_cfg["bbox"],
        "thumbnailBbox": map_cfg["thumbnailBbox"],
        "initialViewState": map_cfg["initialViewState"],
    }


def run_build(mode: str, clean: bool = False) -> tuple[Path, Path]:
    config_path = Path("config") / ("prod.yaml" if mode == "prod" else "dev.yaml")
    cfg = _load_config(config_path)

    _validate_map_code(cfg["map"]["code"])

    output_dir = Path(cfg["build"]["output_dir"])
    ensure_dir(output_dir)

    if clean:
        for filename in [
            "roads.geojson",
            "runways_taxiways.geojson",
            "buildings_index.json",
            "demand_data.json",
            "config.json",
            "map.pmtiles",
            cfg["build"]["package_name"],
        ]:
            file_path = output_dir / filename
            if file_path.exists():
                file_path.unlink()

    t = start_stage("generate essential raw outputs")
    generate_roads(cfg, output_dir / "roads.geojson")
    generate_runways(cfg, output_dir / "runways_taxiways.geojson")
    buildings = generate_buildings_index(cfg, output_dir / "buildings_index.json")
    demand_data = generate_demand_data(cfg, buildings, output_dir / "demand_data.json")
    end_stage(t)

    t = start_stage("generate config.json")
    config_json = _build_config_json(cfg, demand_data)
    write_json(output_dir / "config.json", config_json)
    end_stage(t)

    t = start_stage("build minimal PMTiles")
    build_pmtiles(cfg, output_dir)
    end_stage(t)

    t = start_stage("package final import archive")
    archive_path = package_map(output_dir, cfg["build"]["package_name"])
    end_stage(t)

    t = start_stage("validate outputs and archive contract")
    validate_outputs(output_dir, archive_path)
    end_stage(t)

    print(f"[result] output directory: {output_dir}")
    print(f"[result] import archive: {archive_path}")
    return output_dir, archive_path

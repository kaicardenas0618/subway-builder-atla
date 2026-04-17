from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path


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


def validate_outputs(output_dir: Path, archive_path: Path) -> None:
    required_paths = [
        output_dir / "config.json",
        output_dir / "demand_data.json",
        output_dir / "roads.geojson",
        output_dir / "runways_taxiways.geojson",
        output_dir / "buildings_index.json",
        output_dir / "map.pmtiles",
        archive_path,
    ]
    for path in required_paths:
        if not path.exists():
            raise RuntimeError(f"Missing required output: {path}")

    cfg = json.loads((output_dir / "config.json").read_text(encoding="utf-8"))
    missing_cfg = REQUIRED_CONFIG_KEYS.difference(cfg.keys())
    if missing_cfg:
        raise RuntimeError(f"config.json missing keys: {sorted(missing_cfg)}")

    ivs = cfg.get("initialViewState", {})
    missing_ivs = REQUIRED_INITIAL_VIEW_KEYS.difference(ivs.keys())
    if missing_ivs:
        raise RuntimeError(f"config.json initialViewState missing keys: {sorted(missing_ivs)}")

    pmtiles_path = output_dir / "map.pmtiles"
    if pmtiles_path.stat().st_size <= 0:
        raise RuntimeError("map.pmtiles is empty")

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

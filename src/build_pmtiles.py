from __future__ import annotations

import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from .utils import file_size_mb


def build_pmtiles(cfg: dict[str, Any], output_dir: Path) -> Path:
    roads_path = output_dir / "roads.geojson"
    runways_path = output_dir / "runways_taxiways.geojson"
    buildings_path = output_dir / "buildings_index.json"
    water_path = output_dir / "water.geojson"
    open_space_path = output_dir / "open_space.geojson"
    campuses_path = output_dir / "campuses.geojson"
    pmtiles_filename = f"{cfg['map']['code']}.pmtiles"
    pmtiles_path = output_dir / pmtiles_filename

    inputs = [roads_path, runways_path, buildings_path]
    if water_path.exists():
        inputs.append(water_path)
    if open_space_path.exists():
        inputs.append(open_space_path)
    if campuses_path.exists():
        inputs.append(campuses_path)

    newest_input = max(p.stat().st_mtime for p in inputs)
    if pmtiles_path.exists() and pmtiles_path.stat().st_mtime >= newest_input:
        print(f"[pmtiles] up-to-date: {pmtiles_path}")
        return pmtiles_path

    with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False, encoding="utf-8") as tmp:
        tmp_path = Path(tmp.name)

    try:
        buildings_data = json.loads(buildings_path.read_text(encoding="utf-8"))
        building_features = []
        for idx, building in enumerate(buildings_data["buildings"]):
            building_features.append(
                {
                    "type": "Feature",
                    "properties": {"id": idx, "floors": building["f"]},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": building["p"],
                    },
                }
            )

        tmp_path.write_text(
            json.dumps({"type": "FeatureCollection", "features": building_features}),
            encoding="utf-8",
        )

        minzoom = str(int(cfg["build"]["pmtiles_minzoom"]))
        maxzoom = str(int(cfg["build"]["pmtiles_maxzoom"]))

        cmd = [
            "tippecanoe",
            "-f",
            "-o",
            str(pmtiles_path),
            "-Z",
            minzoom,
            "-z",
            maxzoom,
            "--coalesce-densest-as-needed",
            "--extend-zooms-if-still-dropping",
            "--no-line-simplification",
            "-L",
            f"roads:{roads_path}",
            "-L",
            f"buildings:{tmp_path}",
            "-L",
            f"runways:{runways_path}",
        ]

        if water_path.exists():
            cmd += ["-L", f"water:{water_path}"]
        if open_space_path.exists():
            cmd += ["-L", f"open_space:{open_space_path}"]
        if campuses_path.exists():
            cmd += ["-L", f"campuses:{campuses_path}"]

        start = time.time()
        subprocess.run(cmd, check=True)
        elapsed = max(0.001, time.time() - start)
        size_mb = file_size_mb(pmtiles_path)
        growth_rate = size_mb / elapsed
        print(
            "[pmtiles] complete "
            f"elapsed={elapsed:.1f}s size={size_mb:.2f}MB avg_growth={growth_rate:.2f}MB/s"
        )

    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    return pmtiles_path

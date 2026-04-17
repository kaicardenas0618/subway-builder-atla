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

    buildings_data = json.loads(buildings_path.read_text(encoding="utf-8"))

    generalized_features = []
    detailed_features = []
    for idx, building in enumerate(buildings_data["buildings"]):
        props = {"id": idx, "floors": building["f"]}
        feat = {
            "type": "Feature",
            "properties": props,
            "geometry": {"type": "Polygon", "coordinates": building["p"]},
        }
        detailed_features.append(feat)
        if building["f"] >= 5:
            generalized_features.append(feat)

    roads_data = json.loads(roads_path.read_text(encoding="utf-8"))
    major_road_classes = {"expressway", "trunk", "arterial"}
    major_roads = [f for f in roads_data.get("features", [])
                   if f.get("properties", {}).get("roadClass") in major_road_classes]
    all_roads = roads_data.get("features", [])

    tmp_dir = Path(tempfile.mkdtemp())
    try:
        buildings_detail_path = tmp_dir / "buildings_detail.geojson"
        buildings_detail_path.write_text(
            json.dumps({"type": "FeatureCollection", "features": detailed_features}),
            encoding="utf-8")

        buildings_gen_path = tmp_dir / "buildings_gen.geojson"
        buildings_gen_path.write_text(
            json.dumps({"type": "FeatureCollection", "features": generalized_features}),
            encoding="utf-8")

        major_roads_path = tmp_dir / "major_roads.geojson"
        major_roads_path.write_text(
            json.dumps({"type": "FeatureCollection", "features": major_roads}),
            encoding="utf-8")

        all_roads_path = tmp_dir / "all_roads.geojson"
        all_roads_path.write_text(
            json.dumps({"type": "FeatureCollection", "features": all_roads}),
            encoding="utf-8")

        minzoom = str(int(cfg["build"]["pmtiles_minzoom"]))
        maxzoom = str(int(cfg["build"]["pmtiles_maxzoom"]))

        cmd = [
            "tippecanoe",
            "-f",
            "-o", str(pmtiles_path),
            "-Z", minzoom,
            "-z", maxzoom,
            "--no-line-simplification",
            "--no-tile-size-limit",
            "--extend-zooms-if-still-dropping",
            "-L", json.dumps({"file": str(major_roads_path), "layer": "roads",
                              "minzoom": int(minzoom), "maxzoom": int(maxzoom)}),
            "-L", json.dumps({"file": str(all_roads_path), "layer": "roads_detail",
                              "minzoom": min(int(maxzoom), max(10, int(minzoom) + 1)),
                              "maxzoom": int(maxzoom)}),
            "-L", json.dumps({"file": str(buildings_gen_path), "layer": "buildings",
                              "minzoom": int(minzoom), "maxzoom": int(maxzoom)}),
            "-L", json.dumps({"file": str(buildings_detail_path), "layer": "buildings_detail",
                              "minzoom": min(int(maxzoom), max(12, int(minzoom) + 2)),
                              "maxzoom": int(maxzoom)}),
            "-L", f"runways:{runways_path}",
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
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return pmtiles_path

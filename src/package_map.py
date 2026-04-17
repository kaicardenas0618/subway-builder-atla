from __future__ import annotations

import zipfile
from pathlib import Path


ARCHIVE_FILES = [
    "config.json",
    "demand_data.json",
    "roads.geojson",
    "runways_taxiways.geojson",
    "buildings_index.json",
]


def package_map(output_dir: Path, package_name: str, pmtiles_filename: str) -> Path:
    archive_path = output_dir / package_name
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in [*ARCHIVE_FILES, pmtiles_filename]:
            file_path = output_dir / name
            zf.write(file_path, arcname=name)
    return archive_path

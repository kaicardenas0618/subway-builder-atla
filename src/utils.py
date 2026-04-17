from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_ROOT_FILES = {
    "config.json",
    "demand_data.json",
    "roads.geojson",
    "runways_taxiways.geojson",
    "buildings_index.json",
}

@dataclass
class StageTimer:
    name: str
    start: float

def start_stage(name: str) -> StageTimer:
    print(f"[stage] {name}...")
    return StageTimer(name=name, start=time.time())

def end_stage(timer: StageTimer) -> None:
    elapsed = time.time() - timer.start
    print(f"[done]  {timer.name} ({elapsed:.1f}s)")

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def file_size_mb(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)

def env_port(default: int | None = None) -> int | None:
    raw = os.environ.get("PORT")
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default

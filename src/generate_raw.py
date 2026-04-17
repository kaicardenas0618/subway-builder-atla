from __future__ import annotations

from pathlib import Path
from typing import Any

from .airports import generate_runways_taxiways
from .buildings import generate_buildings_index as generate_buildings_index_impl
from .campuses import generate_campuses
from .city_layout import build_city_layout
from .demand import generate_demand
from .features import generate_open_spaces, generate_water
from .roads import generate_roads as generate_roads_impl
from .utils import write_json


def generate_roads(cfg: dict[str, Any], out_path: Path) -> dict[str, Any]:
    layout = build_city_layout(cfg)
    geo = generate_roads_impl(layout, cfg)
    write_json(out_path, geo)
    return geo


def generate_runways(cfg: dict[str, Any], out_path: Path) -> dict[str, Any]:
    layout = build_city_layout(cfg)
    geo = generate_runways_taxiways(layout, cfg["map"]["bbox"])
    write_json(out_path, geo)
    return geo


def generate_context_layers(cfg: dict[str, Any], output_dir: Path) -> None:
    layout = build_city_layout(cfg)
    water = generate_water(layout, cfg["map"]["bbox"])
    open_space = generate_open_spaces(layout, cfg["map"]["bbox"])
    campuses = generate_campuses(layout, cfg["map"]["bbox"])
    write_json(output_dir / "water.geojson", water)
    write_json(output_dir / "open_space.geojson", open_space)
    write_json(output_dir / "campuses.geojson", campuses)


def generate_buildings_index(cfg: dict[str, Any], out_path: Path) -> dict[str, Any]:
    layout = build_city_layout(cfg)
    b = generate_buildings_index_impl(layout, cfg)
    write_json(out_path, b)
    return b


def generate_demand_data(cfg: dict[str, Any], buildings_index: dict[str, Any], out_path: Path) -> dict[str, Any]:
    layout = build_city_layout(cfg)
    d = generate_demand(layout, cfg, buildings_index)
    write_json(out_path, d)
    return d

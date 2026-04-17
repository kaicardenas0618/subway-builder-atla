# Avatar: The Last Airbender Subway Builder Maps

This repository contains the pipeline for generating Avatar: The Last Airbender maps for Subway Builder.

Current maps in this repository:
- Ba Sing Se

## Make Commands

- `make prod`: full production map build
- `make dev`: small production-ready downtown/core build
- `make serve`: serve `debug_map.html` and existing outputs (no rebuild)

## What `make prod` Does

1. Generates required raw files:
   - `roads.geojson`
   - `runways_taxiways.geojson`
   - `buildings_index.json`
   - `demand_data.json`
2. Generates `config.json`
3. Builds `map.pmtiles`
4. Packages all required root-level files into the final import archive
5. Validates files, PMTiles readability, and archive contract

Output location:
- `outputs/prod/`
- final archive: `outputs/prod/BS1-prod.zip`

## What `make dev` Does

Builds a smaller, denser downtown/core slice with the same essential contract and packaging behavior as production.

Output location:
- `outputs/dev/`
- final archive: `outputs/dev/BS1-dev.zip`

## Debug Viewer

- canonical page: `debug_map.html`
- run with: `make serve`
- URL is printed by the server (auto-selects a free port unless `PORT` or `--port` is set)

The debug page checks byte-range support, loads generated PMTiles, and overlays useful raw layers for quick inspection.

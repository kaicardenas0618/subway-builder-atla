# Avatar: The Last Airbender Subway Builder Maps

Current city: Ba Sing Se.

This repository generates a realism-driven, synthetic, Ba Sing Se-inspired megacity while preserving a stable game import/load package path.

## Public Workflow

- `make prod`: full Ba Sing Se megacity build
- `make dev`: CBD/core slice of the same city logic
- `make serve`: static debug viewer for already-built outputs

Both prod and dev are production-compatible and importable.

## Outputs

Each build writes:

- `roads.geojson`
- `runways_taxiways.geojson`
- `buildings_index.json`
- `demand_data.json`
- `<map_code>.pmtiles` (currently `BSS.pmtiles`)
- `config.json`
- importable archive

Archive paths:

- prod: `outputs/prod/BSS-prod.zip`
- dev: `outputs/dev/BSS-dev.zip`

## Generation Model

- City is synthetic (no real Census/LODES input).
- Macro form follows a modernized Ba Sing Se logic: ring corridors, radial spines, layered districts, core intensity, airports, campuses, parks, and lake/water edge.
- Roads use hierarchical classes: expressway, trunk, arterial, collector, local.
- Buildings are generated from district-aware blocks and parcels (not a single global row/column lattice).
- Demand is synthetic mesozone-level OD with strict referential integrity validation.

## LODES Reference Policy

`reference/create_US_demand_file.py` is used only as a schema/modeling reference for demand structure and integrity discipline.
No real-world LODES/Census pipeline is used as input.

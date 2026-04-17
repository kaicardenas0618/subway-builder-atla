# Avatar: The Last Airbender Subway Builder Maps

Current map build in this repository: Ba Sing Se.

This project generates importable game map packages with a synthetic city and synthetic demand model.

## Public Workflow

- `make prod`: full metropolitan Ba Sing Se build
- `make dev`: realistic CBD/core slice build
- `make serve`: serve `debug_map.html` and existing outputs without rebuilding

Both `prod` and `dev` generate production-compatible, importable map archives.

## Outputs

For both modes, the pipeline produces:

- `roads.geojson`
- `runways_taxiways.geojson`
- `buildings_index.json`
- `demand_data.json`
- `<map_code>.pmtiles` (currently `BSS.pmtiles`)
- `config.json`
- final archive zip

Archive paths:

- prod: `outputs/prod/BSS-prod.zip`
- dev: `outputs/dev/BSS-dev.zip`

## Demand Model

Demand generation is synthetic and deterministic from generated city geometry.

- No real LODES input is used.
- No Census dependency is used.
- `reference/create_US_demand_file.py` is used only as a schema/modeling reference for:
  - `points` / `pops` structure
  - referential integrity discipline
  - aggregated home-work cohort pattern

## Validation

Builds fail on demand integrity issues (duplicate IDs, dangling residence/job references, orphan pop links, malformed travel metrics) and on core contract violations.

Additional sanity checks validate:

- road hierarchy presence
- building height and footprint variability
- core-vs-outer demand distribution
- prod/dev material differentiation (area, population, roads, buildings)

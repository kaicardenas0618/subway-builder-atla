# Avatar: The Last Airbender Subway Builder Maps

Current city: Ba Sing Se.

Generates a realism-driven synthetic Ba Sing Se-inspired megacity with working game import/load path.

## Public Workflow

- `make prod` — full Ba Sing Se megacity build
- `make dev` — CBD/core clip of the same city logic
- `make serve` — static debug viewer for built outputs

## Architecture

The generator pipeline follows 10 stages:

1. **Macro city plan** (`city_plan.py`) — concentric rings, CBD crescent, lake, airports, campuses, parks, industrial/logistics belts, secondary centers
2. **District classification** (`districts_new.py`) — spatial lookup classifying any coordinate into one of 14+ district types
3. **Primary mobility skeleton** (`roads_new.py`) — ring expressways, radial arterials, cross-city connectors
4. **District street fabrics** (`roads_new.py`) — historic irregular, CBD orthogonal, offset grids, superblocks, campus loops, airport perimeters
5. **Blocks** (`blocks_new.py`) — district-density-seeded block generation (NOT a rows/cols lattice)
6. **Parcels** (`parcels_new.py`) — block subdivision by district type
7. **Buildings** (`buildings_new.py`) — parcel-driven footprints with district typologies (courtyard, podium+tower, L-shape, slab, plate)
8. **Demand zones** (`demand_new.py`) — mesozone-level aggregation from building stock
9. **Demand flows** (`demand_new.py`) — gravity-model OD with variable lognormal cohort sizes
10. **PMTiles export** (`build_pmtiles.py`) — multi-scale tile strategy with major/detail road layers and generalized/detailed building layers

## Key Design Decisions

- Historic core is low-rise (ceremonial/institutional); CBD crescent holds the tallest skyline
- Roads carry rich properties: `roadClass`, `kind`, `kind_detail`, `name`, `structure`, `bridge`, `tunnel`, `oneway`
- Buildings use non-rectangular footprints (U-shape courtyards, L-shapes, podium+tower)
- Demand pop cohorts use capped lognormal sizes, not uniform splitting
- Dev is a spatial clip of the same city logic, not a separate mini-generator
- PMTiles use `--no-tile-size-limit` with multi-layer zoom-range strategy for readable city at all scales

## Outputs

- `roads.geojson`, `runways_taxiways.geojson`, `buildings_index.json`, `demand_data.json`
- `BSS.pmtiles` (multi-scale vector tiles)
- `config.json`
- Import archive: `BSS-prod.zip` / `BSS-dev.zip`

# Product spec

This repo builds fictional city map packages for the game.

Public workflow only:
- make all
- make dev
- make serve

make all:
- build full production-ready city
- produce required raw files
- produce map.pmtiles
- produce config.json
- produce final importable zip

make dev:
- build small downtown/core segment
- still importable in-game
- still realistic enough to test density, roads, buildings, and demand
- must finish in a few minutes

make serve:
- serve static debug_map.html
- serve outputs
- support PMTiles byte ranges
- do not rebuild anything

Essential outputs:
- roads.geojson
- runways_taxiways.geojson
- buildings_index.json
- demand_data.json
- map.pmtiles
- config.json
- final importable zip

Important:
- use reference/working_map/ as the file-shape source of truth
- use reference/game_contract/ as the import contract source of truth
- do not copy old repo code
- do not add extra workflows
- get import/load working before adding nonessential layers like landuse/water

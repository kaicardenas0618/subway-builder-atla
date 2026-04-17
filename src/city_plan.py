from __future__ import annotations

from typing import Any

def build_city_plan(cfg: dict[str, Any]) -> dict[str, Any]:
    min_x, min_y, max_x, max_y = cfg["map"]["bbox"]

    metro_bbox = [112.82, 39.60, 113.66, 40.20]
    mx0, my0, mx1, my1 = metro_bbox
    mcx = (mx0 + mx1) / 2
    mcy = (my0 + my1) / 2
    mw = mx1 - mx0
    mh = my1 - my0

    ring_radii_frac = [0.10, 0.22, 0.38, 0.56]
    ring_radii_deg = [r * mw / 2 for r in ring_radii_frac]

    cbd_crescent = {
        "center": [mcx + 0.06 * mw, mcy + 0.035 * mh],
        "rx": 0.08 * mw,
        "ry": 0.055 * mh,
        "angle": 0.35,
    }

    secondary_centers = [
        {"name": "Western Gate Hub", "center": [mcx - 0.22 * mw, mcy + 0.04 * mh], "radius": 0.035},
        {"name": "Southern Cross Hub", "center": [mcx + 0.02 * mw, mcy - 0.24 * mh], "radius": 0.030},
        {"name": "Northern Terrace Hub", "center": [mcx - 0.04 * mw, mcy + 0.26 * mh], "radius": 0.028},
        {"name": "Eastshore Transit Center", "center": [mcx + 0.18 * mw, mcy + 0.15 * mh], "radius": 0.025},
        {"name": "Jade Gate Junction", "center": [mcx - 0.15 * mw, mcy - 0.12 * mh], "radius": 0.022},
        {"name": "Outer Wall Market District", "center": [mcx + 0.30 * mw, mcy - 0.05 * mh], "radius": 0.026},
        {"name": "North Plains Center", "center": [mcx + 0.08 * mw, mcy + 0.32 * mh], "radius": 0.020},
        {"name": "Ring Road Interchange Hub", "center": [mcx - 0.30 * mw, mcy + 0.18 * mh], "radius": 0.024},
        {"name": "Agrarian Quarter Center", "center": [mcx + 0.25 * mw, mcy + 0.28 * mh], "radius": 0.018},
        {"name": "Southwest Commerce Park", "center": [mcx - 0.20 * mw, mcy - 0.26 * mh], "radius": 0.021},
        {"name": "Canal District Hub", "center": [mcx + 0.12 * mw, mcy - 0.18 * mh], "radius": 0.019},
        {"name": "Serpent's Pass Gateway", "center": [mcx + 0.32 * mw, mcy + 0.18 * mh], "radius": 0.017},
        {"name": "Wall Garrison Town", "center": [mcx - 0.34 * mw, mcy - 0.02 * mh], "radius": 0.020},
        {"name": "Midring Bazaar", "center": [mcx + 0.02 * mw, mcy + 0.16 * mh], "radius": 0.016},
        {"name": "Lakeview Terrace Hub", "center": [mcx + 0.20 * mw, mcy + 0.06 * mh], "radius": 0.018},
        {"name": "South Gate Crossing", "center": [mcx - 0.06 * mw, mcy - 0.30 * mh], "radius": 0.019},
        {"name": "Ironworks Junction", "center": [mcx - 0.26 * mw, mcy - 0.14 * mh], "radius": 0.016},
        {"name": "Eastern Farmstead Center", "center": [mcx + 0.34 * mw, mcy + 0.02 * mh], "radius": 0.015},
        {"name": "Twilight Market Hub", "center": [mcx - 0.10 * mw, mcy + 0.30 * mh], "radius": 0.017},
        {"name": "Refugee Quarter Center", "center": [mcx + 0.14 * mw, mcy - 0.28 * mh], "radius": 0.016},
    ]

    lake = {
        "center": [mcx + 0.28 * mw, mcy + 0.10 * mh],
        "rx": 0.11 * mw,
        "ry": 0.09 * mh,
        "name": "Lake Laogai",
    }

    river_segments = [
        [[mcx + 0.20 * mw, mcy + 0.18 * mh], [mcx + 0.18 * mw, mcy + 0.30 * mh]],
        [[mcx + 0.28 * mw, mcy + 0.01 * mh], [mcx + 0.32 * mw, mcy - 0.15 * mh]],
        [[mcx - 0.05 * mw, mcy + 0.35 * mh], [mcx + 0.10 * mw, mcy + 0.38 * mh]],
        [[mcx - 0.20 * mw, mcy + 0.10 * mh], [mcx - 0.30 * mw, mcy + 0.25 * mh]],
    ]

    primary_airport = {
        "name": "Upper Ring International",
        "center": [mcx + 0.26 * mw, mcy - 0.22 * mh],
        "angle": -0.40,
        "runways": 3,
        "size_x": 0.10 * mw,
        "size_y": 0.06 * mh,
    }
    secondary_airport = {
        "name": "West Wall Regional",
        "center": [mcx - 0.28 * mw, mcy - 0.10 * mh],
        "angle": 0.28,
        "runways": 2,
        "size_x": 0.07 * mw,
        "size_y": 0.04 * mh,
    }

    campuses = [
        {"name": "Ba Sing Se Royal University", "center": [mcx + 0.09 * mw, mcy + 0.14 * mh], "radius": 0.032},
        {"name": "Eastern Academy of Arts", "center": [mcx + 0.19 * mw, mcy + 0.04 * mh], "radius": 0.024},
        {"name": "Wall District Polytechnic", "center": [mcx - 0.13 * mw, mcy + 0.09 * mh], "radius": 0.025},
        {"name": "Southern Agricultural Institute", "center": [mcx + 0.04 * mw, mcy - 0.17 * mh], "radius": 0.020},
        {"name": "Imperial War College", "center": [mcx - 0.02 * mw, mcy + 0.05 * mh], "radius": 0.016},
        {"name": "Laogai Research Center", "center": [mcx + 0.22 * mw, mcy + 0.14 * mh], "radius": 0.014},
        {"name": "Northern Medical Academy", "center": [mcx - 0.06 * mw, mcy + 0.22 * mh], "radius": 0.018},
        {"name": "Earth Rumble Training Grounds", "center": [mcx + 0.14 * mw, mcy - 0.08 * mh], "radius": 0.012},
        {"name": "Outer Wall Military Academy", "center": [mcx - 0.30 * mw, mcy + 0.04 * mh], "radius": 0.015},
        {"name": "Inner Ring Conservatory", "center": [mcx + 0.03 * mw, mcy + 0.10 * mh], "radius": 0.010},
        {"name": "Agrarian Sciences Campus", "center": [mcx + 0.20 * mw, mcy + 0.26 * mh], "radius": 0.019},
        {"name": "Canal District Trade School", "center": [mcx + 0.10 * mw, mcy - 0.14 * mh], "radius": 0.011},
        {"name": "Western Seminary", "center": [mcx - 0.18 * mw, mcy + 0.16 * mh], "radius": 0.013},
        {"name": "Dai Li Academy", "center": [mcx + 0.01 * mw, mcy + 0.02 * mh], "radius": 0.009},
        {"name": "Earthbending University", "center": [mcx - 0.08 * mw, mcy - 0.06 * mh], "radius": 0.017},
        {"name": "Southwest Technical College", "center": [mcx - 0.22 * mw, mcy - 0.20 * mh], "radius": 0.013},
        {"name": "Lakeside Liberal Arts College", "center": [mcx + 0.16 * mw, mcy + 0.12 * mh], "radius": 0.010},
        {"name": "Ring Road Vocational Institute", "center": [mcx - 0.16 * mw, mcy - 0.04 * mh], "radius": 0.011},
        {"name": "Northern Plains Research Park", "center": [mcx + 0.06 * mw, mcy + 0.30 * mh], "radius": 0.016},
        {"name": "Eastern Gate Divinity School", "center": [mcx + 0.28 * mw, mcy + 0.00 * mh], "radius": 0.008},
        {"name": "Refugee Quarter Community College", "center": [mcx + 0.12 * mw, mcy - 0.24 * mh], "radius": 0.012},
        {"name": "South Wall Engineering School", "center": [mcx - 0.04 * mw, mcy - 0.28 * mh], "radius": 0.011},
    ]

    parks = [
        {"name": "Imperial Green", "center": [mcx, mcy + 0.01 * mh], "rx": 0.018 * mw, "ry": 0.022 * mh, "kind": "ceremonial_park"},
        {"name": "Outer Promenade", "center": [mcx - 0.17 * mw, mcy + 0.19 * mh], "rx": 0.025 * mw, "ry": 0.018 * mh, "kind": "park"},
        {"name": "Canal Gardens", "center": [mcx + 0.16 * mw, mcy + 0.24 * mh], "rx": 0.020 * mw, "ry": 0.016 * mh, "kind": "park"},
        {"name": "Victory Square", "center": [mcx - 0.04 * mw, mcy - 0.05 * mh], "rx": 0.010 * mw, "ry": 0.012 * mh, "kind": "square"},
        {"name": "Serpent's Pass Memorial", "center": [mcx + 0.22 * mw, mcy + 0.22 * mh], "rx": 0.015 * mw, "ry": 0.015 * mh, "kind": "park"},
        {"name": "Northern Forest Reserve", "center": [mcx - 0.10 * mw, mcy + 0.30 * mh], "rx": 0.035 * mw, "ry": 0.028 * mh, "kind": "forest"},
        {"name": "Inner Wall Botanical", "center": [mcx + 0.04 * mw, mcy + 0.08 * mh], "rx": 0.012 * mw, "ry": 0.010 * mh, "kind": "garden"},
        {"name": "Lakefront Esplanade", "center": [mcx + 0.18 * mw, mcy + 0.12 * mh], "rx": 0.018 * mw, "ry": 0.008 * mh, "kind": "waterfront"},
        {"name": "Western Gate Park", "center": [mcx - 0.25 * mw, mcy + 0.06 * mh], "rx": 0.022 * mw, "ry": 0.020 * mh, "kind": "park"},
        {"name": "South Ring Sports Complex", "center": [mcx + 0.10 * mw, mcy - 0.14 * mh], "rx": 0.016 * mw, "ry": 0.014 * mh, "kind": "sports"},
        {"name": "Earth King's Menagerie", "center": [mcx + 0.02 * mw, mcy + 0.04 * mh], "rx": 0.008 * mw, "ry": 0.007 * mh, "kind": "garden"},
        {"name": "Jade Dragon Arboretum", "center": [mcx - 0.08 * mw, mcy + 0.14 * mh], "rx": 0.014 * mw, "ry": 0.012 * mh, "kind": "garden"},
        {"name": "Outer Wall Greenway", "center": [mcx + 0.32 * mw, mcy + 0.10 * mh], "rx": 0.030 * mw, "ry": 0.008 * mh, "kind": "greenway"},
        {"name": "Refugee Memorial Park", "center": [mcx + 0.12 * mw, mcy - 0.22 * mh], "rx": 0.010 * mw, "ry": 0.009 * mh, "kind": "memorial"},
        {"name": "Ring Road Linear Park", "center": [mcx - 0.14 * mw, mcy - 0.08 * mh], "rx": 0.025 * mw, "ry": 0.005 * mh, "kind": "greenway"},
        {"name": "Iroh's Tea Garden", "center": [mcx + 0.06 * mw, mcy + 0.02 * mh], "rx": 0.005 * mw, "ry": 0.005 * mh, "kind": "garden"},
        {"name": "Great Wall Vista Point", "center": [mcx - 0.36 * mw, mcy + 0.12 * mh], "rx": 0.008 * mw, "ry": 0.012 * mh, "kind": "overlook"},
        {"name": "Northeast Wetlands Reserve", "center": [mcx + 0.26 * mw, mcy + 0.28 * mh], "rx": 0.020 * mw, "ry": 0.025 * mh, "kind": "wetland"},
        {"name": "Badgermole Sanctuary", "center": [mcx - 0.20 * mw, mcy + 0.28 * mh], "rx": 0.018 * mw, "ry": 0.022 * mh, "kind": "nature_reserve"},
        {"name": "Midring Plaza", "center": [mcx - 0.02 * mw, mcy + 0.12 * mh], "rx": 0.006 * mw, "ry": 0.006 * mh, "kind": "square"},
        {"name": "South Gate Cemetery", "center": [mcx - 0.08 * mw, mcy - 0.26 * mh], "rx": 0.012 * mw, "ry": 0.010 * mh, "kind": "cemetery"},
        {"name": "Eastern Terraces", "center": [mcx + 0.30 * mw, mcy + 0.16 * mh], "rx": 0.010 * mw, "ry": 0.014 * mh, "kind": "park"},
        {"name": "Firelight Festival Grounds", "center": [mcx + 0.08 * mw, mcy - 0.04 * mh], "rx": 0.009 * mw, "ry": 0.008 * mh, "kind": "fairground"},
        {"name": "Wall Shadow Forest", "center": [mcx - 0.32 * mw, mcy - 0.16 * mh], "rx": 0.028 * mw, "ry": 0.020 * mh, "kind": "forest"},
        {"name": "Northern Reservoir Park", "center": [mcx + 0.04 * mw, mcy + 0.34 * mh], "rx": 0.016 * mw, "ry": 0.012 * mh, "kind": "park"},
        {"name": "Silk Road Pocket Garden", "center": [mcx + 0.14 * mw, mcy + 0.08 * mh], "rx": 0.004 * mw, "ry": 0.004 * mh, "kind": "garden"},
    ]

    industrial_zones = [
        {"name": "Western Industrial Belt", "center": [mcx - 0.30 * mw, mcy - 0.04 * mh], "rx": 0.08 * mw, "ry": 0.10 * mh},
        {"name": "Southern Freight District", "center": [mcx - 0.08 * mw, mcy - 0.28 * mh], "rx": 0.10 * mw, "ry": 0.06 * mh},
        {"name": "Ironworks Quarter", "center": [mcx - 0.24 * mw, mcy - 0.16 * mh], "rx": 0.05 * mw, "ry": 0.04 * mh},
        {"name": "Eastern Smelting Works", "center": [mcx + 0.30 * mw, mcy - 0.12 * mh], "rx": 0.04 * mw, "ry": 0.05 * mh},
        {"name": "Outer Wall Foundries", "center": [mcx - 0.34 * mw, mcy + 0.08 * mh], "rx": 0.04 * mw, "ry": 0.06 * mh},
        {"name": "South Ring Manufacturing", "center": [mcx + 0.06 * mw, mcy - 0.32 * mh], "rx": 0.06 * mw, "ry": 0.04 * mh},
        {"name": "Earthen Pipe Works", "center": [mcx - 0.18 * mw, mcy - 0.22 * mh], "rx": 0.03 * mw, "ry": 0.03 * mh},
        {"name": "Northern Kiln District", "center": [mcx + 0.14 * mw, mcy + 0.32 * mh], "rx": 0.04 * mw, "ry": 0.03 * mh},
        {"name": "Stone Quarry Zone", "center": [mcx - 0.36 * mw, mcy - 0.10 * mh], "rx": 0.03 * mw, "ry": 0.04 * mh},
        {"name": "Tannery Row", "center": [mcx + 0.22 * mw, mcy - 0.28 * mh], "rx": 0.03 * mw, "ry": 0.02 * mh},
        {"name": "Metalworkers' Yard", "center": [mcx - 0.14 * mw, mcy + 0.24 * mh], "rx": 0.02 * mw, "ry": 0.03 * mh},
        {"name": "Powder Mill Precinct", "center": [mcx + 0.34 * mw, mcy - 0.04 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Textile Mills", "center": [mcx - 0.26 * mw, mcy + 0.20 * mh], "rx": 0.03 * mw, "ry": 0.02 * mh},
        {"name": "Ceramics District", "center": [mcx + 0.08 * mw, mcy - 0.26 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Southwest Brickworks", "center": [mcx - 0.22 * mw, mcy - 0.30 * mh], "rx": 0.03 * mw, "ry": 0.02 * mh},
        {"name": "Dye Works Compound", "center": [mcx + 0.26 * mw, mcy + 0.30 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Lumber Processing Yard", "center": [mcx - 0.32 * mw, mcy + 0.22 * mh], "rx": 0.03 * mw, "ry": 0.03 * mh},
        {"name": "Coal Gasification Plant", "center": [mcx + 0.18 * mw, mcy - 0.32 * mh], "rx": 0.02 * mw, "ry": 0.03 * mh},
        {"name": "Paper Mill Quarter", "center": [mcx - 0.10 * mw, mcy - 0.34 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Eastern Shipyard", "center": [mcx + 0.36 * mw, mcy + 0.06 * mh], "rx": 0.03 * mw, "ry": 0.02 * mh},
    ]

    logistics_zones = [
        {"name": "Airport Logistics Park", "center": [mcx + 0.22 * mw, mcy - 0.16 * mh], "rx": 0.06 * mw, "ry": 0.05 * mh},
        {"name": "Western Depot", "center": [mcx - 0.20 * mw, mcy - 0.18 * mh], "rx": 0.05 * mw, "ry": 0.04 * mh},
        {"name": "Great Wall Gate Depot", "center": [mcx - 0.36 * mw, mcy + 0.00 * mh], "rx": 0.04 * mw, "ry": 0.03 * mh},
        {"name": "Northern Granary Complex", "center": [mcx + 0.02 * mw, mcy + 0.36 * mh], "rx": 0.05 * mw, "ry": 0.03 * mh},
        {"name": "Southeast Transfer Yard", "center": [mcx + 0.28 * mw, mcy - 0.06 * mh], "rx": 0.03 * mw, "ry": 0.04 * mh},
        {"name": "Inner Ring Cold Storage", "center": [mcx - 0.10 * mw, mcy + 0.18 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Southern Cross-Dock", "center": [mcx + 0.04 * mw, mcy - 0.36 * mh], "rx": 0.03 * mw, "ry": 0.02 * mh},
        {"name": "Midring Distribution Hub", "center": [mcx - 0.06 * mw, mcy - 0.14 * mh], "rx": 0.02 * mw, "ry": 0.03 * mh},
        {"name": "Eastern Interchange Depot", "center": [mcx + 0.32 * mw, mcy + 0.14 * mh], "rx": 0.03 * mw, "ry": 0.02 * mh},
        {"name": "North Plains Grain Silos", "center": [mcx + 0.10 * mw, mcy + 0.34 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Wall Shadow Staging Area", "center": [mcx - 0.28 * mw, mcy - 0.24 * mh], "rx": 0.03 * mw, "ry": 0.02 * mh},
        {"name": "Silk Road Caravanserai", "center": [mcx + 0.16 * mw, mcy + 0.20 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Southwest Marshaling Yard", "center": [mcx - 0.16 * mw, mcy - 0.30 * mh], "rx": 0.04 * mw, "ry": 0.02 * mh},
        {"name": "Refugee Quarter Supply Depot", "center": [mcx + 0.14 * mw, mcy - 0.26 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Canal Wharf Transload", "center": [mcx + 0.20 * mw, mcy + 0.28 * mh], "rx": 0.02 * mw, "ry": 0.01 * mh},
        {"name": "Westside Container Yard", "center": [mcx - 0.34 * mw, mcy + 0.16 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Central Post Sorting Hub", "center": [mcx + 0.04 * mw, mcy + 0.06 * mh], "rx": 0.01 * mw, "ry": 0.01 * mh},
        {"name": "Eastern Ore Terminal", "center": [mcx + 0.36 * mw, mcy - 0.10 * mh], "rx": 0.02 * mw, "ry": 0.03 * mh},
        {"name": "South Gate Freight Hub", "center": [mcx - 0.04 * mw, mcy - 0.32 * mh], "rx": 0.03 * mw, "ry": 0.02 * mh},
        {"name": "Badgermole Tunnel Depot", "center": [mcx - 0.24 * mw, mcy + 0.10 * mh], "rx": 0.02 * mw, "ry": 0.01 * mh},
    ]

    entertainment_zones = [
        {"name": "Jasmine Quarter", "center": [mcx + 0.05 * mw, mcy - 0.02 * mh], "rx": 0.05 * mw, "ry": 0.04 * mh},
        {"name": "Upper Ring Theater Row", "center": [mcx + 0.03 * mw, mcy + 0.07 * mh], "rx": 0.03 * mw, "ry": 0.02 * mh},
        {"name": "Firelight Night Market", "center": [mcx + 0.08 * mw, mcy - 0.06 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Lakefront Resort Strip", "center": [mcx + 0.16 * mw, mcy + 0.10 * mh], "rx": 0.03 * mw, "ry": 0.01 * mh},
        {"name": "Earth Rumble Arena District", "center": [mcx + 0.12 * mw, mcy - 0.10 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Royal Festival Grounds", "center": [mcx - 0.01 * mw, mcy + 0.03 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Western Amphitheater Complex", "center": [mcx - 0.16 * mw, mcy + 0.06 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "South Ring Racecourse", "center": [mcx + 0.08 * mw, mcy - 0.18 * mh], "rx": 0.03 * mw, "ry": 0.02 * mh},
        {"name": "Caldera Music Hall Row", "center": [mcx - 0.06 * mw, mcy + 0.10 * mh], "rx": 0.01 * mw, "ry": 0.02 * mh},
        {"name": "Outer Ring Fairgrounds", "center": [mcx - 0.22 * mw, mcy + 0.14 * mh], "rx": 0.03 * mw, "ry": 0.02 * mh},
        {"name": "Harbor Promenade", "center": [mcx + 0.24 * mw, mcy + 0.06 * mh], "rx": 0.02 * mw, "ry": 0.01 * mh},
        {"name": "Artists' Alley District", "center": [mcx + 0.06 * mw, mcy + 0.12 * mh], "rx": 0.01 * mw, "ry": 0.01 * mh},
        {"name": "Sunset Terrace Dining", "center": [mcx - 0.10 * mw, mcy - 0.02 * mh], "rx": 0.01 * mw, "ry": 0.01 * mh},
        {"name": "Northern Pleasure Gardens", "center": [mcx - 0.04 * mw, mcy + 0.24 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Cactus Juice Tavern Row", "center": [mcx + 0.10 * mw, mcy + 0.02 * mh], "rx": 0.01 * mw, "ry": 0.01 * mh},
        {"name": "Ba Sing Se Zoo", "center": [mcx - 0.12 * mw, mcy + 0.04 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Cabbage Merchant Square", "center": [mcx + 0.02 * mw, mcy - 0.08 * mh], "rx": 0.01 * mw, "ry": 0.01 * mh},
        {"name": "Eastern Hot Springs", "center": [mcx + 0.28 * mw, mcy + 0.20 * mh], "rx": 0.02 * mw, "ry": 0.02 * mh},
        {"name": "Poetry & Scroll District", "center": [mcx + 0.04 * mw, mcy + 0.16 * mh], "rx": 0.01 * mw, "ry": 0.01 * mh},
        {"name": "Wall Gate Night Bazaar", "center": [mcx - 0.30 * mw, mcy + 0.02 * mh], "rx": 0.02 * mw, "ry": 0.01 * mh},
    ]

    return {
        "bbox": [min_x, min_y, max_x, max_y],
        "metro_bbox": metro_bbox,
        "center": [mcx, mcy],
        "metro_scale": {"w": mw, "h": mh},
        "ring_radii": ring_radii_deg,
        "ring_radii_frac": ring_radii_frac,
        "cbd_crescent": cbd_crescent,
        "secondary_centers": secondary_centers,
        "lake": lake,
        "river_segments": river_segments,
        "primary_airport": primary_airport,
        "secondary_airport": secondary_airport,
        "campuses": campuses,
        "parks": parks,
        "industrial_zones": industrial_zones,
        "logistics_zones": logistics_zones,
        "entertainment_zones": entertainment_zones,
    }

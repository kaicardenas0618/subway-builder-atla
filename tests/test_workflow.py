from __future__ import annotations

import http.client
import json
import threading
import time
import unittest
import zipfile
from pathlib import Path

from src.debug_server import RangeRequestHandler, pick_free_port
from src.pipeline import run_build
from src.validation import validate_demand_integrity

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "roads.geojson",
    "runways_taxiways.geojson",
    "buildings_index.json",
    "demand_data.json",
    "BSS.pmtiles",
    "config.json",
}

class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_build("dev", clean=True)
        run_build("prod", clean=True)

    def test_debug_page_exists(self):
        self.assertTrue((ROOT / "debug_map.html").exists())

    def test_dev_outputs_exist(self):
        out = ROOT / "outputs" / "dev"
        for name in REQUIRED:
            self.assertTrue((out / name).exists(), msg=f"missing {name}")

    def test_prod_outputs_exist(self):
        out = ROOT / "outputs" / "prod"
        for name in REQUIRED:
            self.assertTrue((out / name).exists(), msg=f"missing {name}")

    def test_archive_contract_root_files(self):
        archive = ROOT / "outputs" / "dev" / "BSS-dev.zip"
        self.assertTrue(archive.exists())
        with zipfile.ZipFile(archive, "r") as zf:
            names = {i.filename for i in zf.infolist() if not i.is_dir()}
            self.assertTrue(REQUIRED.issubset(names))
            pmtiles = [n for n in names if n.endswith(".pmtiles")]
            self.assertEqual(len(pmtiles), 1)
            self.assertTrue(all("/" not in n for n in names))

    def test_config_shape(self):
        cfg = json.loads((ROOT / "outputs" / "dev" / "config.json").read_text(encoding="utf-8"))
        for key in ["name", "code", "description", "population", "creator", "version", "initialViewState"]:
            self.assertIn(key, cfg)
        self.assertEqual(cfg["code"], "BSS")
        for key in ["latitude", "longitude", "zoom", "bearing"]:
            self.assertIn(key, cfg["initialViewState"])

    def test_demand_integrity(self):
        demand = json.loads((ROOT / "outputs" / "dev" / "demand_data.json").read_text(encoding="utf-8"))
        summary = validate_demand_integrity(demand)
        self.assertGreater(summary["pointCount"], 100)
        self.assertGreater(summary["popCount"], 1000)
        self.assertGreater(summary["representedPopulation"], 500000)

    def test_byte_range_serving(self):
        from http.server import ThreadingHTTPServer

        port = pick_free_port()
        handler = lambda *args, **kwargs: RangeRequestHandler(*args, directory=str(ROOT), **kwargs)
        server = ThreadingHTTPServer(("127.0.0.1", port), handler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.2)
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
            conn.request("GET", "/outputs/dev/BSS.pmtiles", headers={"Range": "bytes=0-31"})
            resp = conn.getresponse()
            body = resp.read()
            self.assertEqual(resp.status, 206)
            self.assertEqual(len(body), 32)
        finally:
            server.shutdown()
            server.server_close()

    def test_dev_materially_smaller_than_prod(self):
        prod = json.loads((ROOT / "config" / "prod.yaml").read_text(encoding="utf-8"))
        dev = json.loads((ROOT / "config" / "dev.yaml").read_text(encoding="utf-8"))

        prod_area = (prod["map"]["bbox"][2] - prod["map"]["bbox"][0]) * (prod["map"]["bbox"][3] - prod["map"]["bbox"][1])
        dev_area = (dev["map"]["bbox"][2] - dev["map"]["bbox"][0]) * (dev["map"]["bbox"][3] - dev["map"]["bbox"][1])
        self.assertGreater(prod_area / dev_area, 3.0)

        self.assertLess(dev["build"]["building_rows"] * dev["build"]["building_cols"], prod["build"]["building_rows"] * prod["build"]["building_cols"])
        self.assertLess(dev["build"]["target_population"], prod["build"]["target_population"])

        prod_cfg = json.loads((ROOT / "outputs" / "prod" / "config.json").read_text(encoding="utf-8"))
        dev_cfg = json.loads((ROOT / "outputs" / "dev" / "config.json").read_text(encoding="utf-8"))
        self.assertGreater(prod_cfg["population"], dev_cfg["population"] * 2)

if __name__ == "__main__":
    unittest.main()

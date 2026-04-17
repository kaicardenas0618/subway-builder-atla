from __future__ import annotations

import http.client
import json
import subprocess
import threading
import time
import unittest
import zipfile
from pathlib import Path

from src.debug_server import RangeRequestHandler, pick_free_port
from src.pipeline import run_build


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "roads.geojson",
    "runways_taxiways.geojson",
    "buildings_index.json",
    "demand_data.json",
    "map.pmtiles",
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
        archive = ROOT / "outputs" / "dev" / "FC1-dev.zip"
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
        for key in ["latitude", "longitude", "zoom", "bearing"]:
            self.assertIn(key, cfg["initialViewState"])

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
            conn.request("GET", "/outputs/dev/map.pmtiles", headers={"Range": "bytes=0-31"})
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

        self.assertLess(dev["build"]["building_rows"] * dev["build"]["building_cols"], prod["build"]["building_rows"] * prod["build"]["building_cols"])
        self.assertLess(dev["build"]["demand_points"], prod["build"]["demand_points"])
        self.assertLess(dev["build"]["pop_links_per_point"], prod["build"]["pop_links_per_point"])


if __name__ == "__main__":
    unittest.main()

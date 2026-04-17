from __future__ import annotations

import mimetypes
import os
import socket
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

def pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])

class RangeRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        if not os.path.exists(path):
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        ctype = self.guess_type(path)
        file_size = os.path.getsize(path)
        range_header = self.headers.get("Range")

        f = open(path, "rb")
        if not range_header:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            return f

        try:
            unit, rng = range_header.strip().split("=", 1)
            if unit != "bytes":
                raise ValueError("Unsupported range unit")
            start_s, end_s = rng.split("-", 1)
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else file_size - 1
            if start > end or end >= file_size:
                raise ValueError("Invalid range values")
        except Exception:
            f.close()
            self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, "Invalid Range header")
            return None

        self.send_response(HTTPStatus.PARTIAL_CONTENT)
        self.send_header("Content-type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        f.seek(start)
        self.range = (start, end)
        return f

    def copyfile(self, source, outputfile):
        if hasattr(self, "range"):
            start, end = self.range
            remaining = end - start + 1
            chunk_size = 64 * 1024
            while remaining > 0:
                chunk = source.read(min(chunk_size, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
            del self.range
            return
        super().copyfile(source, outputfile)

def serve(root_dir: Path, port: int | None) -> None:
    host = "127.0.0.1"
    use_port = port if port is not None else pick_free_port()
    handler = lambda *args, **kwargs: RangeRequestHandler(*args, directory=str(root_dir), **kwargs)
    server = ThreadingHTTPServer((host, use_port), handler)
    url = f"http://{host}:{use_port}/debug_map.html"
    print(f"[serve] {url}")
    print("[serve] serving existing artifacts only; no build is triggered")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

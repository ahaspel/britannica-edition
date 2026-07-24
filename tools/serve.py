#!/usr/bin/env python3
"""Local dev server — the repo root on :8000, speaking PRODUCTION's URL space.

Two jobs in one server:

1. DETACHED OPERATION: registered as the `britannica-webserver` scheduled
   task (at logon), running under `pythonw.exe`.  With no console there is
   no valid stderr, so `http.server`'s per-request log write would raise and
   kill the connection mid-response — logging goes to a real file instead,
   and never raises.  It serves the repo root regardless of inherited
   working directory.

2. PRODUCTION URL SPACE, VERBATIM: the deployed site's URLs are shaped by
   CloudFront + the S3 layout (see tools/deploy.sh for the mapping).  This
   server maps that space onto the working tree so the viewer pages carry
   ZERO local/production switches — every href and fetch is written in the
   production form and works in both worlds:

     /                        → tools/viewer/home.html
     /{page}.html, /{asset}   → tools/viewer/{...} when it exists there
     /article/{sid}[/{slug}]  → tools/viewer/viewer.html  (the CloudFront
                                article-rewrite: 200-serve the SPA shell;
                                the client routes on location.pathname)
     /data/articles/*         → data/derived/articles/*
     /data/scans/*            → data/derived/scans/*
     /data/{name}.json        → data/derived/{name}.json
     /data/images/*           → data/images/*  (same path; no rewrite)
     /download/eb1911-corpus… → data/derived/eb1911-corpus…
     /download/*              → data/derived/download/*
     /search-api/*            → proxied to Meilisearch at 127.0.0.1:7700,
                                Authorization REWRITTEN to the local dev key
                                (clients always send the production key)
     everything else          → repo-root relative (dev conveniences like
                                /tools/viewer/… and /data/derived/… still work)

Run by hand the same way the task does:  uv run python tools/serve.py [port]
"""
import http.server
import os
import re
import socketserver
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWER = ROOT / "tools" / "viewer"
MEILI = "http://127.0.0.1:7700"
MEILI_LOCAL_KEY = "britannica-dev-key"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
LOG = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / \
    "britannica-webserver.log"

_DATA_JSON_RE = re.compile(r"^/data/([^/]+\.json)$")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def log_message(self, fmt, *args):
        # Never raise: a logging failure must not take the response with it.
        try:
            with LOG.open("a", encoding="utf-8") as fh:
                fh.write(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} "
                         f"{self.address_string()} {fmt % args}\n")
        except Exception:
            pass

    # ── production-shaped routing ────────────────────────────────────────
    def _rewrite_path(self) -> None:
        """Map the production URL space onto the working tree (in place)."""
        path, sep, query = self.path.partition("?")

        if path == "/":
            path = "/home.html"
        elif path.startswith("/article/"):
            # The CloudFront article-rewrite: serve the SPA shell; the client
            # routes on the id in location.pathname.
            path = "/tools/viewer/viewer.html"
        elif path.startswith("/data/articles/"):
            path = "/data/derived/articles/" + path[len("/data/articles/"):]
        elif path.startswith("/data/scans/"):
            path = "/data/derived/scans/" + path[len("/data/scans/"):]
        elif _DATA_JSON_RE.match(path):
            path = "/data/derived/" + path[len("/data/"):]
        elif path.startswith("/download/eb1911-corpus"):
            path = "/data/derived/" + path[len("/download/"):]
        elif path.startswith("/download/"):
            path = "/data/derived/download/" + path[len("/download/"):]

        # A bucket-root file that lives in tools/viewer/ locally.
        candidate = path.lstrip("/")
        if "/" not in candidate and (VIEWER / candidate).is_file():
            path = f"/tools/viewer/{candidate}"
        self.path = path + (sep + query if query else "")

    # ── meilisearch proxy ────────────────────────────────────────────────
    def _proxy_meili(self, subpath: str, query: str, body: bytes | None = None):
        url = MEILI + subpath + (f"?{query}" if query else "")
        req = urllib.request.Request(url, data=body, method=self.command)
        ct = self.headers.get("Content-Type")
        if ct:
            req.add_header("Content-Type", ct)
        # Clients send the PRODUCTION search key (there is no local fork);
        # the local Meilisearch only knows the dev master key — swap it in.
        if self.headers.get("Authorization"):
            req.add_header("Authorization", f"Bearer {MEILI_LOCAL_KEY}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header(
                    "Content-Type",
                    resp.headers.get("Content-Type", "application/json"))
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except OSError:
            msg = (b'{"message": "Meilisearch is not running locally - '
                   b'start it via tools/pipeline/start_services.sh"}')
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    # ── verbs ────────────────────────────────────────────────────────────
    def do_GET(self):
        path, _, query = self.path.partition("?")
        if path.startswith("/search-api/"):
            self._proxy_meili(path[len("/search-api"):], query)
            return
        self._rewrite_path()
        super().do_GET()

    def do_HEAD(self):
        path, _, query = self.path.partition("?")
        if path.startswith("/search-api/"):
            self._proxy_meili(path[len("/search-api"):], query)
            return
        self._rewrite_path()
        super().do_HEAD()

    def do_POST(self):
        path, _, query = self.path.partition("?")
        if path.startswith("/search-api/"):
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else None
            self._proxy_meili(path[len("/search-api"):], query, body)
            return
        self.send_error(405)


class Server(socketserver.ThreadingTCPServer):
    # Threaded so one slow article fetch can't block the viewer's next request,
    # and address-reusing so a restart doesn't hit TIME_WAIT on the port.
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    try:
        LOG.write_text(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} "
                       f"serving {ROOT} on :{PORT} (production-shaped URLs)\n",
                       encoding="utf-8")
    except Exception:
        pass
    with Server(("", PORT), Handler) as httpd:
        httpd.serve_forever()

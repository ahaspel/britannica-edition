"""Local dev server that speaks PRODUCTION's URL space.

The deployed site's URLs are shaped by CloudFront + the S3 layout: pages live
at the bucket root (`/home.html`, `/topics.html`, `/readers-guide-*.html`),
articles route through the `article-rewrite` function
(`/article/{stable-id}[/{slug}]` → viewer.html), and `/search-api/*` proxies
to Meilisearch.  A bare ``python -m http.server`` at the repo root has none of
that, so every production-shaped href 404s locally — the main pages, the
Reader's Guide links, the bylines.

This server maps the production URL space onto the working tree, so LOCAL
navigation works exactly like the live site with ZERO page changes:

  /                          → tools/viewer/home.html
  /{page}.html, /{asset}     → tools/viewer/{...} when it exists there
  /article/{sid}[/{slug}]    → 302 to /viewer.html?article=/data/derived/articles/{sid}.json
                               (the IS_LOCAL viewer reads ?article=; the slug is
                               cosmetic exactly as in production)
  /search-api/*              → proxied to Meilisearch at 127.0.0.1:7700
                               (start it via tools/pipeline/start_services.sh)
  everything else            → repo-root relative (/data/derived/..., scans, …)

Usage:
  uv run python tools/serve_local.py            # port 8000
  uv run python tools/serve_local.py 8080
"""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWER = ROOT / "tools" / "viewer"
MEILI = "http://127.0.0.1:7700"


class ProductionShapedHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    # ── routing ──────────────────────────────────────────────────────────
    def _route(self) -> bool:
        """Handle the production-only URL shapes.  Returns True when the
        request was fully handled here."""
        path, _, query = self.path.partition("?")

        if path.startswith("/article/"):
            # /article/{stable-id}[/{slug}] — the CloudFront article-rewrite.
            sid = path.split("/")[2]
            target = f"/viewer.html?article=/data/derived/articles/{sid}.json"
            if query:
                target += "&" + query
            self.send_response(302)
            self.send_header("Location", target)
            self.end_headers()
            return True

        if path.startswith("/search-api/"):
            self._proxy_meili(path[len("/search-api"):], query)
            return True

        return False

    def _rewrite_path(self) -> None:
        """Map bucket-root paths onto the working tree (in place)."""
        path, sep, query = self.path.partition("?")
        if path == "/":
            path = "/home.html"
        # A bucket-root file that lives in tools/viewer/ locally.
        candidate = path.lstrip("/")
        if "/" not in candidate and (VIEWER / candidate).is_file():
            path = f"/tools/viewer/{candidate}"
        self.path = path + (sep + query if query else "")

    # ── meilisearch proxy ────────────────────────────────────────────────
    def _proxy_meili(self, subpath: str, query: str, body: bytes | None = None):
        url = MEILI + subpath + (f"?{query}" if query else "")
        req = urllib.request.Request(url, data=body, method=self.command)
        for h in ("Content-Type", "Authorization"):
            v = self.headers.get(h)
            if v:
                req.add_header(h, v)
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
        if self._route():
            return
        self._rewrite_path()
        super().do_GET()

    def do_HEAD(self):
        if self._route():
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

    def log_message(self, fmt, *args):  # quieter: only errors and redirects
        if args and str(args[1:2] or "").startswith(("4", "5")):
            super().log_message(fmt, *args)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), ProductionShapedHandler)
    print(f"serving production-shaped URLs at http://localhost:{port}/ "
          f"(root: {ROOT})")
    server.serve_forever()


if __name__ == "__main__":
    main()

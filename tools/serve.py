#!/usr/bin/env python3
"""Static file server for local development — the repo root on :8000.

The same thing as `python -m http.server 8000` at the repo root, with two
differences that let it run DETACHED as a logon task:

  * It serves the repo root regardless of the working directory it inherits.
  * It owns its logging.  Under `pythonw.exe` (no console) there is no valid
    stderr, so `http.server`'s per-request log write raises and the connection
    dies mid-response — the server looks up but every fetch fails.  Writing to a
    real file instead is what makes windowless operation work at all.

Registered as the `britannica-webserver` scheduled task (at logon).  Run it by
hand the same way:  uv run python tools/serve.py [port]
"""
import http.server
import os
import socketserver
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
LOG = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir()) / \
    "britannica-webserver.log"


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


class Server(socketserver.ThreadingTCPServer):
    # Threaded so one slow article fetch can't block the viewer's next request,
    # and address-reusing so a restart doesn't hit TIME_WAIT on the port.
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    try:
        LOG.write_text(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} "
                       f"serving {ROOT} on :{PORT}\n", encoding="utf-8")
    except Exception:
        pass
    with Server(("", PORT), Handler) as httpd:
        httpd.serve_forever()

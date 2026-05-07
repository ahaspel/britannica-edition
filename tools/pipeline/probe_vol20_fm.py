"""Fetch WS DjVu pages 1-20 for vol 20 to determine FM-leaf alignment.

The article-body swap (swap_vol20_scans.py) uses a +2 offset
(ws-page 19 -> IA leaf 21).  Whether that offset extends back through
the front-matter / leading-blank region depends on whether the WS DjVu
and Osmania have the same number of leading title/blank pages.

This script pulls the first 20 WS DjVu pages into a side-by-side
directory so you can eyeball alignment against the existing Osmania
leaves 1..20 in ``data/derived/scans/vol20_leafNNNN.jpg``.

After visual confirmation, edit the ALIGNMENT below (or invoke
``swap_vol20_scans.py``-style logic for the chosen ws->leaf range)
to swap the FM bytes in.

Usage::

    uv run python tools/pipeline/probe_vol20_fm.py
"""
from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

OUT = Path("tmp_vol20_ws_fm")
OUT.mkdir(exist_ok=True)
DJVU = "EB1911 - Volume 20.djvu"
WIDTH = 2400
DELAY = 3.0

SESSION = requests.Session()
SESSION.headers["User-Agent"] = (
    "Britannica11Bot/1.0 (https://britannica11.org; scholarly digital edition)"
)


def djvu_page_url(filename: str, page: int, width: int) -> str:
    name = filename.replace(" ", "_")
    md5 = hashlib.md5(name.encode()).hexdigest()
    enc = quote(name)
    return (
        f"https://upload.wikimedia.org/wikipedia/commons/thumb/"
        f"{md5[0]}/{md5[:2]}/{enc}/page{page}-{width}px-{enc}.jpg"
    )


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    for ws in range(1, 21):
        out = OUT / f"vol20_ws{ws:04d}.jpg"
        if out.exists() and out.stat().st_size > 0:
            print(f"  cached {out.name}", flush=True)
            continue
        url = djvu_page_url(DJVU, ws, WIDTH)
        r = SESSION.get(url, timeout=60)
        if r.status_code != 200:
            print(f"  ws {ws}: HTTP {r.status_code}", flush=True)
            time.sleep(DELAY)
            continue
        out.write_bytes(r.content)
        print(f"  ws {ws} -> {out.name}  ({len(r.content):,} bytes)", flush=True)
        time.sleep(DELAY)
    print("\nNow eyeball tmp_vol20_ws_fm/vol20_ws*.jpg vs "
          "data/derived/scans/vol20_leaf*.jpg (leaves 1..20) to "
          "determine the FM ws->leaf offset.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

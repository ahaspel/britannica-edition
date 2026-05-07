"""Replace vol-20 scan bytes with higher-quality wikisource DjVu page renders.

Vol 20's bundled IA scans (Osmania) are noticeably lower-resolution than
the EB1911 - Volume 20.djvu source on Wikimedia Commons (samples checked
at ~2.7x linear resolution).  This one-shot script overwrites each
``data/derived/scans/vol20_leaf{leaf:04d}.jpg`` whose ws-page is in
``scan_map["20"]`` with the WS DjVu thumbnail at 2400 px width.

The 56 ws-pages absent from scan_map (plate inserts not addressable via
the printed-page index) are deferred to a follow-up splice — they keep
their Osmania bytes for now.

Resumable: if a target file already exists with size > MIN_REPLACE_BYTES,
it is treated as already-swapped and skipped.  Set ``--force`` to
overwrite regardless.

Rate-limiting: 3 s between requests; on HTTP 429 sleep 6 min and retry
(per the wikisource-rate memory entry — ~450 at 3 s delay, 6-min
cooldown works).

Usage::

    nohup uv run python tools/pipeline/swap_vol20_scans.py \\
        > vol20_scan_swap.log 2>&1 &
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

VOL = 20
DJVU = f"EB1911 - Volume {VOL:02d}.djvu"
SCAN_DIR = Path("data/derived/scans")
SCAN_MAP_PATH = Path("data/derived/scan_map.json")
WIDTH = 2400
DELAY = 3.0
RATE_LIMIT_WAIT = 360  # seconds; 6-min cooldown per memory
MAX_RETRIES = 5

# Osmania scans top out around 600 KB; WS scans at WIDTH=2400 are
# 1-2.5 MB.  Use 700 KB as the resume threshold so any partially-written
# Osmania file (or a previously-swapped WS file) is correctly classified.
MIN_REPLACE_BYTES = 700_000

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


def fetch_ws_page(ws: int) -> bytes | None:
    url = djvu_page_url(DJVU, ws, WIDTH)
    for attempt in range(MAX_RETRIES):
        try:
            r = SESSION.get(url, timeout=60)
        except requests.RequestException as e:
            print(f"  ws {ws}: network error {e!r}, retry {attempt + 1}/"
                  f"{MAX_RETRIES} after {RATE_LIMIT_WAIT}s",
                  flush=True)
            time.sleep(RATE_LIMIT_WAIT)
            continue
        if r.status_code == 429:
            print(f"  ws {ws}: 429 rate-limit, sleeping {RATE_LIMIT_WAIT}s "
                  f"(retry {attempt + 1}/{MAX_RETRIES})",
                  flush=True)
            time.sleep(RATE_LIMIT_WAIT)
            continue
        if r.status_code == 404:
            print(f"  ws {ws}: 404 not found, skipping", flush=True)
            return None
        if r.status_code != 200:
            print(f"  ws {ws}: HTTP {r.status_code}, retry {attempt + 1}/"
                  f"{MAX_RETRIES} after {RATE_LIMIT_WAIT}s",
                  flush=True)
            time.sleep(RATE_LIMIT_WAIT)
            continue
        return r.content
    print(f"  ws {ws}: FAILED after {MAX_RETRIES} retries", flush=True)
    return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true",
                   help="overwrite even files that already look like WS scans")
    p.add_argument("--dry-run", action="store_true",
                   help="report what would happen without fetching")
    p.add_argument("--limit", type=int, default=0,
                   help="stop after N successful fetches (0 = no limit)")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    sm = json.loads(SCAN_MAP_PATH.read_text(encoding="utf-8"))[str(VOL)]
    pairs = sorted(((int(w), int(l)) for w, l in sm.items() if l is not None),
                   key=lambda x: x[0])
    print(f"vol {VOL}: {len(pairs)} ws -> leaf entries in scan_map", flush=True)

    todo = []
    for ws, leaf in pairs:
        out = SCAN_DIR / f"vol{VOL:02d}_leaf{leaf:04d}.jpg"
        if not args.force and out.exists() and out.stat().st_size >= MIN_REPLACE_BYTES:
            continue
        todo.append((ws, leaf, out))
    print(f"  to fetch: {len(todo)}  (already swapped: "
          f"{len(pairs) - len(todo)})", flush=True)

    if args.dry_run:
        for ws, leaf, out in todo[:20]:
            sz = out.stat().st_size if out.exists() else 0
            print(f"  WOULD fetch ws {ws} -> {out.name} (current {sz} bytes)")
        if len(todo) > 20:
            print(f"  ... and {len(todo) - 20} more")
        return 0

    fetched = 0
    skipped = 0
    failed = 0
    started = time.time()
    for i, (ws, leaf, out) in enumerate(todo, 1):
        data = fetch_ws_page(ws)
        if data is None:
            failed += 1
            continue
        if len(data) < MIN_REPLACE_BYTES:
            print(f"  ws {ws}: response too small ({len(data)} bytes), "
                  f"skipping write", flush=True)
            skipped += 1
            continue
        tmp = out.with_suffix(".jpg.tmp")
        tmp.write_bytes(data)
        tmp.replace(out)
        fetched += 1
        elapsed = time.time() - started
        rate = fetched / elapsed if elapsed > 0 else 0
        if i % 10 == 0 or i == len(todo):
            print(f"  [{i}/{len(todo)}] ws {ws} -> {out.name} "
                  f"({len(data):,} bytes)  fetched={fetched} skipped={skipped} "
                  f"failed={failed}  rate={rate:.2f}/s",
                  flush=True)
        if args.limit and fetched >= args.limit:
            print(f"  --limit {args.limit} reached, stopping", flush=True)
            break
        time.sleep(DELAY)

    print(f"\nDONE: fetched={fetched}  skipped={skipped}  failed={failed}  "
          f"elapsed={time.time() - started:.0f}s",
          flush=True)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
import requests

API_URL = "https://en.wikisource.org/w/api.php"

HEADERS = {
    "User-Agent": "britannica-edition/0.1 (local dev)",
    "Accept": "application/json",
}


def fetch_page_wikitext(volume: int, page_number: int) -> str:
    title = f"Page:EB1911 - Volume {volume:02d}.djvu/{page_number}"
    params = {
        "action": "query",
        "prop": "revisions",
        "rvslots": "main",
        "rvprop": "content",
        "titles": title,
        "format": "json",
        "formatversion": "2",
    }

    max_retries = 3
    for attempt in range(max_retries):
        print(f"Fetching {title} ...")
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
        print(f"HTTP {response.status_code} for {title}")

        if response.status_code == 429:
            print(f"  Rate limited, sleeping 1 hour...")
            time.sleep(3600)
            continue

        response.raise_for_status()
        break
    else:
        raise requests.exceptions.HTTPError(
            f"Still rate-limited after {max_retries} retries for {title}"
        )

    data = response.json()
    pages = data.get("query", {}).get("pages", [])
    if not pages:
        raise ValueError(f"No page data returned for {title}")

    page = pages[0]
    if page.get("missing"):
        print(f"  Page does not exist: {title} — writing empty placeholder")
        return ""

    revisions = page.get("revisions", [])
    if not revisions:
        raise ValueError(f"No revisions/content found for {title}")

    rev = revisions[0]

    content = rev.get("content")
    if content is None:
        content = rev.get("slots", {}).get("main", {}).get("content")

    # Extra fallback for some MediaWiki response shapes
    if content is None:
        content = rev.get("slots", {}).get("main", {}).get("*")

    if content is None:
        raise ValueError(
            f"Could not locate content for {title}. Revision keys: {list(rev.keys())}"
        )

    return content


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=int, required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0,
                        help="Max pages to fetch this invocation (0 = no limit)")
    args = parser.parse_args()

    print("Starting fetch...")
    print(f"Volume: {args.volume}")
    print(f"Page range: {args.start} to {args.end}")
    print(f"Outdir arg: {args.outdir}")

    if args.end < args.start:
        raise SystemExit("--end must be >= --start")

    outdir = args.outdir.resolve()
    print(f"Resolved outdir: {outdir}")

    outdir.mkdir(parents=True, exist_ok=True)
    print(f"Outdir exists: {outdir.exists()}")

    fetched_this_run = 0
    for page_number in range(args.start, args.end + 1):
        outfile = outdir / f"vol{args.volume:02d}-page{page_number:04d}.json"
        if outfile.exists():
            continue

        if args.limit and fetched_this_run >= args.limit:
            print(f"Reached limit of {args.limit} pages, stopping.")
            break

        raw = fetch_page_wikitext(args.volume, page_number)
        fetched_this_run += 1
        time.sleep(3)  # polite delay between requests

        payload = {
            "volume": args.volume,
            "page_number": page_number,
            "source": "wikisource",
            "title": f"Page:EB1911 - Volume {args.volume:02d}.djvu/{page_number}",
            "raw_text": raw,
        }

        outfile = outdir / f"vol{args.volume:02d}-page{page_number:04d}.json"
        outfile.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {outfile}")

    print("Done.")


if __name__ == "__main__":
    main()

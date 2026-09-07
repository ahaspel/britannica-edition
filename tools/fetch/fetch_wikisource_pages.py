#!/usr/bin/env python3
"""Fetch a volume's pages from Wikisource into one JSON file per page.

BATCHED, because the arithmetic forces it.  The MediaWiki API returns up to 50
pages per query; asking one at a time with a three-second delay costs 28 hours
for the DNB's 33,824 pages and 24 for the Britannica's 29,000.  Fifty at a time
with a delay between BATCHES is both faster and politer per page: the same work
becomes ~680 requests instead of ~34,000.

Politeness is not just the delay.  `maxlag=5` asks the API to refuse us when its
replicas are lagging, which is the documented way to be a good citizen — it
means a busy Wikisource sheds our load rather than us noticing later, if at all.

The CLI and the output contract are unchanged: one
`vol<NN>-page<NNNN>.json` per page, `{volume, page_number, source, title,
raw_text}`, which `import_wikisource_pages.py` reads.  Existing files are
skipped, so a run resumes where the last one stopped.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests

from britannica.corpora import current_corpus

API_URL = "https://en.wikisource.org/w/api.php"

HEADERS = {
    "User-Agent": "britannica-edition/0.2 (ahaspel@gmail.com)",
    "Accept": "application/json",
}

BATCH = 50               # the API's limit for anonymous queries
DELAY = 1.0              # between batches — 50 pages per request, so ~0.02s/page
RATE_LIMIT_WAIT = 3600   # a 429 means back off for an hour, not retry harder
MAX_RETRIES = 3


def fetch_batch(volume: int, page_numbers: list[int]) -> dict[int, str]:
    """Wikitext for up to ``BATCH`` pages of one volume, keyed by page number.

    A page that does not exist comes back as the empty string, not as a missing
    key: a gap in a scan is a fact about the book, and recording it as an empty
    page is how the importer and every later count stay aligned with the volume.
    """
    corpus = current_corpus()
    by_title = {corpus.page_title(volume, n): n for n in page_numbers}
    params = {
        "action": "query",
        "prop": "revisions",
        "rvslots": "main",
        "rvprop": "content",
        "titles": "|".join(by_title),
        "format": "json",
        "formatversion": "2",
        "maxlag": 5,
    }

    for attempt in range(MAX_RETRIES):
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=90)
        if response.status_code == 429:
            print(f"  Rate limited, sleeping {RATE_LIMIT_WAIT // 60} min...")
            time.sleep(RATE_LIMIT_WAIT)
            continue
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code} for a batch of "
                               f"{len(page_numbers)} in volume {volume}")
        data = response.json()
        # maxlag is reported as an error, not a status code.
        if data.get("error", {}).get("code") == "maxlag":
            wait = int(float(data["error"].get("lag", 5))) + 5
            print(f"  Replicas lagging, waiting {wait}s...")
            time.sleep(wait)
            continue
        break
    else:
        raise RuntimeError(f"still rate-limited after {MAX_RETRIES} attempts "
                           f"(volume {volume})")

    out: dict[int, str] = {}
    # `normalized` maps what we asked for to what the API calls it; without
    # following it, a title the API rewrites silently loses its page.
    canonical = {n["to"]: n["from"] for n in data.get("query", {}).get("normalized", [])}
    for page in data.get("query", {}).get("pages", []):
        title = canonical.get(page["title"], page["title"])
        number = by_title.get(title)
        if number is None:
            continue
        if page.get("missing"):
            out[number] = ""
            continue
        try:
            out[number] = page["revisions"][0]["slots"]["main"]["content"]
        except (KeyError, IndexError):
            out[number] = ""

    absent = set(page_numbers) - set(out)
    if absent:
        raise RuntimeError(f"volume {volume}: the API returned nothing at all for "
                           f"{len(absent)} requested page(s), e.g. {sorted(absent)[:5]}")
    return out


def fetch_volume(volume: int, start: int, end: int, outdir: Path,
                 limit: int = 0) -> int:
    """One volume's pages into ``outdir``.  Returns how many were written."""
    corpus = current_corpus()
    outdir.mkdir(parents=True, exist_ok=True)

    def path_for(n: int) -> Path:
        return outdir / f"vol{volume:02d}-page{n:04d}.json"

    wanted = [n for n in range(start, end + 1) if not path_for(n).exists()]
    if limit:
        wanted = wanted[:limit]

    have = (end - start + 1) - len(wanted)
    print(f"  volume {volume:>2}  {corpus.scan_name(volume)}")
    print(f"            {len(wanted)} to fetch, {have} already present")
    if not wanted:
        return 0

    written = 0
    for i in range(0, len(wanted), BATCH):
        for number, raw in sorted(fetch_batch(volume, wanted[i:i + BATCH]).items()):
            path_for(number).write_text(
                json.dumps({
                    "volume": volume,
                    "page_number": number,
                    "source": "wikisource",
                    "title": corpus.page_title(volume, number),
                    "raw_text": raw,
                }, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            written += 1
        print(f"            {written}/{len(wanted)}", end="\r", flush=True)
        if i + BATCH < len(wanted):
            time.sleep(DELAY)
    print(f"            {written}/{len(wanted)} written        ")
    return written


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=int,
                        help="One volume.  Omit with --all for the whole book.")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int,
                        help="Defaults to the volume's page count from the corpus profile.")
    parser.add_argument("--outdir", type=Path,
                        help="Defaults to data/raw/<corpus>/vol_<NN>.")
    parser.add_argument("--all", action="store_true",
                        help="Every volume in the corpus, in order.")
    parser.add_argument("--limit", type=int, default=0,
                        help="Max pages per volume this invocation (0 = no limit)")
    args = parser.parse_args()

    corpus = current_corpus()
    if not args.all and args.volume is None:
        raise SystemExit("give --volume N, or --all for the whole book")

    volumes = corpus.volumes if args.all else [args.volume]
    # The page count is the corpus profile's job.  It used to be a bash array in
    # fetch_all.sh, which could not be tested and did not know which book it was
    # for.  Passing --end still overrides, for a deliberate partial fetch.
    unknown = [v for v in volumes if v not in corpus.pages]
    if unknown:
        raise SystemExit(f"{corpus.key} has no page count for volume(s) {unknown}")

    print(f"{corpus.key}: {len(volumes)} volume(s), "
          f"{sum(corpus.pages[v] for v in volumes):,} pages")

    total = 0
    for v in volumes:
        end = args.end if args.end else corpus.pages[v]
        if end < args.start:
            raise SystemExit("--end must be >= --start")
        outdir = (args.outdir if args.outdir
                  else Path("data/raw") / corpus.key / f"vol_{v:02d}").resolve()
        total += fetch_volume(v, args.start, end, outdir, args.limit)
    print(f"Done. {total:,} page(s) written.")


if __name__ == "__main__":
    main()

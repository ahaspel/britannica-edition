"""Download Commons images for local hosting and EPUB prep.

Downloads every image the corpus references — the filenames are harvested from
the exported article bodies' {{IMG:…}} markers, not a DB table (PNG/JPG/SVG/GIF).

DjVu page crops are handled separately by tools/download_djvu_crops.py.

Downloads to data/images/ — the SAME directory the render points at
(`/data/images/<name>`) and deploy.sh syncs to S3 — skipping files already
present.  (This line said data/derived/images/ for a while; the code never
did, but a reader chasing missing figures would have looked in the wrong
place.)
Rate-limited to respect Wikimedia servers.

Rate limiting: 3s between requests, 15-minute cooldown after every 350 requests
(matches the Wikisource fetch policy).  Falls back to Special:FilePath on 404
(handles case-sensitivity mismatches in Commons URLs).

Usage:
    python tools/download_images.py [--delay SECONDS]
"""

import argparse
import io

from britannica.export.corpus import load_corpus
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

# Force UTF-8 output on Windows (filenames may contain non-Latin characters)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

IMAGE_DIR = Path("data/images")
ARTICLES_DIR = Path("data/derived/articles")
DELAY = 3  # seconds between requests
BATCH_SIZE = 350  # requests before cooldown
COOLDOWN = 15 * 60  # 15 minutes

SESSION = requests.Session()
SESSION.headers["User-Agent"] = (
    "Britannica11Bot/1.0 (https://britannica11.org; scholarly digital edition)"
)


# ---------------------------------------------------------------------------
# Commons images (from the exported corpus)
# ---------------------------------------------------------------------------

# The name derivation belongs to `image_assets.local_image_filename` — the SAME
# function the render calls to build the `<img src>`, handed the same name or
# URL.  Getting the two out of step is what left 18 articles pointing at files
# stored under another spelling.
from britannica.image_assets import local_image_filename as _local_filename


def _cooldown_if_needed(request_count: int) -> int:
    """Pause for COOLDOWN seconds after every BATCH_SIZE requests. Returns new count."""
    if request_count > 0 and request_count % BATCH_SIZE == 0:
        print(f"  — Batch of {BATCH_SIZE} reached, cooling down for {COOLDOWN // 60} minutes...")
        time.sleep(COOLDOWN)
    return request_count


RATE_LIMIT_WAIT = 3600  # 1 hour, matches fetch_wikisource_pages.py


def _download_with_retry(url: str, local_path: Path, local_name: str,
                         max_retries: int = 3, quiet: bool = False) -> bool:
    """Download a file, retrying on 429 rate-limit errors.

    Sleeps 1 hour on 429 (same as the Wikisource fetch pipeline).
    Returns True if downloaded successfully, False on permanent failure.

    ``quiet`` suppresses the failure line when this is the FIRST of several
    hosts to try — a miss on Commons for a Wikisource-hosted file is expected,
    not a failure, and printing it would train the reader to ignore the line
    that reports a real one.
    """
    for attempt in range(max_retries):
        try:
            resp = SESSION.get(url, timeout=60, allow_redirects=True)
            if resp.status_code == 429:
                print(f"  Rate limited, sleeping 1 hour...")
                time.sleep(RATE_LIMIT_WAIT)
                continue
            resp.raise_for_status()
            local_path.write_bytes(resp.content)
            return True
        except requests.RequestException as e:
            if not quiet:
                print(f"  FAILED: {local_name} — {e}", file=sys.stderr)
            return False
    print(f"  FAILED (still rate-limited after {max_retries} retries): {local_name}",
          file=sys.stderr)
    return False


def _harvest_image_filenames() -> list[str]:
    """Every image filename the corpus references, read from the exported article
    bodies' ``{{IMG:filename|…}}`` markers — the corpus is its own record of which
    images it needs, so there's no separate table to keep in sync."""
    from britannica.markers import IMG_PARTS_RE

    names: set[str] = set()
    # Total read: an article this cannot parse RAISES rather than having its
    # images quietly go undownloaded.
    for path, data in sorted(load_corpus()[0].items()):
        for m in IMG_PARTS_RE.finditer(data.get("body") or ""):
            fn = (m.group(1) or "").strip()
            if fn:
                names.add(fn)
    return sorted(names)


def download_commons_images(delay: float, request_count: int = 0) -> tuple[int, int, int]:
    """Download every Commons image the corpus references.

    Returns (downloaded, skipped, request_count).
    """
    filenames = _harvest_image_filenames()

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    skipped = 0

    for filename in filenames:
        local_name = _local_filename(filename)
        local_path = IMAGE_DIR / local_name
        if local_path.exists() and local_path.stat().st_size > 0:
            skipped += 1
            continue

        # SVGs: save as .png since Special:FilePath rasterises them
        ext = local_name.rsplit(".", 1)[-1].lower()
        if ext == "svg":
            local_path = IMAGE_DIR / (local_name + ".png")
            if local_path.exists() and local_path.stat().st_size > 0:
                skipped += 1
                continue

        # A bare name → Special:FilePath; a full URL (e.g. a rendered score
        # image) → fetch it directly, the way the viewer links it.
        #
        # COMMONS IS NOT THE ONLY HOST.  Some EB1911 illustrations live on
        # en.wikisource itself rather than Commons — PALLIUM's
        # `EB1911 - Volume 20.djvu-694.png` is a 1588x561 crop that exists there
        # and nowhere on Commons — so a Commons-only fetch reports "absent" for
        # a file that is simply somewhere else.  Try Commons, then Wikisource:
        # the wiki that hosts it is not something the corpus records, so asking
        # both is cheaper than maintaining a list of which images live where.
        if filename.startswith("http"):
            urls = [filename]
        else:
            urls = [f"https://{host}/wiki/Special:FilePath/{quote(filename)}?width=1200"
                    for host in ("commons.wikimedia.org", "en.wikisource.org")]

        request_count += 1
        request_count = _cooldown_if_needed(request_count)

        if any(_download_with_retry(u, local_path, local_name, quiet=(i == 0 and len(urls) > 1))
               for i, u in enumerate(urls)):
            downloaded += 1
            print(f"  [{downloaded}] {local_name} ({local_path.stat().st_size:,} bytes)")

        time.sleep(delay)

    return downloaded, skipped, request_count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Download Commons images")
    parser.add_argument("--delay", type=float, default=DELAY,
                        help=f"Seconds between requests (default: {DELAY})")
    args = parser.parse_args()

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Downloading Commons images ===")
    dl, sk, _ = download_commons_images(args.delay)
    print(f"  Done: {dl} downloaded, {sk} already present")

    total = len(list(IMAGE_DIR.iterdir()))
    print(f"\nTotal images in {IMAGE_DIR}: {total}")


if __name__ == "__main__":
    main()

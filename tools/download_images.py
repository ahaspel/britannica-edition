"""Download Commons images for local hosting and EPUB prep.

Downloads all images tracked in the ArticleImage table
(upload.wikimedia.org URLs, PNG/JPG/SVG/GIF).

DjVu page crops are handled separately by tools/download_djvu_crops.py.

Downloads to data/derived/images/, skipping files already present.
Rate-limited to respect Wikimedia servers.

Rate limiting: 3s between requests, 15-minute cooldown after every 350 requests
(matches the Wikisource fetch policy).  Falls back to Special:FilePath on 404
(handles case-sensitivity mismatches in Commons URLs).

Usage:
    python tools/download_images.py [--delay SECONDS]
"""

import argparse
import io
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

IMAGE_DIR = Path("data/derived/images")
DELAY = 3  # seconds between requests
BATCH_SIZE = 350  # requests before cooldown
COOLDOWN = 15 * 60  # 15 minutes

SESSION = requests.Session()
SESSION.headers["User-Agent"] = (
    "Britannica11Bot/1.0 (https://britannica11.org; scholarly digital edition)"
)


# ---------------------------------------------------------------------------
# Commons images (from DB)
# ---------------------------------------------------------------------------

def _local_filename(commons_url: str) -> str:
    """Derive a local filename from a Commons URL, preserving the original name."""
    name = commons_url.rsplit("/", 1)[-1]
    from urllib.parse import unquote
    return unquote(name)


def _cooldown_if_needed(request_count: int) -> int:
    """Pause for COOLDOWN seconds after every BATCH_SIZE requests. Returns new count."""
    if request_count > 0 and request_count % BATCH_SIZE == 0:
        print(f"  — Batch of {BATCH_SIZE} reached, cooling down for {COOLDOWN // 60} minutes...")
        time.sleep(COOLDOWN)
    return request_count


RATE_LIMIT_WAIT = 3600  # 1 hour, matches fetch_wikisource_pages.py


def _download_with_retry(url: str, local_path: Path, local_name: str,
                         max_retries: int = 3) -> bool:
    """Download a file, retrying on 429 rate-limit errors.

    Sleeps 1 hour on 429 (same as the Wikisource fetch pipeline).
    Returns True if downloaded successfully, False on permanent failure.
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
            print(f"  FAILED: {local_name} — {e}", file=sys.stderr)
            return False
    print(f"  FAILED (still rate-limited after {max_retries} retries): {local_name}",
          file=sys.stderr)
    return False


def download_commons_images(delay: float, request_count: int = 0) -> tuple[int, int, int]:
    """Download all Commons images from the ArticleImage table.

    Returns (downloaded, skipped, request_count).
    """
    from britannica.db.session import SessionLocal
    from britannica.db.models import ArticleImage

    session = SessionLocal()
    images = session.query(ArticleImage.commons_url, ArticleImage.filename).distinct().all()
    session.close()

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    skipped = 0

    for commons_url, orig_filename in images:
        local_name = _local_filename(commons_url)
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

        # Use Special:FilePath — case-insensitive, handles redirects
        url = (
            f"https://commons.wikimedia.org/wiki/Special:FilePath/"
            f"{quote(local_name)}?width=1200"
        )

        request_count += 1
        request_count = _cooldown_if_needed(request_count)

        if _download_with_retry(url, local_path, local_name):
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

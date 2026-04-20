"""Download and crop DjVu page images from Wikimedia Commons.

Scans raw wikitext for {{Css image crop}} templates referencing .djvu files,
downloads the full rendered page from Wikimedia, then crops each region with
Pillow using the template parameters (bSize, cWidth, cHeight, oTop, oLeft).

Saves cropped images to data/derived/images/ with deterministic names:
    djvu_vol{NN}_page{NNNN}_crop{N}.jpg

Rate limiting: 3s between requests, 1-hour sleep on 429 (matches
fetch_wikisource_pages.py and download_images.py).

Usage:
    python tools/download_djvu_crops.py [--delay SECONDS]
"""

import argparse
import hashlib
import io
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests
from PIL import Image
from io import BytesIO

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

RAW_DIR = Path("data/raw/wikisource")
IMAGE_DIR = Path("data/derived/images")
CACHE_DIR = Path("data/derived/images/.djvu_cache")
DELAY = 3  # seconds between requests
RATE_LIMIT_WAIT = 3600  # 1 hour on 429

SESSION = requests.Session()
SESSION.headers["User-Agent"] = (
    "Britannica11Bot/1.0 (https://britannica11.org; scholarly digital edition)"
)

# ---------------------------------------------------------------------------
# Parse {{Css image crop}} from raw wikitext
# ---------------------------------------------------------------------------

_CSS_CROP_PATTERN = re.compile(
    r"\{\{Css image crop\s*\n(.*?)\}\}", re.DOTALL | re.IGNORECASE
)


def _parse_param(body: str, name: str) -> str:
    """Extract a named parameter from a template body."""
    m = re.search(rf"\|{name}\s*=\s*([^\n|]*)", body, re.IGNORECASE)
    return m.group(1).strip() if m else ""


_RAW_IMAGE_DJVU_RE = re.compile(
    # Matches any reference to a DjVu page in wikisource that should
    # become a full-page figure:
    #   {{raw image|EB1911 - Volume 24.djvu/1037}}
    #   [[File:EB1911 - Volume 20.djvu-694.png|…]]  (typo variant)
    # Handles spaces-or-underscores + canonical `/` or typo `-`.
    r"(?:\{\{\s*raw\s+image\s*\||\[\[(?:File|Image):\s*)"
    r"(EB1911\s+-\s+Volume\s+\d+\.djvu)"
    r"(?:/|-)"
    r"(\d+)"
    r"(?:\.png)?",
    re.IGNORECASE,
)

# {{Css image crop|Image = EB1911 - Volume 24.djvu|Page = 988|...}}
# SHIPBUILDING Figs 6/9/10 and others use this for DjVu crops. The
# transform converts these to ``{{raw image|...djvu/N}}`` but the
# downloader also needs to see them to provision full-page renders.
_CSS_CROP_DJVU_RE = re.compile(
    r"\{\{\s*Css\s+image\s+crop\b[^}]*?"
    r"Image\s*=\s*(EB1911\s+-\s+Volume\s+\d+\.djvu)[^}]*?"
    r"Page\s*=\s*(\d+)[^}]*\}\}",
    re.IGNORECASE | re.DOTALL,
)


def scan_full_page_refs() -> list[dict]:
    """Scan all raw wikitext for bare DjVu page references that
    should be rendered as full-page figures (no cropping).

    Returns list of dicts with keys: djvu_file, page, volume.
    Unlike crop refs, these produce a plain
    `djvu_vol{NN}_page{NNNN}.jpg` filename that serves as the
    figure's own image.
    """
    found = {}
    # Scan corrections.json `to` text first — these add DjVu refs that
    # don't appear in raw wikitext (e.g. TOOL p30's corrections replace
    # unproofed OCR garbage with {{raw image|…djvu/P}} or [[File:…
    # djvu/P|…]]).
    corrections_path = Path("data/corrections.json")
    if corrections_path.exists():
        try:
            corrections = json.loads(corrections_path.read_text(encoding="utf-8"))
            for key, entries in corrections.items():
                if key.startswith("_") or not isinstance(entries, list):
                    continue
                for c in entries:
                    to_text = c.get("to", "") or ""
                    for m in list(_RAW_IMAGE_DJVU_RE.finditer(to_text)) + list(
                            _CSS_CROP_DJVU_RE.finditer(to_text)):
                        djvu_file = m.group(1).strip()
                        if not djvu_file.lower().endswith(".djvu"):
                            djvu_file += ".djvu"
                        page = int(m.group(2))
                        vol_match = re.search(r"Volume (\d+)", djvu_file)
                        if not vol_match:
                            continue
                        k = (djvu_file, page)
                        if k not in found:
                            found[k] = {
                                "djvu_file": djvu_file,
                                "page": page,
                                "volume": int(vol_match.group(1)),
                            }
        except Exception:
            pass
    for vol_dir in sorted(RAW_DIR.iterdir()):
        if not vol_dir.is_dir():
            continue
        for page_file in sorted(vol_dir.glob("*.json")):
            try:
                data = json.loads(page_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            raw = data.get("raw_text", "")
            for m in list(_RAW_IMAGE_DJVU_RE.finditer(raw)) + list(
                    _CSS_CROP_DJVU_RE.finditer(raw)):
                djvu_file = re.sub(r"\s+", " ", m.group(1)).strip() + ".djvu"
                # The regex captured `.djvu` with no leading space; the
                # group ends at `.djvu`, then we add it back.
                djvu_file = m.group(1).strip()
                if not djvu_file.lower().endswith(".djvu"):
                    djvu_file += ".djvu"
                page = int(m.group(2))
                vol_match = re.search(r"Volume (\d+)", djvu_file)
                if not vol_match:
                    continue
                key = (djvu_file, page)
                if key not in found:
                    found[key] = {
                        "djvu_file": djvu_file,
                        "page": page,
                        "volume": int(vol_match.group(1)),
                    }
    return list(found.values())


def _full_page_output_path(volume: int, page: int) -> Path:
    """Local filename used by the viewer for a full-page DjVu render."""
    return IMAGE_DIR / f"djvu_vol{volume:02d}_page{page:04d}.jpg"


def _commons_source_url(filename: str) -> str:
    """Build the direct Commons URL for a non-DjVu source image."""
    name = filename.replace(" ", "_")
    md5 = hashlib.md5(name.encode()).hexdigest()
    return (
        f"https://upload.wikimedia.org/wikipedia/commons/"
        f"{md5[0]}/{md5[:2]}/{quote(name)}"
    )


def download_commons_source(filename: str, delay: float) -> Path | None:
    """Download a Commons PNG/JPG source referenced by a
    `{{Css image crop}}` template.  Saves under the original filename
    (spaces → underscores) so the existing commonsUrl() path in the
    viewer resolves to this local file."""
    local_name = filename.replace(" ", "_")
    out = IMAGE_DIR / local_name
    if out.exists() and out.stat().st_size > 0:
        return out
    url = _commons_source_url(filename)
    try:
        resp = SESSION.get(url, timeout=60)
        if resp.status_code == 429:
            print("  Rate limited, sleeping 1 hour...")
            time.sleep(RATE_LIMIT_WAIT)
            resp = SESSION.get(url, timeout=60)
        if resp.status_code == 404:
            # Special:FilePath fallback (case-insensitive lookup).
            fp = ("https://commons.wikimedia.org/wiki/Special:"
                  f"FilePath/{quote(filename.replace(' ', '_'))}")
            resp = SESSION.get(fp, timeout=60, allow_redirects=True)
        resp.raise_for_status()
        out.write_bytes(resp.content)
        return out
    except requests.RequestException as e:
        print(f"  FAILED: {filename} — {e}", file=sys.stderr)
        return None


def scan_wikitext() -> list[dict]:
    """Scan all raw wikitext for `{{Css image crop}}` references.

    Returns list of dicts with keys:
        djvu_file, page, bSize, cWidth, cHeight, oTop, oLeft, volume

    Non-DjVu sources (e.g. `Image=EB1911 Alphabet - Plate.png`) are
    skipped here — `scan_non_djvu_crop_sources()` handles those, as
    they only need the source image downloaded, not a page-rendered
    crop.
    """
    found = []
    for vol_dir in sorted(RAW_DIR.iterdir()):
        if not vol_dir.is_dir():
            continue
        for page_file in sorted(vol_dir.glob("*.json")):
            data = json.loads(page_file.read_text(encoding="utf-8"))
            raw = data.get("raw_text", "")
            for m in _CSS_CROP_PATTERN.finditer(raw):
                body = m.group(1)
                image = _parse_param(body, "Image")
                if not image.endswith(".djvu"):
                    continue
                page_str = _parse_param(body, "Page")
                if not page_str:
                    continue
                found.append({
                    "djvu_file": image,
                    "page": int(page_str),
                    "bSize": int(_parse_param(body, "bSize") or "600"),
                    "cWidth": int(_parse_param(body, "cWidth") or "600"),
                    "cHeight": int(_parse_param(body, "cHeight") or "600"),
                    "oTop": int(_parse_param(body, "oTop") or "0"),
                    "oLeft": int(_parse_param(body, "oLeft") or "0"),
                    "volume": data["volume"],
                })
    return found


def scan_non_djvu_crop_sources() -> list[str]:
    """Scan for `{{Css image crop}}` templates whose `Image` is a
    regular Commons PNG/JPG (not a `.djvu` file).  The source image
    itself needs to be downloaded so any consumer (the viewer's
    full-plate fallback) can resolve it.

    Returns deduped list of Commons filenames.
    """
    seen: set[str] = set()
    for vol_dir in sorted(RAW_DIR.iterdir()):
        if not vol_dir.is_dir():
            continue
        for page_file in sorted(vol_dir.glob("*.json")):
            try:
                data = json.loads(
                    page_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            raw = data.get("raw_text", "")
            for m in _CSS_CROP_PATTERN.finditer(raw):
                image = _parse_param(m.group(1), "Image")
                if image and not image.endswith(".djvu"):
                    seen.add(image)
    return sorted(seen)


# ---------------------------------------------------------------------------
# Download full DjVu page renders
# ---------------------------------------------------------------------------

def _djvu_page_url(djvu_filename: str, page: int, width: int = 1200) -> str:
    """Build the Wikimedia Commons thumb URL for a single DjVu page."""
    name = djvu_filename.replace(" ", "_")
    md5 = hashlib.md5(name.encode()).hexdigest()
    encoded = quote(name)
    return (
        f"https://upload.wikimedia.org/wikipedia/commons/thumb/"
        f"{md5[0]}/{md5[:2]}/{encoded}/"
        f"page{page}-{width}px-{encoded}.jpg"
    )


def _cache_path(djvu_file: str, page: int) -> Path:
    """Path for the cached full-page render."""
    vol_match = re.search(r"Volume (\d+)", djvu_file)
    vol = int(vol_match.group(1)) if vol_match else 0
    return CACHE_DIR / f"vol{vol:02d}_page{page:04d}_full.jpg"


def download_page(djvu_file: str, page: int, delay: float,
                  max_retries: int = 3) -> Path | None:
    """Download a full DjVu page render, with retry on 429.

    Returns the cache path if successful, None on failure.
    """
    cached = _cache_path(djvu_file, page)
    if cached.exists() and cached.stat().st_size > 0:
        return cached

    url = _djvu_page_url(djvu_file, page)
    for attempt in range(max_retries):
        try:
            resp = SESSION.get(url, timeout=60)
            if resp.status_code == 429:
                print(f"  Rate limited, sleeping 1 hour...")
                time.sleep(RATE_LIMIT_WAIT)
                continue
            resp.raise_for_status()
            cached.write_bytes(resp.content)
            return cached
        except requests.RequestException as e:
            print(f"  FAILED: {djvu_file} page {page} — {e}", file=sys.stderr)
            return None

    print(f"  FAILED (still rate-limited after {max_retries} retries): "
          f"{djvu_file} page {page}", file=sys.stderr)
    return None


# ---------------------------------------------------------------------------
# Crop
# ---------------------------------------------------------------------------

def crop_region(full_page_path: Path, crop: dict, crop_index: int) -> Path | None:
    """Crop a region from a full-page render using Css image crop parameters.

    The template works by scaling the source image to bSize width, then
    taking a cWidth x cHeight viewport offset by oTop/oLeft.

    Returns the output path if successful.
    """
    vol = crop["volume"]
    page = crop["page"]
    out_name = f"djvu_vol{vol:02d}_page{page:04d}_crop{crop_index}.jpg"
    out_path = IMAGE_DIR / out_name
    if out_path.exists() and out_path.stat().st_size > 0:
        return out_path

    try:
        img = Image.open(full_page_path)
    except Exception as e:
        print(f"  FAILED to open {full_page_path}: {e}", file=sys.stderr)
        return None

    # Scale factor: the template assumes the image is rendered at bSize width
    bSize = crop["bSize"]
    scale = img.width / bSize

    left = int(crop["oLeft"] * scale)
    top = int(crop["oTop"] * scale)
    right = int((crop["oLeft"] + crop["cWidth"]) * scale)
    bottom = int((crop["oTop"] + crop["cHeight"]) * scale)

    # Clamp to image bounds
    right = min(right, img.width)
    bottom = min(bottom, img.height)

    cropped = img.crop((left, top, right, bottom))
    cropped.save(out_path, "JPEG", quality=90)
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Download and crop DjVu page images")
    parser.add_argument("--delay", type=float, default=DELAY,
                        help=f"Seconds between requests (default: {DELAY})")
    args = parser.parse_args()

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Scanning wikitext for DjVu crop references ===")
    crops = scan_wikitext()
    print(f"  Found {len(crops)} crop regions")

    print("=== Scanning wikitext for full-page DjVu refs ===")
    full_refs = scan_full_page_refs()
    print(f"  Found {len(full_refs)} full-page references")

    print("=== Scanning wikitext for non-DjVu crop sources ===")
    non_djvu_sources = scan_non_djvu_crop_sources()
    print(f"  Found {len(non_djvu_sources)} non-DjVu crop sources")

    # Group by (djvu_file, page) to download each page only once
    from collections import defaultdict
    pages = defaultdict(list)
    for crop in crops:
        key = (crop["djvu_file"], crop["page"])
        pages[key].append(crop)

    print(f"  {len(pages)} unique pages to download")
    print()

    print("=== Downloading and cropping ===")
    downloaded = 0
    skipped_pages = 0
    cropped = 0
    skipped_crops = 0
    failed = 0

    for (djvu_file, page), page_crops in sorted(pages.items()):
        cached = _cache_path(djvu_file, page)
        if cached.exists() and cached.stat().st_size > 0:
            skipped_pages += 1
        else:
            result = download_page(djvu_file, page, args.delay)
            if result is None:
                failed += 1
                continue
            downloaded += 1
            print(f"  [{downloaded}] {djvu_file} page {page} "
                  f"({result.stat().st_size:,} bytes)")
            time.sleep(args.delay)

        # Crop all regions from this page
        for i, crop in enumerate(page_crops):
            out = crop_region(cached, crop, i)
            if out is None:
                failed += 1
            elif out.stat().st_size > 0:
                # Check if it was already there
                cropped += 1

    # Full-page refs — download each as djvu_volNN_pageNNNN.jpg
    # directly under IMAGE_DIR.  These don't need cropping.
    full_downloaded = 0
    full_skipped = 0
    full_failed = 0
    print()
    print("=== Downloading full-page DjVu refs ===")
    for ref in sorted(full_refs, key=lambda r: (r["volume"], r["page"])):
        out_path = _full_page_output_path(ref["volume"], ref["page"])
        if out_path.exists() and out_path.stat().st_size > 0:
            full_skipped += 1
            continue
        cached = _cache_path(ref["djvu_file"], ref["page"])
        if not cached.exists() or cached.stat().st_size == 0:
            result = download_page(
                ref["djvu_file"], ref["page"], args.delay)
            if result is None:
                full_failed += 1
                continue
            time.sleep(args.delay)
        # Copy the cached full-page render to the output path.
        out_path.write_bytes(cached.read_bytes())
        full_downloaded += 1
        print(f"  [{full_downloaded}] {out_path.name} "
              f"({out_path.stat().st_size:,} bytes)")

    # Non-DjVu crop sources (ALPHABET Plate.png etc.) — download the
    # source image itself.  The viewer's commonsUrl() resolves local
    # files by filename; crops aren't generated (crop regions of PNG
    # sources are currently rendered by CSS in the viewer or shown
    # as the whole source).
    source_downloaded = 0
    source_skipped = 0
    source_failed = 0
    print()
    print("=== Downloading non-DjVu crop sources ===")
    for src in non_djvu_sources:
        local_name = src.replace(" ", "_")
        out = IMAGE_DIR / local_name
        if out.exists() and out.stat().st_size > 0:
            source_skipped += 1
            continue
        result = download_commons_source(src, args.delay)
        if result is None:
            source_failed += 1
            continue
        source_downloaded += 1
        print(f"  [{source_downloaded}] {out.name} "
              f"({out.stat().st_size:,} bytes)")
        time.sleep(args.delay)

    print()
    print(f"Pages downloaded: {downloaded} (skipped: {skipped_pages})")
    print(f"Crops produced: {cropped}")
    print(f"Full-page refs: {full_downloaded} downloaded, "
          f"{full_skipped} skipped, {full_failed} failed")
    print(f"Non-DjVu sources: {source_downloaded} downloaded, "
          f"{source_skipped} skipped, {source_failed} failed")
    print(f"Failed: {failed}")
    total_djvu = len(list(IMAGE_DIR.glob("djvu_*.jpg")))
    print(f"Total DjVu images in {IMAGE_DIR}: {total_djvu}")


if __name__ == "__main__":
    main()

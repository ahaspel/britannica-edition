"""Extract page scans from IA JP2 zips.

Maps Wikisource page numbers → IA leaf numbers using a per-volume offset.

Usage:
    python tools/extract_scan.py <volume> <page>
    python tools/extract_scan.py <volume> <start_page> <end_page>
    python tools/extract_scan.py --article <TITLE> <volume>
"""
from wikikit.corpora import current_corpus
import argparse
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, "src")
from wikikit.export.pages import leaf_for_ws   # noqa: E402
from eb1911.scans import leaf_image   # noqa: E402

OUT_DIR = current_corpus().derived("scans")


def extract_leaf(vol: int, leaf: int, out_name: str, width: int = 1200) -> Path | None:
    """Extract a single leaf by its IA leaf number, downsampled to `width` for
    the site. Returns output path or None."""
    out = OUT_DIR / out_name
    if out.exists() and out.stat().st_size > 0:
        return out
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        img = leaf_image(vol, leaf)
        if img.width > width:
            ratio = width / img.width
            img = img.resize((width, int(img.height * ratio)), Image.LANCZOS)
        img.save(out, "JPEG", quality=85)
        return out
    except Exception as e:
        print(f"  Failed: {e}", file=sys.stderr)
        return None


def extract_page(vol: int, ws_page: int, width: int = 1200) -> Path | None:
    """Extract a single page scan by WS page number. Returns output path or None."""
    # The ws -> leaf translation is the exporter's (`export.pages.leaf_for_ws`):
    # the leaf a scan is extracted at must be the leaf the article JSON already
    # claims in its `leaf_start`/`leaf_end`, and two copies cannot promise that.
    leaf = leaf_for_ws(vol, ws_page)
    out_name = f"vol{vol:02d}_leaf{leaf:04d}.jpg"
    return extract_leaf(vol, leaf, out_name, width)


def main():
    parser = argparse.ArgumentParser(description="Extract page scans from IA JP2 zips")
    parser.add_argument("--article", action="store_true")
    parser.add_argument("--width", type=int, default=1200)
    parser.add_argument("args", nargs="+")
    args = parser.parse_args()

    if args.article:
        title = args.args[0]
        vol = int(args.args[1])
        from wikikit.db.session import SessionLocal
        from wikikit.db.models import Article
        s = SessionLocal()
        a = s.query(Article).filter(
            Article.title == title.upper(), Article.volume == vol
        ).first()
        if not a:
            print(f"Article '{title}' not found in volume {vol}")
            return
        pages = range(a.page_start, a.page_end + 1)
        s.close()
        print(f"Extracting pages {a.page_start}-{a.page_end} for {a.title}")
    elif len(args.args) == 2:
        vol = int(args.args[0])
        pages = [int(args.args[1])]
    elif len(args.args) == 3:
        vol = int(args.args[0])
        pages = range(int(args.args[1]), int(args.args[2]) + 1)
    else:
        parser.error("Provide volume + page, or --article title volume")
        return

    if not args.article:
        vol = int(args.args[0])

    for page in pages:
        out = extract_page(vol, page, args.width)
        if out:
            print(f"  vol {vol} page {page}: {out} ({out.stat().st_size:,} bytes)")
        else:
            print(f"  vol {vol} page {page}: FAILED")


if __name__ == "__main__":
    main()

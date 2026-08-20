"""Extract page scans from IA JP2 zips.

Maps Wikisource page numbers → IA leaf numbers using a per-volume offset.

Usage:
    python tools/extract_scan.py <volume> <page>
    python tools/extract_scan.py <volume> <start_page> <end_page>
    python tools/extract_scan.py --article <TITLE> <volume>
"""
import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, "src")
from britannica.export.pages import leaf_for_ws   # noqa: E402

SCAN_DIR = Path("data/raw/ia_scans")
OUT_DIR = Path("data/derived/scans")

def _ia_identifier(vol: int) -> str:
    if vol in (3, 5, 6, 7, 8, 9, 11, 12, 13):
        return f"encyclopaediabrit{vol:02d}chisrich"
    elif vol == 20:
        return "10689.10192"
    else:
        return f"encyclopaediabri{vol:02d}chisrich"


def _find_zip(vol: int) -> Path | None:
    ident = _ia_identifier(vol)
    expected = SCAN_DIR / f"{ident}_jp2.zip"
    if expected.exists():
        return expected
    for f in SCAN_DIR.iterdir():
        if f.suffix == ".zip" and f"vol{vol:02d}" in f.name.lower():
            return f
    return None


def extract_leaf(vol: int, leaf: int, out_name: str, width: int = 1200) -> Path | None:
    """Extract a single leaf by its IA leaf number. Returns output path or None."""
    out = OUT_DIR / out_name
    if out.exists() and out.stat().st_size > 0:
        return out

    zip_path = _find_zip(vol)
    if not zip_path:
        print(f"  No JP2 zip for volume {vol}", file=sys.stderr)
        return None

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        z = zipfile.ZipFile(zip_path)
        ident = zip_path.stem.replace("_jp2", "")
        jp2_name = f"{ident}_jp2/{ident}_{leaf:04d}.jp2"
        if jp2_name not in z.namelist():
            print(f"  Leaf {leaf} not in {zip_path.name}", file=sys.stderr)
            return None
        jp2_data = z.read(jp2_name)
        img = Image.open(io.BytesIO(jp2_data))
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
        from britannica.db.session import SessionLocal
        from britannica.db.models import Article
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

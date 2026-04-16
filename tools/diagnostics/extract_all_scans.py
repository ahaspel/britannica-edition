"""Extract all page scans from IA JP2 zips for all 29 volumes.

One-time batch job. Saves as vol{NN}_leaf{NNNN}.jpg in data/derived/scans/.
Skips existing files. Safe to re-run.

Usage:
    python tools/extract_all_scans.py [--width 1200]
"""
import io
import json
import sys
import zipfile
from pathlib import Path

from PIL import Image

SCAN_DIR = Path("data/raw/ia_scans")
OUT_DIR = Path("data/derived/scans")


def _ia_identifier(vol):
    if vol in (3, 5, 6, 7, 8, 9, 11, 12, 13):
        return f"encyclopaediabrit{vol:02d}chisrich"
    elif vol == 20:
        return "10689.10192"
    else:
        return f"encyclopaediabri{vol:02d}chisrich"


def _find_zip(vol):
    ident = _ia_identifier(vol)
    expected = SCAN_DIR / f"{ident}_jp2.zip"
    if expected.exists():
        return expected
    for f in SCAN_DIR.iterdir():
        if f.suffix == ".zip" and "jp2" in f.name:
            if f"{vol:02d}" in f.name:
                return f
    return None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--width", type=int, default=1200)
    parser.add_argument("--vol", type=int, help="Extract single volume")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    volumes = [args.vol] if args.vol else range(1, 30)

    total_extracted = 0
    total_skipped = 0
    total_failed = 0

    for vol in volumes:
        zip_path = _find_zip(vol)
        if not zip_path:
            print(f"Vol {vol}: no JP2 zip found")
            continue

        try:
            z = zipfile.ZipFile(zip_path)
        except zipfile.BadZipFile:
            print(f"Vol {vol}: bad zip file")
            continue

        ident = zip_path.stem.replace("_jp2", "")
        jp2_files = sorted([n for n in z.namelist() if n.endswith(".jp2")])

        vol_extracted = 0
        vol_skipped = 0
        vol_failed = 0

        for jp2_name in jp2_files:
            leaf = int(jp2_name.rsplit("_", 1)[1].replace(".jp2", ""))
            out = OUT_DIR / f"vol{vol:02d}_leaf{leaf:04d}.jpg"

            if out.exists() and out.stat().st_size > 0:
                vol_skipped += 1
                continue

            try:
                jp2_data = z.read(jp2_name)
                img = Image.open(io.BytesIO(jp2_data))
                if img.width > args.width:
                    ratio = args.width / img.width
                    img = img.resize(
                        (args.width, int(img.height * ratio)), Image.LANCZOS
                    )
                img.save(out, "JPEG", quality=85)
                vol_extracted += 1
            except Exception as e:
                print(f"  Vol {vol} leaf {leaf}: {e}", file=sys.stderr)
                vol_failed += 1

        total_extracted += vol_extracted
        total_skipped += vol_skipped
        total_failed += vol_failed
        print(f"Vol {vol:2d}: {vol_extracted} extracted, {vol_skipped} skipped, {vol_failed} failed ({len(jp2_files)} total)")

    print(f"\nDone: {total_extracted} extracted, {total_skipped} skipped, {total_failed} failed")


if __name__ == "__main__":
    main()

"""OCR printed page numbers from scan images.

Reads the top corners of each scan to extract the printed page number.
Writes results to data/derived/ocr_page_numbers.json.

Usage:
    python tools/ocr_page_numbers.py [--vol N]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

SCAN_DIR = Path("data/derived/scans")
OUT = Path("data/derived/ocr_page_numbers.json")

# Per-volume page-number location (top_frac, bottom_frac) of the page.
# Default (IA chisrich scans): number sits in the top 6% of the page.
# Vol 20 (DLI Bengal): huge top margin, number sits 7-14% down.
DEFAULT_BAND = (0.0, 0.06)
VOL_BAND = {
    20: (0.07, 0.14),
}


def ocr_page_number(scan_path: Path, vol: int) -> int | None:
    """Extract printed page number from the page-number band."""
    img = Image.open(scan_path)
    w, h = img.size
    top_frac, bot_frac = VOL_BAND.get(vol, DEFAULT_BAND)
    y0 = int(h * top_frac)
    y1 = int(h * bot_frac)

    # Try top-right (odd pages), top-left (even pages)
    for crop in [
        img.crop((int(w * 0.75), y0, w, y1)),
        img.crop((0, y0, int(w * 0.25), y1)),
    ]:
        # Digits-only whitelist — page numbers are pure digits, and
        # restricting the character set dramatically reduces noise.
        text = pytesseract.image_to_string(
            crop, config="--psm 7 -c tessedit_char_whitelist=0123456789"
        ).strip()
        m = re.search(r"\b(\d{1,4})\b", text)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 1200:
                return n
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vol", type=int, help="Process single volume")
    args = parser.parse_args()

    # Load existing results
    if OUT.exists():
        result = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        result = {}

    volumes = [args.vol] if args.vol else range(1, 29)

    for vol in volumes:
        vol_key = str(vol)
        pad_vol = f"{vol:02d}"

        # Find all leaf scans for this volume
        scans = sorted(SCAN_DIR.glob(f"vol{pad_vol}_leaf*.jpg"))
        if not scans:
            print(f"Vol {vol}: no scans found")
            continue

        vol_map = result.get(vol_key, {})
        found = 0
        skipped = 0

        for scan in scans:
            leaf = int(re.search(r"leaf(\d+)", scan.name).group(1))
            leaf_key = str(leaf)

            # Skip if already done
            if leaf_key in vol_map:
                skipped += 1
                continue

            num = ocr_page_number(scan, vol)
            if num is not None:
                vol_map[leaf_key] = num
                found += 1

        result[vol_key] = vol_map
        total = len(vol_map)
        print(f"Vol {vol:2d}: {found} new, {skipped} cached, {total} total "
              f"(of {len(scans)} scans)")

        # Save after each volume
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"\nResults saved to {OUT}")


if __name__ == "__main__":
    main()

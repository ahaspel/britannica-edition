"""Classify scan pages as text vs plate using image analysis + OCR cross-check.

For each scan, computes:
  1. Image analysis: dark pixel ratio and strip variance
  2. OCR presence: whether a number is found in the page corners

A plate page has: high dark ratio + high variance AND no OCR number.
A text page has: low/uniform dark ratio OR has an OCR number.

Output: data/derived/scan_classification.json
Format: {"vol": {"leaf": {"type": "text"|"plate"|"blank", "dark": N, "var": N, "ocr": N|null}}}

Usage:
    python tools/classify_scans.py [--vol N]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

SCAN_DIR = Path("data/derived/scans")
OUT = Path("data/derived/scan_classification.json")

# Thresholds from empirical testing
PLATE_DARK_MIN = 0.25
PLATE_VAR_MIN = 0.01
BLANK_DARK_MAX = 0.05


def classify_scan(path: Path) -> dict:
    """Classify a single scan page."""
    img = Image.open(path).convert("L")
    arr = np.array(img)
    h, w = arr.shape

    # Body region (exclude margins)
    body = arr[int(h * 0.05):int(h * 0.95), int(w * 0.05):int(w * 0.95)]
    body_dark = float((body < 128).mean())

    # Strip variance
    n_strips = 20
    strip_h = body.shape[0] // n_strips
    densities = [(body[i * strip_h:(i + 1) * strip_h] < 128).mean()
                 for i in range(n_strips)]
    variance = float(np.var(densities))

    # OCR: check corners for a page number
    ocr_num = None
    crop_h = int(h * 0.06)
    for crop in [
        img.crop((int(w * 0.8), 0, w, crop_h)),
        img.crop((0, 0, int(w * 0.2), crop_h)),
    ]:
        text = pytesseract.image_to_string(crop).strip()
        m = re.search(r"\b(\d{1,4})\b", text)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 1200:
                ocr_num = n
                break

    # Classify
    looks_plate = body_dark > PLATE_DARK_MIN and variance > PLATE_VAR_MIN
    looks_blank = body_dark < BLANK_DARK_MAX

    if looks_blank:
        page_type = "blank"
    elif looks_plate and ocr_num is None:
        # Looks like a plate AND no page number found
        page_type = "plate"
    else:
        page_type = "text"

    return {
        "type": page_type,
        "dark": round(body_dark, 4),
        "var": round(variance, 6),
        "ocr": ocr_num,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vol", type=int, help="Process single volume")
    args = parser.parse_args()

    # Load existing results
    if OUT.exists():
        result = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        result = {}

    volumes = [args.vol] if args.vol else range(1, 30)

    for vol in volumes:
        vol_key = str(vol)
        pad_vol = f"{vol:02d}"

        scans = sorted(SCAN_DIR.glob(f"vol{pad_vol}_leaf*.jpg"))
        if not scans:
            continue

        vol_data = result.get(vol_key, {})
        new = 0
        cached = 0
        counts = {"text": 0, "plate": 0, "blank": 0}

        for i, scan in enumerate(scans):
            leaf = re.search(r"leaf(\d+)", scan.name).group(1)

            if leaf in vol_data:
                counts[vol_data[leaf]["type"]] += 1
                cached += 1
                continue

            info = classify_scan(scan)
            vol_data[leaf] = info
            counts[info["type"]] += 1
            new += 1

            if (i + 1) % 100 == 0:
                print(f"  Vol {vol}: {i + 1}/{len(scans)}...", file=sys.stderr)

        result[vol_key] = vol_data
        print(f"Vol {vol:2d}: {counts['text']} text, {counts['plate']} plate, "
              f"{counts['blank']} blank ({new} new, {cached} cached)")

        # Save after each volume
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"\nResults saved to {OUT}")


if __name__ == "__main__":
    main()

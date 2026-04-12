"""OCR the vol 29 (Index) scans that Wikisource hasn't transcribed.

Wikisource has only ~7% of vol 29 transcribed, but the scans are high
quality and the text is dense index entries (topic → vol-page refs).
Tesseract reads these pages well. We OCR every scan whose Wikisource
page JSON has empty `raw_text`, so the xref alias builder has enough
entries to cover the whole A-Z index.

Output: data/derived/vol29_ocr.json  (ws_str -> full-page OCR text)

Usage:
    python tools/ocr_vol29_index.py
"""
import json
import re
from pathlib import Path

import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

RAW_DIR = Path("data/raw/wikisource/vol_29")
SCAN_DIR = Path("data/derived/scans")
OUT = Path("data/derived/vol29_ocr.json")

# ws-to-leaf offset for vol 29 per LEAF_OFFSET.
LEAF_OFFSET = 6


def main() -> None:
    existing: dict[str, str] = {}
    if OUT.exists():
        existing = json.loads(OUT.read_text(encoding="utf-8"))

    result = dict(existing)
    done = 0
    total_empty = 0
    new_ocr = 0

    for f in sorted(RAW_DIR.glob("vol29-page*.json")):
        ws_match = re.search(r"page(\d{4})", f.name)
        if not ws_match:
            continue
        ws = int(ws_match.group(1))
        ws_str = str(ws)

        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue

        if d.get("raw_text", "").strip():
            # Wikisource has content; skip
            continue

        total_empty += 1

        if ws_str in result and result[ws_str]:
            continue  # already OCR'd

        leaf = ws + LEAF_OFFSET
        scan_path = SCAN_DIR / f"vol29_leaf{leaf:04d}.jpg"
        if not scan_path.exists():
            continue

        try:
            img = Image.open(scan_path)
            text = pytesseract.image_to_string(img)
        except Exception as e:
            print(f"  ws {ws}: OCR failed: {e}")
            continue

        result[ws_str] = text
        new_ocr += 1
        done += 1
        if done % 50 == 0:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(f"  progress: {done} pages OCR'd ({total_empty} empty so far)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nTotal empty Wikisource pages: {total_empty}")
    print(f"Newly OCR'd this run: {new_ocr}")
    print(f"Total OCR entries: {len(result)}")
    print(f"Wrote to {OUT}")


if __name__ == "__main__":
    main()

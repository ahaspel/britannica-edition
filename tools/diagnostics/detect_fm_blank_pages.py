"""Detect the first non-blank front matter scan for each volume.

Output: data/derived/fm_first_content.json
  {"1": 6, "2": 4, ...}  # volume → first fm index with content

Uses PIL to check if a scan is nearly uniform (blank paper).
"""
import io
import json
import sys
from pathlib import Path

from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

SCAN_DIR = Path("data/derived/scans")
OUT = Path("data/derived/fm_first_content.json")


def is_blank(path: Path) -> bool:
    """True if the scan is a mostly-blank page (cover paper / end paper).

    Heuristic: count dark (ink) pixels. Blank pages have almost no
    pixels darker than a reasonable ink threshold. Even a title page
    with just a few lines of text has thousands of dark pixels.
    Paper texture / shadows stay in the mid-grays and don't reach
    ink-level darkness.
    """
    try:
        img = Image.open(path).convert("L")
        img.thumbnail((400, 400))
        pixels = list(img.getdata())
        if not pixels:
            return True
        # Ink is typically below 80 (0=black, 255=white). Paper/shadow
        # usually stays above 130.
        dark_ratio = sum(1 for p in pixels if p < 80) / len(pixels)
        # All-black separator pages (DLI Bengal vol 20) have ~100% dark
        # pixels — treat as blank (skip in first-content detection).
        if dark_ratio > 0.8:
            return True
        # Less than 0.1% dark pixels → blank paper. Even a sparse
        # title page has thousands of ink pixels — far above noise.
        return dark_ratio < 0.001
    except Exception:
        return True


def main() -> None:
    result: dict[str, int] = {}
    for vol in range(1, 30):
        padded = f"{vol:02d}"
        fm_scans = sorted(SCAN_DIR.glob(f"vol{padded}_fm*.jpg"))
        if not fm_scans:
            continue
        first_content = None
        blanks = 0
        for scan in fm_scans:
            # Extract index from filename vol01_fmNN.jpg
            idx = int(scan.stem.rsplit("fm", 1)[-1])
            if is_blank(scan):
                blanks += 1
            else:
                first_content = idx
                break
        if first_content is not None:
            result[str(vol)] = first_content
            print(f"  vol{padded}: first content = fm{first_content:02d} "
                  f"(skipped {blanks} blank)")
        else:
            print(f"  vol{padded}: all {len(fm_scans)} fm scans are blank?")

    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()

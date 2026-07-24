"""Process Rumsey Stieler atlas zips into servable map assets.

Each zip (data/raw/maps/*.zip) holds {id}.txt metadata + {id}.jpg — a ~104MP
photo of the OPEN ATLAS: cream page on a gray table, dark cover edges, and the
light fore-edge page stack to one side.  We crop to the printed PAGE (not
tight to the neat-line — the engraved title and "GOTHA: JUSTUS PERTHES"
imprint stay visible), then emit:

    data/images/maps/stieler_{slug}_full.jpg   full-res crop (the download asset)
    data/images/maps/stieler_{slug}.jpg        display copy (~3200px long side)
    <scratch>/stieler_{slug}_check.png         crop-overlay preview for review

Auto-crop: threshold the bright page against the darker surround on a
downsample, take the largest connected bright component, snap its bbox.  The
fore-edge stack is excluded by requiring near-full column coverage (the stack
is bright but striated).  EVERY crop is eyeballed via the _check preview
before the assets are trusted — the registry only references reviewed files.

  uv run python tools/maps/process_stieler.py           # all zips
  uv run python tools/maps/process_stieler.py Schweiz   # name filter
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None

RAW = Path("data/raw/maps")
OUT = Path("data/images/maps")
SCRATCH = Path(os.environ.get("CLAUDE_SCRATCHPAD", tempfile.gettempdir()))

# zip-name fragment -> our slug (aligned with the encbr11_{slug} ids)
SLUGS = [
    ("Schweiz", "switzerland"),
    ("Russland,_Bl._1", "russia_1"),
    ("Russland,_Bl._2", "russia_2"),
    ("Vorder-Indien", "india"),
    ("China", "china"),
    ("Japan", "japan_and_korea"),
    ("Afrika", "africa"),
    ("Europa", "europe"),
    ("Australien", "australia"),
]

DISPLAY_LONG_SIDE = 3200


def autocrop_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    """Page bbox at full-res coordinates."""
    small = img.convert("L").copy()
    small.thumbnail((1200, 1200))
    a = np.asarray(small, dtype=np.uint8)
    # The page is the brightest broad region; Otsu-ish split on the upper mode.
    thr = int(a.mean() + (a.max() - a.mean()) * 0.35)
    bright = a > thr
    # Column/row coverage: the page spans near-full columns; the fore-edge
    # stack is bright but only over part of the height (and striated).
    col_cov = bright.mean(axis=0)
    row_cov = bright.mean(axis=1)
    cols = np.where(col_cov > 0.55)[0]
    rows = np.where(row_cov > 0.55)[0]
    if not len(cols) or not len(rows):      # fallback: whole frame
        return 0, 0, img.width, img.height
    sx = img.width / a.shape[1]
    sy = img.height / a.shape[0]
    pad = 4
    x0 = max(0, int((cols[0] - pad) * sx))
    x1 = min(img.width, int((cols[-1] + pad) * sx))
    y0 = max(0, int((rows[0] - pad) * sy))
    y1 = min(img.height, int((rows[-1] + pad) * sy))
    return x0, y0, x1, y1


def process(zp: Path) -> None:
    slug = next((s for frag, s in SLUGS if frag in zp.name), None)
    if slug is None:
        print(f"  SKIP (no slug rule): {zp.name}")
        return
    z = zipfile.ZipFile(zp)
    jpg = [n for n in z.namelist() if n.endswith(".jpg")][0]
    with z.open(jpg) as fh:
        img = Image.open(fh)
        img.load()
    x0, y0, x1, y1 = autocrop_bbox(img)
    crop = img.crop((x0, y0, x1, y1))

    OUT.mkdir(parents=True, exist_ok=True)
    full = OUT / f"stieler_{slug}_full.jpg"
    crop.save(full, quality=88, optimize=True)
    disp = crop.copy()
    disp.thumbnail((DISPLAY_LONG_SIDE, DISPLAY_LONG_SIDE))
    disp_path = OUT / f"stieler_{slug}.jpg"
    disp.save(disp_path, quality=85, optimize=True)

    # review preview: the uncropped frame with the crop rectangle drawn
    prev = img.copy()
    prev.thumbnail((1100, 1100))
    d = ImageDraw.Draw(prev)
    fx = prev.width / img.width
    fy = prev.height / img.height
    d.rectangle([x0 * fx, y0 * fy, x1 * fx, y1 * fy], outline="red", width=4)
    check = SCRATCH / f"stieler_{slug}_check.png"
    prev.save(check)
    print(f"  {slug:16} crop {x1-x0}x{y1-y0} of {img.width}x{img.height}  "
          f"full={full.stat().st_size//1024//1024}MB "
          f"disp={disp_path.stat().st_size//1024}KB  check={check.name}")


def main() -> None:
    pat = sys.argv[1] if len(sys.argv) > 1 else ""
    for zp in sorted(RAW.glob("*.zip")):
        if pat and pat.lower() not in zp.name.lower():
            continue
        process(zp)


if __name__ == "__main__":
    main()

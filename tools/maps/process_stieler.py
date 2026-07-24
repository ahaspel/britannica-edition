"""Process Rumsey Stieler atlas zips into servable map assets.

Each zip (data/raw/maps/*.zip) holds {id}.txt metadata + {id}.jpg — either a
~104MP photo of the OPEN ATLAS (cream page on a gray table, dark cover edges,
fore-edge page stack to one side) or an already-cropped Rumsey composite.
We crop the atlas photos to the printed PAGE (not tight to the neat-line —
the engraved title and "GOTHA: JUSTUS PERTHES" imprint stay visible), then
emit:

    data/images/maps/stieler_{slug}_full.jpg     full-res crop (the download asset)
    data/images/maps/stieler_{slug}.jpg          display copy (~3200px long side)
    data/raw/maps/_previews/..._check.png        crop-overlay preview for review

Crops are HAND-TUNED fractions per map (CROPS), verified against the
_check previews — auto-detection was tried and defeated by content-dark
maps (Schweiz hachures match the gray table) and the bright fore-edge
stack; nine fixed images deserve nine reviewed numbers, not a heuristic.
A new zip without a CROPS entry emits full-frame + a preview to measure.

  uv run python tools/maps/process_stieler.py           # all zips
  uv run python tools/maps/process_stieler.py Schweiz   # name filter
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None

RAW = Path("data/raw/maps")
OUT = Path("data/images/maps")
PREVIEWS = RAW / "_previews"          # review artifacts, outside deploy sync

# zip-name fragment -> our slug (aligned with the encbr11_{slug} ids).
# First match wins: "Japan,_Korea" must precede "China" — zip 65 is
# "Japan,_Korea_und_Ost-China" and would otherwise land on china.
SLUGS = [
    ("Schweiz", "switzerland"),
    ("Russland,_Bl._1", "russia_1"),
    ("Russland,_Bl._2", "russia_2"),
    ("Vorder-Indien", "india"),
    ("Japan,_Korea", "japan_and_korea"),
    ("China", "china"),
    ("Afrika", "africa"),
    ("Europa", "europe"),
    ("Australien", "australia"),
]

# Hand-tuned page crops as (x0, y0, x1, y1) fractions of the full frame,
# measured on the _check previews.  australia is a Rumsey composite,
# already cropped edge-to-edge.
CROPS = {
    "switzerland":     (0.033, 0.031, 0.886, 0.964),
    "russia_1":        (0.038, 0.023, 0.908, 0.970),
    "russia_2":        (0.037, 0.026, 0.905, 0.969),
    "india":           (0.034, 0.024, 0.905, 0.966),
    "china":           (0.034, 0.023, 0.901, 0.965),
    "japan_and_korea": (0.034, 0.024, 0.905, 0.966),
    "africa":          (0.118, 0.024, 0.914, 0.976),
    "europe":          (0.062, 0.023, 0.862, 0.978),
    "australia":       (0.0, 0.0, 1.0, 1.0),
}

DISPLAY_LONG_SIDE = 3200


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

    fr = CROPS.get(slug)
    tag = ""
    if fr is None:
        fr = (0.0, 0.0, 1.0, 1.0)
        tag = "  NO CROPS ENTRY — full frame, measure the preview"
    x0 = int(fr[0] * img.width)
    y0 = int(fr[1] * img.height)
    x1 = int(fr[2] * img.width)
    y1 = int(fr[3] * img.height)
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
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    check = PREVIEWS / f"stieler_{slug}_check.png"
    prev.save(check)
    print(f"  {slug:16} crop {x1-x0}x{y1-y0} of {img.width}x{img.height}  "
          f"full={full.stat().st_size//1024//1024}MB "
          f"disp={disp_path.stat().st_size//1024}KB  check={check.name}{tag}")


def main() -> None:
    pat = sys.argv[1] if len(sys.argv) > 1 else ""
    for zp in sorted(RAW.glob("*.zip")):
        if pat and pat.lower() not in zp.name.lower():
            continue
        process(zp)


if __name__ == "__main__":
    main()

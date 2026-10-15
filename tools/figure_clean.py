"""A figure set from its Commons region, with print the region cannot leave
out wiped from it: the region as cut (`download_djvu_crops.crop_region`, from
the cached render), each rectangle whitened, saved as a file of its own and
set in the region's place.  Recorded with the page (`provenance.cleaned`:
item -> the region, the rectangles, why), so the image can be made again
from the record, never only found on disk.

The case (2026-10-15): SEWERAGE's Fig. 20 (vol 24 p. 739) — its pull chain
hangs beside its printed caption, so no rectangle takes the drawing without
the caption, and the caption is set as text below it.

    uv run python tools/figure_clean.py VOL:PAGE ITEM X0,Y0,X1,Y1 [...] --why "…"

PAGE is the PRINTED page; rectangles in pixels of the region as cut.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent / "pipeline"))
from download_djvu_crops import _cache_path, crop_region  # noqa: E402

from eb1911.scans import _printed  # noqa: E402
from wikikit.corpora import current_corpus  # noqa: E402
from wikikit.image_assets import local_image_filename  # noqa: E402
from wikikit.scan import supplied  # noqa: E402
from wikikit.wikitext import template_param  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")


def region_crop(css: str, volume: int) -> Path:
    body = css.strip().removeprefix("{{").removesuffix("}}")
    crop = {k: int(template_param(body, k)) for k in ("bSize", "cWidth", "cHeight", "oTop", "oLeft")}
    crop.update(djvu_file=template_param(body, "Image"), page=int(template_param(body, "Page")), volume=volume)
    path = crop_region(_cache_path(crop["djvu_file"], crop["page"]), crop, 0)
    if path is None:
        raise SystemExit(f"could not cut the region from the cached render: {css!r}")
    return path


def clean(vol: int, ws: int, item: str, rects: list[tuple[int, ...]], why: str) -> Path:
    payload = supplied.read(vol, ws)
    p = payload["provenance"]
    done = (p.get("cleaned") or {}).get(item)
    css = done["region"] if done else p["regions"][item]       # the region as first set
    img = Image.open(region_crop(css, vol)).convert("RGB")
    draw = ImageDraw.Draw(img)
    for r in rects:
        draw.rectangle(r, fill="white")
    name = f"eb1911 v{vol:02d} p{ws:04d} {item} cleaned.png"
    out = current_corpus().images() / local_image_filename(name)
    img.save(out, optimize=True)
    width = int(template_param(css.strip().removeprefix("{{").removesuffix("}}"), "cWidth"))
    p.setdefault("cleaned", {})[item] = {"region": css, "whitened": [list(r) for r in rects], "why": why}
    p["regions"][item] = f"[[File:{name}|center|{width}px]]"
    supplied.write(supplied.reassemble(payload))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page", help="VOL:PAGE, the printed page")
    ap.add_argument("item", help="the figure's item name (c1f1 …)")
    ap.add_argument("rects", nargs="+", help="X0,Y0,X1,Y1 to whiten")
    ap.add_argument("--why", required=True)
    a = ap.parse_args()
    vol, printed = (int(x) for x in a.page.split(":"))
    ws = next(int(w) for w, pg in _printed("printed_pages.json")[str(vol)].items() if pg == printed)
    rects = [tuple(int(x) for x in r.split(",")) for r in a.rects]
    print(clean(vol, ws, a.item, rects, a.why))
    return 0


if __name__ == "__main__":
    sys.exit(main())

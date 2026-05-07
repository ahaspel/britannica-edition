"""Corpus-wide regression check for plate extraction.

For every page in data/raw/wikisource/* whose heading template carries
an explicit `Plate N.` token, run `_transform_plate` on the raw_text
and compare the image count against the count of `[[Image:]]`/
`[[File:]]` links in the source.  Any page where transformed images <
source images is a regression candidate (we're losing pictures).

Also reports total plate count, caption coverage (fraction of
extracted images that have a non-empty caption), and per-volume
breakdown.

Usage:
    python tools/pipeline/check_plate_extraction.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "src")

from britannica.pipeline.stages.detect_boundaries import (
    _extract_plate_number,
    _heading_names_plate,
)
from britannica.pipeline.stages.transform_articles import _transform_plate


_IMG_RE = re.compile(r"\[\[(?:File|Image):", re.IGNORECASE)
_BODY_IMG_RE = re.compile(r"\{\{IMG:([^|}]+)(?:\|([^}]*))?\}\}")


def main() -> None:
    raw_root = Path("data/raw/wikisource")
    by_vol: dict[int, dict] = {}
    losses: list[tuple] = []

    for vol_dir in sorted(raw_root.iterdir()):
        if not vol_dir.is_dir():
            continue
        m = re.match(r"vol_(\d+)$", vol_dir.name)
        if not m:
            continue
        vol = int(m.group(1))
        by_vol[vol] = {"plates": 0, "src_imgs": 0, "out_imgs": 0,
                       "out_captioned": 0, "no_img": 0, "lost": 0}

        for fp in sorted(vol_dir.iterdir()):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            raw = data.get("raw_text") or ""
            if not raw:
                continue
            if not _heading_names_plate(raw):
                continue
            src_n = len(_IMG_RE.findall(raw))
            try:
                body = _transform_plate(raw)
            except Exception as e:
                losses.append((vol, fp.name, "ERROR", str(e), src_n, 0, 0))
                continue
            out_imgs = list(_BODY_IMG_RE.finditer(body))
            out_n = len(out_imgs)
            out_cap = sum(1 for m in out_imgs if (m.group(2) or "").strip())

            d = by_vol[vol]
            d["plates"] += 1
            d["src_imgs"] += src_n
            d["out_imgs"] += out_n
            d["out_captioned"] += out_cap
            if out_n == 0 and src_n > 0:
                d["no_img"] += 1
                losses.append((vol, fp.name,
                               _extract_plate_number(raw) or "?",
                               "no images extracted", src_n, out_n, out_cap))
            elif out_n < src_n:
                d["lost"] += 1
                losses.append((vol, fp.name,
                               _extract_plate_number(raw) or "?",
                               f"lost {src_n - out_n} of {src_n}",
                               src_n, out_n, out_cap))

    # Per-volume summary
    print("Volume |  Plates |  Src img | Out img | Captioned | NoImg | Lost")
    print("-------+---------+----------+---------+-----------+-------+------")
    tot = {"plates": 0, "src_imgs": 0, "out_imgs": 0,
           "out_captioned": 0, "no_img": 0, "lost": 0}
    for vol in sorted(by_vol):
        d = by_vol[vol]
        for k in tot:
            tot[k] += d[k]
        cap_pct = (d["out_captioned"] / d["out_imgs"] * 100
                   if d["out_imgs"] else 0.0)
        print(f"  vol{vol:02d} | {d['plates']:7} | {d['src_imgs']:8} | "
              f"{d['out_imgs']:7} | {cap_pct:7.1f}%  | {d['no_img']:5} | "
              f"{d['lost']:4}")
    cap_pct = (tot["out_captioned"] / tot["out_imgs"] * 100
               if tot["out_imgs"] else 0.0)
    print("-------+---------+----------+---------+-----------+-------+------")
    print(f"  TOTAL | {tot['plates']:7} | {tot['src_imgs']:8} | "
          f"{tot['out_imgs']:7} | {cap_pct:7.1f}%  | {tot['no_img']:5} | "
          f"{tot['lost']:4}")

    if losses:
        print()
        print(f"Loss list ({len(losses)} pages):")
        for vol, fn, pl, msg, src_n, out_n, out_cap in losses[:50]:
            print(f"  vol{vol:02d}  {fn}  Plate {pl}  "
                  f"src={src_n} out={out_n} cap={out_cap}  {msg}")
        if len(losses) > 50:
            print(f"  ... and {len(losses) - 50} more")


if __name__ == "__main__":
    main()

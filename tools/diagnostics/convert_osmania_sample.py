"""One-off: convert the Osmania vol-20 JP2s to small JPGs for visual review.

Source: data extracted from in.ernet.dli.2015.85243_jp2.tar
Output: data/derived/scans_osmania/vol20_leafNNNN.jpg, ~800px wide.
"""
from __future__ import annotations

import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

SRC = Path(r"D:\work\britannica-edition\osmania_extract\2015.85243.The-Encyclopaedia-Britannica-Eleventh-Edition-Vol-Xx_jp2")
OUT = Path(r"D:\work\britannica-edition\data\derived\scans_osmania")
PREFIX = "2015.85243.The-Encyclopaedia-Britannica-Eleventh-Edition-Vol-Xx_"


def convert(idx: int) -> tuple[int, str]:
    src = SRC / f"{PREFIX}{idx:04d}.jp2"
    if not src.exists():
        return idx, "missing"
    dst = OUT / f"vol20_leaf{idx + 1:04d}.jpg"  # leaf is 1-based
    if dst.exists():
        return idx, "skip"
    img = Image.open(src)
    img.thumbnail((900, 1200))
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(dst, "JPEG", quality=78, optimize=True)
    return idx, "ok"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    indices = sorted(int(p.stem.rsplit("_", 1)[-1]) for p in SRC.glob("*.jp2"))
    print(f"Converting {len(indices)} leaves...")
    done = 0
    with ProcessPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(convert, i) for i in indices]
        for fut in as_completed(futures):
            i, status = fut.result()
            done += 1
            if done % 100 == 0:
                print(f"  {done}/{len(indices)}", file=sys.stderr)
    print("Done.")


if __name__ == "__main__":
    main()

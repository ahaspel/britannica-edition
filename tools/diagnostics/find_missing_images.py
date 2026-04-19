"""Audit exported articles for image references whose source files are
missing on disk.

For every article JSON in ``data/derived/articles``, collects image
filenames from two places:

* ``{{IMG:filename}}`` markers in the body text (what the viewer renders)
* ``images[*].filename`` entries in the JSON (the article image gallery)

Each filename is mapped to its expected path under ``data/derived/images``
(spaces→underscores; SVGs get a ``.png`` suffix because the download
script rasterizes them).  Filenames that resolve to ``http(s)://…``
URLs are skipped — those are inline-hosted assets (score images,
ornaments) that don't live in our image directory.

Usage:
    uv run python tools/diagnostics/find_missing_images.py
    uv run python tools/diagnostics/find_missing_images.py --verbose
    uv run python tools/diagnostics/find_missing_images.py --limit 50

Output is grouped by volume with a summary at the end.  Exit code is 0
regardless (this is a diagnostic, not a gate) — wire it into a gate
separately if we want to block deploys on missing images.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

ART_DIR = "data/derived/articles"
IMG_DIR = "data/derived/images"

IMG_MARKER_RE = re.compile(r"\{\{IMG:([^|}]+)(?:\|[^}]*)?\}\}")


def disk_name(filename: str) -> str:
    """Translate a Commons-style filename to its local on-disk filename."""
    name = filename.replace(" ", "_")
    if name.lower().endswith(".svg"):
        name = name + ".png"
    return name


def is_remote(filename: str) -> bool:
    return filename.startswith("http://") or filename.startswith("https://")


def collect_refs(article: dict) -> set[str]:
    """Return every image filename referenced by the article."""
    refs: set[str] = set()
    body = article.get("body") or ""
    for m in IMG_MARKER_RE.finditer(body):
        refs.add(m.group(1).strip())
    for img in article.get("images") or []:
        fn = (img.get("filename") or "").strip()
        if fn:
            refs.add(fn)
    for plate in article.get("plates") or []:
        for fn in (plate.get("images") or []):
            if isinstance(fn, str) and fn.strip():
                refs.add(fn.strip())
    return refs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0,
                    help="Stop after N missing references (0 = no limit).")
    ap.add_argument("--verbose", action="store_true",
                    help="Also list expected disk paths for each miss.")
    ap.add_argument("--json", action="store_true",
                    help="Emit machine-readable JSON instead of a report.")
    ap.add_argument("--article", type=str, default=None,
                    help="Only audit this article filename (e.g. "
                         "01-0481-s8-AIR-ENGINE.json).")
    args = ap.parse_args()

    if not os.path.isdir(ART_DIR):
        print(f"article dir not found: {ART_DIR}", file=sys.stderr)
        return 2
    if not os.path.isdir(IMG_DIR):
        print(f"image dir not found: {IMG_DIR}", file=sys.stderr)
        return 2

    on_disk: set[str] = set(os.listdir(IMG_DIR))

    files = sorted(os.listdir(ART_DIR))
    if args.article:
        files = [f for f in files if f == args.article]
        if not files:
            print(f"no article matched {args.article!r}", file=sys.stderr)
            return 2

    misses_by_vol: dict[int, list[tuple[str, str, str]]] = defaultdict(list)
    total_refs = 0
    total_misses = 0
    seen_misses: set[tuple[str, str]] = set()
    unique_missing_files: set[str] = set()

    for fname in files:
        if not fname.endswith(".json"):
            continue
        if fname in ("index.json", "contributors.json"):
            continue
        path = os.path.join(ART_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                article = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        refs = collect_refs(article)
        if not refs:
            continue
        vol = int(article.get("volume") or 0)
        title = article.get("title") or fname
        for ref in sorted(refs):
            total_refs += 1
            if is_remote(ref):
                continue
            disk = disk_name(ref)
            if disk in on_disk:
                continue
            total_misses += 1
            unique_missing_files.add(disk)
            key = (fname, ref)
            if key in seen_misses:
                continue
            seen_misses.add(key)
            misses_by_vol[vol].append((fname, title, ref))
            if args.limit and total_misses >= args.limit:
                break
        if args.limit and total_misses >= args.limit:
            break

    if args.json:
        out = {
            "total_refs": total_refs,
            "total_misses": total_misses,
            "unique_missing_files": sorted(unique_missing_files),
            "by_volume": {
                str(v): [
                    {"article_file": f, "title": t, "filename": r}
                    for f, t, r in misses
                ]
                for v, misses in sorted(misses_by_vol.items())
            },
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print(f"Articles scanned: {len(files)}")
    print(f"Total image references: {total_refs}")
    print(f"Missing-file references: {total_misses}")
    print(f"Unique missing filenames: {len(unique_missing_files)}")
    print()
    if not misses_by_vol:
        print("No missing images.")
        return 0

    for vol in sorted(misses_by_vol):
        misses = misses_by_vol[vol]
        print(f"=== Volume {vol:02d} ({len(misses)} misses) ===")
        for article_file, title, ref in misses:
            print(f"  {article_file}  [{title}]")
            print(f"    missing: {ref}")
            if args.verbose:
                print(f"    expected on disk: {IMG_DIR}/{disk_name(ref)}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

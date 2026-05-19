"""Snapshot the article-body JSON exports under
``data/derived/articles/`` to a timestamped backup directory.

The exports under ``data/derived/articles/`` are the production
pipeline's output for the corpus.  Any rebuild that runs the export
stage will overwrite them — but they're our cleanest baseline for
verifying that future pipeline changes don't regress arbitrary
articles.  This tool freezes a copy somewhere the rebuild process
doesn't touch.

Default destination: ``data/baselines/articles-YYYYMMDD/`` (created
fresh; will refuse to overwrite an existing backup of the same date).

Usage::

    .venv/Scripts/python tools/diagnostics/baseline_article_bodies.py
    .venv/Scripts/python tools/diagnostics/baseline_article_bodies.py --tag pre-redistribution
"""
from __future__ import annotations

import io
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                               errors="replace")


SRC = Path("data/derived/articles")
BACKUP_PARENT = Path("data/baselines")


def main() -> int:
    args = sys.argv[1:]
    tag = None
    while args:
        a = args.pop(0)
        if a == "--tag" and args:
            tag = args.pop(0)
        else:
            print(f"Unknown arg: {a}", file=sys.stderr)
            return 2

    if not SRC.exists():
        print(f"Source not found: {SRC}", file=sys.stderr)
        return 1

    stamp = datetime.now().strftime("%Y%m%d")
    name = f"articles-{stamp}" + (f"-{tag}" if tag else "")
    dst = BACKUP_PARENT / name

    if dst.exists():
        print(f"Backup directory already exists: {dst}")
        print("Refusing to overwrite.  Use a different --tag or "
              "delete the existing directory first.")
        return 1

    BACKUP_PARENT.mkdir(parents=True, exist_ok=True)

    # Count source files first so we have a progress target.
    src_files = sorted(SRC.glob("*.json"))
    n_total = len(src_files)
    print(f"Backing up {n_total} JSON exports from {SRC}")
    print(f"  → {dst}")

    t0 = time.time()
    shutil.copytree(SRC, dst)
    elapsed = time.time() - t0

    backed_up = sum(1 for _ in dst.glob("*.json"))
    total_bytes = sum(p.stat().st_size for p in dst.glob("*.json"))
    print(f"Done in {elapsed:.1f}s.  "
          f"{backed_up} files, {total_bytes / (1024 * 1024):.1f} MB.")

    if backed_up != n_total:
        print(f"WARNING: source had {n_total} files but backup "
              f"contains {backed_up}.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

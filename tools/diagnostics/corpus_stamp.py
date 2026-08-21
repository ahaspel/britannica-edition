"""Did this corpus come from a COMPLETED rebuild, and has anything touched it since?

    uv run python tools/diagnostics/corpus_stamp.py --write   # end of a green rebuild
    uv run python tools/diagnostics/corpus_stamp.py --check    # start of a deploy

THE GAP THIS FILLS.  `deploy.sh` ships whatever is in `data/derived/` and says so
in its own header: "run it ONLY right after a clean FULL rebuild you have
reviewed: a partial or stale tree here is exactly the partial deploy the project
forbids".  That was an instruction to a human, and instructions get judged in the
moment by whoever wants to ship — which is the moment least able to judge them.

`build_stamp.py` does NOT cover this: it fingerprints the bytes on disk for
cache-busting, so it describes a contaminated corpus just as faithfully as a
clean one.

WHAT IT CATCHES, all real events from this project:
  * a single-article look-render written back into the corpus
    (`tools/render_article.py` writes `data/derived/articles/<id>.json`, and its
    output SKIPS xref resolution — it is not pipeline output).  Three such files
    silently entered a pre-rebuild fingerprint and made a clean rebuild read as a
    3-article regression until the baseline was re-derived.
  * a per-volume rebuild (`rebuild_volume.py`) leaving the rest of the corpus at
    the previous build.
  * a rebuild that died mid-phase, leaving a half-written export directory.
  * deploying after editing `src/` without rebuilding.

MTIME IS THE SIGNAL, deliberately.  The question is not "do these bytes hash the
same" but "has anything WRITTEN here since the build finished", and a write is
exactly what mtime records.  `data/derived/` is gitignored, so nothing rewrites
these files as a side effect of ordinary git work; a changed mtime means a tool
ran.  It is also ~40ms over 37k files rather than the ~90s a content hash costs,
which matters: a gate people are tempted to skip is a gate that gets skipped.

The stamp is written ONLY after every phase-7 gate has passed, so its existence
means "a full rebuild finished green", not merely "a rebuild ran".
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "data" / "derived" / "articles"
STAMP = ROOT / "data" / "derived" / "rebuild_stamp.json"


def corpus_signature() -> tuple[str, int]:
    """(hash, file count) over every article JSON's name, size and mtime."""
    h = hashlib.sha256()
    n = 0
    for entry in sorted(os.scandir(EXPORT_DIR), key=lambda e: e.name):
        if not entry.name.endswith(".json"):
            continue
        st = entry.stat()
        h.update(f"{entry.name}:{st.st_size}:{st.st_mtime_ns}\n".encode())
        n += 1
    return h.hexdigest(), n


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true",
                   help="record the current corpus as rebuild output (end of a green build)")
    g.add_argument("--check", action="store_true",
                   help="fail if the corpus has changed since the stamp")
    args = ap.parse_args()

    if not EXPORT_DIR.is_dir():
        print(f"  no export directory at {EXPORT_DIR}", file=sys.stderr)
        return 1

    sig, count = corpus_signature()

    if args.write:
        STAMP.write_text(json.dumps({
            "signature": sig,
            "articles": count,
            "finished": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        }, indent=2) + "\n", encoding="utf-8")
        print(f"  corpus stamped: {count:,} articles, {sig[:16]}")
        return 0

    if not STAMP.is_file():
        print("  REFUSING TO DEPLOY: no rebuild stamp.", file=sys.stderr)
        print("  This corpus was not produced by a rebuild that finished its gates.",
              file=sys.stderr)
        print("  Run ./tools/rebuild_all.sh, then deploy the build you reviewed.",
              file=sys.stderr)
        return 1

    prev = json.loads(STAMP.read_text(encoding="utf-8"))
    if prev.get("signature") != sig:
        print("  REFUSING TO DEPLOY: the corpus has changed since the last "
              "completed rebuild.", file=sys.stderr)
        print(f"    stamped {prev.get('articles')} articles at {prev.get('finished')}",
              file=sys.stderr)
        print(f"    on disk {count:,} articles now", file=sys.stderr)
        print("  Something wrote to data/derived/articles after the build — a "
              "single-article", file=sys.stderr)
        print("  re-render, a per-volume rebuild, or an interrupted run.  Shipping "
              "this is the", file=sys.stderr)
        print("  partial deploy the project forbids: rebuild in full, then deploy.",
              file=sys.stderr)
        return 1

    print(f"  corpus matches the rebuild that finished {prev.get('finished')} "
          f"({count:,} articles)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

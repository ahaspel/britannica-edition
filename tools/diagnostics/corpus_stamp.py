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
import pathlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
# STDERR TOO.  Every refusal message goes to stderr, and this is the one file
# whose output is read at the worst possible moment — when a deploy has just
# been stopped.  Un-reconfigured, the em-dashes in those messages arrive as
# mojibake on a Windows console, which makes a correct refusal look like a
# broken tool.
sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "data" / "derived" / "articles"
DERIVED = ROOT / "data" / "derived"
STAMP = DERIVED / "rebuild_stamp.json"

# EVERYTHING ELSE A DEPLOY SHIPS out of data/derived, taken from what
# `deploy.sh` actually uploads.  The articles were the only thing covered until
# 2026-08-24, and the gap was demonstrated rather than theorised: running ONE
# pipeline stage by hand rewrote `classified_toc.json` with a pre-disambiguation
# version — the exact "a tool ran after the build finished" case this file
# exists to catch — and the check passed, because the file sits outside the
# scanned directory.  A deploy would have shipped it with every gate green.
#
# NOT `scans/`: those are inputs that no rebuild regenerates, so including them
# would fail the check whenever a scan was added, which is not what this asks.
SHIPPED_FILES = [
    # regenerated every rebuild and read client-side to build links and pages
    "classified_toc.json", "printed_pages.json", "printed_pages_leaf.json",
    "scan_map.json", "fm_first_content.json", "volumes.json",
    # the public bundles
    "eb1911-corpus.tar.gz", "eb1911-corpus.tar.gz.sha256",
    "eb1911-maps.tar.gz", "eb1911-maps.tar.gz.sha256",
    "eb1911-tei.tar.gz", "eb1911-tei.tar.gz.sha256",
]
SHIPPED_DIRS = ["download"]


def _stat_line(name: str, path: pathlib.Path) -> str:
    st = path.stat()
    return f"{name}:{st.st_size}:{st.st_mtime_ns}\n"


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


def shipped_signature() -> tuple[str, int]:
    """(hash, file count) over the OTHER derived files a deploy ships.

    A missing file is recorded as missing rather than skipped: a bundle that
    vanished between the build and the deploy is exactly as interesting as one
    that changed.
    """
    h = hashlib.sha256()
    n = 0
    for name in SHIPPED_FILES:
        f = DERIVED / name
        if f.is_file():
            h.update(_stat_line(name, f).encode())
            n += 1
        else:
            h.update(f"{name}:MISSING\n".encode())
    for d in SHIPPED_DIRS:
        base = DERIVED / d
        if not base.is_dir():
            h.update(f"{d}/:MISSING\n".encode())
            continue
        for entry in sorted(os.scandir(base), key=lambda e: e.name):
            if entry.is_file():
                h.update(_stat_line(f"{d}/{entry.name}",
                                    pathlib.Path(entry.path)).encode())
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
        ssig, scount = shipped_signature()
        STAMP.write_text(json.dumps({
            "signature": sig,
            "articles": count,
            "shipped_signature": ssig,
            "shipped_files": scount,
            "finished": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        }, indent=2) + "\n", encoding="utf-8")
        print(f"  corpus stamped: {count:,} articles, {sig[:16]}")
        print(f"  shipped files stamped: {scount}, {ssig[:16]}")
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

    # The other derived files a deploy ships.  A stamp written before this check
    # existed has no `shipped_signature`; say so rather than failing a build that
    # is otherwise sound — the next rebuild records one and it self-heals.
    if "shipped_signature" not in prev:
        print("  (stamp predates the shipped-file check; articles verified only —"
              " the next rebuild will widen it)")
    else:
        ssig, scount = shipped_signature()
        if prev["shipped_signature"] != ssig:
            print("  REFUSING TO DEPLOY: a derived file this deploy ships has "
                  "changed since the", file=sys.stderr)
            print("  last completed rebuild.", file=sys.stderr)
            print(f"    stamped {prev.get('shipped_files')} files at "
                  f"{prev.get('finished')}", file=sys.stderr)
            print(f"    on disk {scount} now", file=sys.stderr)
            print("  The ARTICLES are intact, so this is not a half-written "
                  "export — something", file=sys.stderr)
            print("  rewrote a bundle, a graph, or one of the client-side JSONs "
                  "after the build:", file=sys.stderr)
            print("  running a single pipeline stage by hand does exactly this, "
                  "and produces a", file=sys.stderr)
            print("  file that looks right and lacks whatever later phases add "
                  "to it.  Rebuild in", file=sys.stderr)
            print("  full, then deploy.", file=sys.stderr)
            return 1

    print(f"  corpus matches the rebuild that finished {prev.get('finished')} "
          f"({count:,} articles)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

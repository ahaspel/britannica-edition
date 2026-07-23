#!/usr/bin/env python3
"""Render-leak report — the honest leak oracle over the whole corpus.

    python tools/diagnostics/render_leaks.py

Reads every article's ``rendered_html`` and reports everything that survived raw
into it — guillemet markers, ``{{templates}}``, ``[[wikilinks]]``, control
sentinels — via ``britannica.render.leaks.find_render_leaks``, the SAME detector
the quality report uses.  There is no handled-marker manifest to strip against:
a known marker in the render is a recursion failure, not an exemption.

Writes per-article detail to data/derived/quality_reports/render_leaks.tsv so a
leak class can be grepped and chased to the producer/render layer that emitted it.
"""
import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
sys.stdout.reconfigure(encoding="utf-8")
from britannica.render.leaks import find_render_leaks  # noqa: E402

ART = "data/derived/articles"
OUT = Path("data/derived/quality_reports/render_leaks.tsv")


def main():
    files = [f for f in glob.glob(f"{ART}/*.json")
             if os.path.basename(f) not in ("index.json", "contributors.json")]
    cat_arts = Counter()
    cat_occ = Counter()
    marker_names = Counter()
    rows = []
    dirty = 0
    for f in files:
        rh = json.loads(open(f, encoding="utf-8").read()).get("rendered_html", "")
        leaks = find_render_leaks(rh)
        if not leaks:
            continue
        dirty += 1
        for cat in {c for c, _ in leaks}:
            cat_arts[cat] += 1
        stem = os.path.basename(f)[:-5]
        for cat, snippet in leaks:
            cat_occ[cat] += 1
            rows.append((stem, cat, snippet.replace("\t", " ").replace("\n", "\\n")))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        fh.write("stem\tcategory\tsnippet\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")

    print(f"RENDER-LEAK REPORT — {len(files)} articles, {dirty} dirty "
          f"({100 * dirty / max(1, len(files)):.2f}%)")
    for cat in ("marker", "template", "wikilink", "attr", "tag", "sentinel"):
        print(f"  {cat:9} {cat_arts[cat]:4} articles, {cat_occ[cat]:5} occurrences")
    print(f"  detail -> {OUT}")
    return 1 if dirty else 0


if __name__ == "__main__":
    sys.exit(main())

"""Diff the Python article renderer against the jsdom golden (browser-normalized).

    python tools/render/verify_render.py [<stem> ...]

For each seed: render the frozen .input.json through render_article, normalize both it and
the golden via html5lib (equal footing — browser tree-construction + entity normalization),
and compare.  Reports each seed OK / DIFF (first divergence) / ERROR.  The render port is
green for a seed when normalized Python == normalized golden.
"""
import io
import json
import os
import sys
import traceback

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))

from britannica.render.article import render_article       # noqa: E402
from britannica.render.normalize import normalize_html     # noqa: E402

RENDER_DIR = os.path.join(ROOT, "tests", "snapshots", "render")

SEEDS = [
    "01-0032-a-A", "01-0036-s5-ABACUS", "01-0042-s5-ABBEY", "01-0127-s3-ACACIA",
    "01-0157-s2-ACCUMULATOR", "01-0426-agriculture-AGRICULTURE", "01-0358-africa-AFRICA",
    "01-0571-s4-ALDEHYDES", "01-0766-s5-ALPHABET", "02-0302-s5-ARACHNIDA",
    "02-0723-s2-ARTHUR", "03-0219-s5-BAG-PIPE", "04-0375-brachiopoda-BRACHIOPODA",
    "06-0411-cithara-CITHARA", "08-0783-dynamics-DYNAMICS", "14-0147-hydromedusae-HYDROMEDUSAE",
    "14-0737-s2-INTERPOLATION", "18-0684-s2-MOLECULE", "20-0215-s3-ORDNANCE",
    "25-0840-s3-STEAM_ENGINE", "26-0933-s2-THUCYDIDES",
    "20-0023-odo-of-bayeux-ODO_OF_BAYEUX",  # title footnote (#1) — render-specific guard
]


def first_divergence(a, b):
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    return i


def main():
    stems = [a for a in sys.argv[1:] if not a.startswith("--")] or SEEDS
    ok = 0
    for stem in stems:
        try:
            article = json.load(open(os.path.join(RENDER_DIR, stem + ".input.json"), encoding="utf-8"))
            got = normalize_html(render_article(article))
            exp = normalize_html(open(os.path.join(RENDER_DIR, stem + ".html"), encoding="utf-8").read())
        except Exception as e:
            print(f"  ERROR {stem}: {e}")
            if "-v" in sys.argv:
                traceback.print_exc()
            continue
        if got == exp:
            ok += 1
            print(f"  OK    {stem}")
            continue
        i = first_divergence(got, exp)
        print(f"  DIFF  {stem}  @{i}  (got {len(got)} / golden {len(exp)} chars)")
        print(f"          exp: ...{exp[max(0, i - 20):i + 60]!r}")
        print(f"          got: ...{got[max(0, i - 20):i + 60]!r}")

    print(f"\n{ok}/{len(stems)} seeds match" + ("  ✓ UNEXPECTED=0" if ok == len(stems) else ""))
    return 0 if ok == len(stems) else 1


if __name__ == "__main__":
    sys.exit(main())

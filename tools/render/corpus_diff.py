"""Check side of the full-corpus render diff: read {stem, html} JSONL from corpus_diff.js,
render each article through the Python renderer, and diff normalize_html(python) against
normalize_html(golden) (mp-\\d+ neutralized on both sides, since the viewer window is reused).

    node tools/render/corpus_diff.js | python tools/render/corpus_diff.py

Reports matched / mismatched / errors, buckets mismatches by their first leaked marker (so a
long tail collapses to a short list of causes), and writes the full mismatch list to
corpus_diff_mismatches.tsv for follow-up.
"""
import io
import json
import os
import re
import sys
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")  # node pipes UTF-8
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))

from britannica.render.article import render_article       # noqa: E402
from britannica.render.normalize import normalize_html     # noqa: E402

ARTICLES = os.path.join(ROOT, "data", "derived", "articles")
_MP = re.compile(r"mp-\d+")
_MARKER = re.compile(r"«(/?[A-Za-z_]+)|(\x01PAGE)|(\{\{[A-Za-z]+)")


def _norm(html):
    return normalize_html(_MP.sub("mp-N", html))


def _first_divergence(a, b):
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    return i


def _cause(exp_tail, got_tail):
    m = _MARKER.search(got_tail) or _MARKER.search(exp_tail)
    return next((g for g in (m.groups() if m else ()) if g), "?") if m else "?"


def main():
    matched = 0
    mism = []
    errors = []
    n = 0
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        stem = rec["stem"]
        n += 1
        if "error" in rec:
            errors.append((stem, "viewer: " + rec["error"]))
        else:
            try:
                article = json.load(open(os.path.join(ARTICLES, stem + ".json"), encoding="utf-8"))
                got = _norm(render_article(article))
                exp = _norm(rec["html"])
            except Exception as e:  # noqa: BLE001
                errors.append((stem, "python: " + repr(e)))
            else:
                if got == exp:
                    matched += 1
                else:
                    i = _first_divergence(got, exp)
                    mism.append((stem, i, exp[i:i + 60], got[i:i + 60]))
        if n % 2000 == 0:
            sys.stderr.write(f"  diffed {n}: {matched} ok, {len(mism)} diff, {len(errors)} err\n")

    with open(os.path.join(ROOT, "corpus_diff_mismatches.tsv"), "w", encoding="utf-8") as fh:
        fh.write("stem\tpos\tcause\texp\tgot\n")
        for stem, i, exp, got in mism:
            fh.write(f"{stem}\t{i}\t{_cause(exp, got)}\t{exp!r}\t{got!r}\n")

    print(f"\n=== corpus render diff: {matched}/{n} matched"
          f" | {len(mism)} mismatched | {len(errors)} errors ===")
    causes = Counter(_cause(exp, got) for _, _, exp, got in mism)
    if causes:
        print("mismatch causes (first leaked marker):")
        for cause, cnt in causes.most_common(25):
            print(f"  {cnt:6d}  {cause}")
    if errors:
        print("\nerror kinds:")
        for kind, cnt in Counter(e.split(":")[0] + ":" + e.split(":", 1)[1].split("(")[0][:40]
                                 for _, e in errors).most_common(15):
            print(f"  {cnt:6d}  {kind}")
    print("\nsample mismatches:")
    for stem, i, exp, got in mism[:15]:
        print(f"  {stem} @{i}\n    exp {exp!r}\n    got {got!r}")
    print("\nfull list -> corpus_diff_mismatches.tsv")


if __name__ == "__main__":
    main()

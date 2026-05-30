"""Leak-scan — the totality gate and the Phase-1 worklist.

Runs the prototype `render()` over the corpus and reports any SOURCE markup that
survived into the output. A leak = an unhandled construct (recurse/carry/compile
gap). Once totality is reached, a leak ⟺ a transcription error. Until then, the
leak inventory IS the worklist: each unhandled template / marker / structure is
the next attribute to translate (producer) + handle (viewer).

De-noised: it does NOT flag `render()`'s own `<table class="figtable|data-table">`,
only RAW source markup. Output-wide; flushes progress; Ctrl-C-safe (prints the
partial report).

Usage:  uv run python tools/diagnostics/leak_scan.py [N|all]   (default N=1500)
"""
from __future__ import annotations

import io
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools" / "diagnostics"))

import render_proto
from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment
from britannica.pipeline.stages.elements._classifier import classify_article

LEAKS = [
    (re.compile(r"\{\|"), "wiki-table {|"),
    (re.compile(r'<table(?! class="(?:figtable|data-table)")', re.I), "raw <table>"),
    (re.compile(r"<poem", re.I), "<poem>"),
    (re.compile(r"\[\[(?:File|Image):", re.I), "[[File]] link"),
    (re.compile(r"\{\{"), "{{template}}"),
]
# Markers («X») are the producer's intended output, not leaks — the viewer renders
# them (step 2). A LEAK is SOURCE markup that never converted (above). Markers are
# tracked separately as the producer's vocabulary = the viewer's step-2 checklist.
_CARRIED = {"MATH", "HIERO", "SCORE"}   # compile-terminals: carried verbatim
_TMPL = re.compile(r"\{\{\s*([A-Za-z0-9][A-Za-z0-9 _-]*?)\s*[|}]")
_MARK = re.compile(r"«(/?[A-Z][A-Za-z]*)")

# Worklist triage — a PLAN, not a done. STRIP? = drop wrapper, keep inner, at the
# top (corrections.json-adjacent); it stays leaking (listed) until the strip is
# actually committed, then vanishes. TRANSCRIBE = producer→marker→viewer. "—" =
# untriaged, stays listed pending a decision. Only confident calls below.
TRIAGE = {
    "fine block": "STRIP?",            # small-font wrapper — print-economy artifact
    "eb1911 fine print": "STRIP?",
    "rh": "STRIP?",                    # running header — page furniture, not content
    "block center": "TRANSCRIBE",      # centring → «CTR»
    "csc": "TRANSCRIBE",               # centred small-caps (residual leak — investigate)
    "img float": "TRANSCRIBE",         # float layout
    "left": "TRANSCRIBE",              # alignment
    "fs": "TRANSCRIBE",                # font-size
}


def triage(name: str) -> str:
    if name in TRIAGE:
        return TRIAGE[name]
    if name.startswith("eb1911 shoulder heading"):
        return "TRANSCRIBE"            # → «SH»
    return "—"


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else "1500"
    s = SessionLocal()
    q = (s.query(Article).filter(Article.article_type != "plate")
         .order_by(Article.volume, Article.page_start))
    arts = q.all() if arg == "all" else q.limit(int(arg)).all()
    total = len(arts)
    print(f"leak-scan over {total} articles (render_proto)\n", flush=True)

    kind = Counter()
    tmpl = Counter()
    mark = Counter()
    per_label = defaultdict(lambda: [0, 0])   # label -> [elements, leaking]
    n_elem = n_leak = n_exc = 0
    sample = defaultdict(list)

    try:
        for i, a in enumerate(arts):
            if i and i % 500 == 0:
                print(f"  …{i}/{total}  elems={n_elem} leaking={n_leak}", flush=True)
            segs = (s.query(ArticleSegment).filter_by(article_id=a.id)
                    .order_by(ArticleSegment.sequence_in_article).all())
            try:
                _ph, tree = classify_article("\n\n".join(x.segment_text or "" for x in segs))
            except Exception:
                continue
            for _k, ce in tree.items():
                n_elem += 1
                per_label[ce.label][0] += 1
                try:
                    out = render_proto.render(ce.raw)
                except Exception as ex:
                    n_exc += 1
                    kind[f"EXC:{type(ex).__name__}"] += 1
                    continue
                mark.update(m for m in _MARK.findall(out)        # vocabulary, every elem
                            if m.lstrip("/").upper() not in _CARRIED and not m.startswith("/"))
                hits = [(rx.pattern, name) for rx, name in LEAKS if rx.search(out)]
                if not hits:
                    continue
                n_leak += 1
                per_label[ce.label][1] += 1
                for _pat, name in hits:
                    kind[name] += 1
                tmpl.update(t.strip().lower() for t in _TMPL.findall(out))
                names = {name for _p, name in hits}
                for name in names:
                    if len(sample[name]) < 3:
                        sample[name].append((a.title, ce.label, re.sub(r"\s+", " ", out)[:120]))
    except KeyboardInterrupt:
        print("\n[interrupted — partial report]\n", flush=True)

    s.close()
    print(f"\n===== LEAK-SCAN: {n_elem} elements, {n_leak} leaking "
          f"({100 * n_leak / max(n_elem, 1):.1f}%), {n_exc} exceptions =====")
    print("\nleak kinds:")
    for name, n in kind.most_common():
        print(f"  {n:6d}  {name}")
    print("\nWORKLIST — leaking templates, triaged [STRIP? | TRANSCRIBE | — untriaged]")
    print("  (STRIP? stays listed until the top-strip is actually committed, then vanishes)")
    for name, n in tmpl.most_common(30):
        print(f"  {n:6d}  {triage(name):11s}  {{{{{name}}}}}")
    print("\nproducer marker vocabulary (NOT leaks — viewer step-2 must render these):")
    for name, n in mark.most_common(20):
        print(f"  {n:6d}  «{name}»")
    print("\nleak rate by label (≥1% of leaking elems):")
    rows = sorted(((lab, e, lk) for lab, (e, lk) in per_label.items() if lk),
                  key=lambda r: -r[2])
    for lab, e, lk in rows[:20]:
        print(f"  {lk:5d}/{e:<5d}  {lab}")
    print("\nsamples:")
    for name, exs in sample.items():
        print(f"  [{name}]")
        for title, lab, snip in exs:
            print(f"     {title} ({lab}): {snip}")


if __name__ == "__main__":
    main()

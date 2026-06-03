"""Strip-scan — the MIRROR of leak_scan.  leak_scan catches markup that
SURVIVES into output (over-retention); this catches markup `_strip_templates`
DELETES before output (under-retention — invisible to leak_scan).

Monkeypatches `_strip_templates` to record every `{{…}}` the catch-all regex
removes, then runs the REAL producer (`_transform_text_v2`) over the corpus.
The result is the remaining worklist to drain before `_strip_templates` is a
no-op and can be deleted.  Template deletions = content concern; orphan
brace/table cleanups are reported separately (malformed-markup, lesser).

Usage: uv run python tools/diagnostics/strip_scan.py [N|all|validate] [--refresh]

`all` scans every non-plate article (cached raw, seconds after first build);
`N` scans the first N; `validate` checks the instrument on {{lh}} articles.
`--refresh` rebuilds the raw-text cache from the DB (do this after a rebuild).
"""
from __future__ import annotations
import io, re, sys
from collections import Counter
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))   # _corpus_cache
from _corpus_cache import load_corpus
from britannica.pipeline.stages.transform_articles import body_text as BT
from britannica.pipeline.stages.transform_articles import _transform_text_v2

DELETED = Counter()          # template-name -> count
SAMPLES: dict[str, str] = {}
_orig = BT._strip_templates
def _spy(text: str) -> str:
    prev, t = None, text
    while prev != t:
        prev = t
        for m in BT._STRIP_TEMPLATES_RE.findall(t):
            name = re.match(r"\{\{\s*([^|}\n]*)", m)
            key = (name.group(1).strip().lower()[:30] if name else m[:30]) or "(empty)"
            DELETED[key] += 1
            SAMPLES.setdefault(key, m[:90])
        t = BT._STRIP_TEMPLATES_RE.sub("", t)
    return _orig(text)
BT._strip_templates = _spy

def run(corpus) -> int:
    """Run the REAL producer over each (aid, vol, pg0, raw); the spy records.
    Returns the number of articles processed."""
    n = 0
    for aid, vol, pg0, raw in corpus:
        n += 1
        try:
            _transform_text_v2(raw, vol, pg0)
        except Exception:
            pass
    return n

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    refresh = "--refresh" in sys.argv
    arg = args[0] if args else "2000"
    if arg == "validate":
        # known {{lh}}-bearing articles — instrument must catch lh
        corpus = [r for r in load_corpus(contains="{{lh", refresh=refresh)][:30]
        run(corpus)
        print(f"VALIDATE on {len(corpus)} {{{{lh}}}}-bearing articles:")
        print(f"  'lh' deletions caught: {DELETED.get('lh', 0)}  (instrument {'WORKS' if DELETED.get('lh') else 'BROKEN'})")
        print(f"  top deleted here: {dict(DELETED.most_common(8))}")
    else:
        corpus = load_corpus(refresh=refresh)
        if arg != "all":
            corpus = (r for i, r in enumerate(corpus) if i < int(arg))
        n_arts = run(corpus)
        tot = sum(DELETED.values())
        print(f"=== STRIP-SCAN: {n_arts} articles, {tot} template-deletions, {len(DELETED)} distinct ===")
        print("  (each is content `_strip_templates` silently removed — invisible to leak_scan)\n")
        import collections
        dist = collections.Counter(v for v in DELETED.values())
        print('  count-distribution (how many templates have each deletion-count):')
        print('   ', dict(sorted(dist.items())))
        print(f'  templates with count>=5: {sum(1 for v in DELETED.values() if v>=5)}; count<=2 (tail): {sum(1 for v in DELETED.values() if v<=2)}')
        print()
        for name, n in DELETED.most_common():
            print(f"  {n:6d}  {{{{{name}}}}}   e.g. {SAMPLES[name]!r}")

if __name__ == "__main__":
    main()

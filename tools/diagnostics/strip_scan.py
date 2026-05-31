"""Strip-scan — the MIRROR of leak_scan.  leak_scan catches markup that
SURVIVES into output (over-retention); this catches markup `_strip_templates`
DELETES before output (under-retention — invisible to leak_scan).

Monkeypatches `_strip_templates` to record every `{{…}}` the catch-all regex
removes, then runs the REAL producer (`_transform_text_v2`) over the corpus.
The result is the remaining worklist to drain before `_strip_templates` is a
no-op and can be deleted.  Template deletions = content concern; orphan
brace/table cleanups are reported separately (malformed-markup, lesser).

Usage: uv run python tools/diagnostics/strip_scan.py [N|all|validate]
"""
from __future__ import annotations
import io, re, sys
from collections import Counter
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment, SourcePage
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

def run(article_ids, s):
    for aid in article_ids:
        a = s.get(Article, aid)
        if not a:
            continue
        segs = (s.query(ArticleSegment, SourcePage.page_number)
                .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
                .filter(ArticleSegment.article_id == aid)
                .order_by(ArticleSegment.sequence_in_article).all())
        raw = "\n".join(f"\x01PAGE:{pg}\x01{(seg.segment_text or '')}" for seg, pg in segs)
        try:
            _transform_text_v2(raw, a.volume, segs[0][1] if segs else 0)
        except Exception:
            pass

def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "2000"
    s = SessionLocal()
    if arg == "validate":
        # known {{lh}} non-plate articles — instrument must catch lh
        ids = [aid for (aid,) in s.query(ArticleSegment.article_id)
               .filter(ArticleSegment.segment_text.like("%{{lh%")).distinct()][:30]
        run(ids, s)
        print(f"VALIDATE on {len(ids)} {{{{lh}}}}-bearing articles:")
        print(f"  'lh' deletions caught: {DELETED.get('lh', 0)}  (instrument {'WORKS' if DELETED.get('lh') else 'BROKEN'})")
        print(f"  top deleted here: {dict(DELETED.most_common(8))}")
    else:
        q = s.query(Article.id).filter(Article.article_type != "plate").order_by(Article.volume, Article.page_start)
        ids = [a.id for a in (q.all() if arg == "all" else q.limit(int(arg)).all())]
        run(ids, s)
        tot = sum(DELETED.values())
        print(f"=== STRIP-SCAN: {len(ids)} articles, {tot} template-deletions, {len(DELETED)} distinct ===")
        print("  (each is content `_strip_templates` silently removed — invisible to leak_scan)\n")
        import collections
        dist = collections.Counter(v for v in DELETED.values())
        print('  count-distribution (how many templates have each deletion-count):')
        print('   ', dict(sorted(dist.items())))
        print(f'  templates with count>=5: {sum(1 for v in DELETED.values() if v>=5)}; count<=2 (tail): {sum(1 for v in DELETED.values() if v<=2)}')
        print()
        for name, n in DELETED.most_common():
            print(f"  {n:6d}  {{{{{name}}}}}   e.g. {SAMPLES[name]!r}")
    s.close()

if __name__ == "__main__":
    main()

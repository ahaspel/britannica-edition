"""render-diff — the regression / quality net (Phase-0 instrument #2).

Compares `render_proto` against the CURRENT pipeline (`_transform_text_v2`) at
the article level, on CONTENT WORDS (both sides are rendered, so markup-stripped
word-sets compare apples-to-apples). Two-way:

  REGRESSION  = content the current pipeline keeps that render_proto drops.
  IMPROVEMENT = content render_proto keeps that the current pipeline drops.
  NEUTRAL     = same content.

The Phase-3 cutover gate: render_proto must show NO regressions before it
replaces the per-label producers. During Phase 1, regressions ≈ the leak-scan
worklist (un-transcribed templates swallow their inner content) and should fall
to zero as each template is transcribed — the two instruments corroborate.

Usage:  uv run python tools/diagnostics/render_diff.py [N|all]   (default N=400)
"""
from __future__ import annotations

import io
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools" / "diagnostics"))

import render_proto
from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment
from britannica.pipeline.stages.elements._classifier import classify_article
from britannica.pipeline.stages.transform_articles import _transform_text_v2

STOP = set(
    "the and for with from this that ts em gap sc csc center fine block link nbsp "
    "emsp ensp numsp thinsp valign align colspan rowspan width style border padding "
    "right left top bottom none solid black collapse class table cols rows poem file "
    "image text font size line height auto margin brace polytonic tfrac sfrac frac sup "
    "sub smaller larger overline lang wikitable shoulder heading print nowrap div span "
    "img float figure tooltip chart".split())
_WORD = re.compile(r"[A-Za-zÀ-ɏ]{3,}")


def cw(s: str) -> Counter:
    """Rendered content-words: drop math, tags, markers, templates; keep prose."""
    s = re.sub(r"<math>.*?</math>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"«[^»]*»", " ", s)
    for _ in range(4):
        s = re.sub(r"\{\{[^{}]*\}\}", " ", s)
    return Counter(w.lower() for w in _WORD.findall(s) if w.lower() not in STOP)


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else "400"
    s = SessionLocal()
    q = (s.query(Article).filter(Article.article_type != "plate")
         .order_by(Article.volume, Article.page_start))
    arts = q.all() if arg == "all" else q.limit(int(arg)).all()
    total = len(arts)
    print(f"render-diff over {total} articles (render_proto vs current pipeline)\n", flush=True)

    n_reg = n_imp = n_neu = n_skip = 0
    lost_words = Counter()
    samples = []
    try:
        for i, a in enumerate(arts):
            if i and i % 100 == 0:
                print(f"  …{i}/{total}  reg={n_reg} imp={n_imp} neu={n_neu}", flush=True)
            segs = (s.query(ArticleSegment).filter_by(article_id=a.id)
                    .order_by(ArticleSegment.sequence_in_article).all())
            raw = "\n\n".join(x.segment_text or "" for x in segs)
            if not raw.strip():
                continue
            try:
                current = _transform_text_v2(raw, a.volume, a.page_start)
                _ph, tree = classify_article(raw)
                new = "".join(render_proto.render(ce.raw) for ce in tree.values())
            except Exception:
                n_skip += 1
                continue
            c, n = cw(current), cw(new)
            lost = {w: c[w] - n.get(w, 0) for w in c if c[w] > n.get(w, 0)}
            gained = {w: n[w] - c.get(w, 0) for w in n if n[w] > c.get(w, 0)}
            if lost:
                n_reg += 1
                lost_words.update(lost)
                if len(samples) < 12:
                    samples.append((a.title, sum(lost.values()), list(lost)[:8]))
            elif gained:
                n_imp += 1
            else:
                n_neu += 1
    except KeyboardInterrupt:
        print("\n[interrupted — partial report]\n", flush=True)

    s.close()
    judged = n_reg + n_imp + n_neu
    print(f"\n===== RENDER-DIFF: {judged} articles judged, {n_skip} skipped =====")
    print(f"  REGRESSION (render_proto drops content current keeps): {n_reg}")
    print(f"  IMPROVEMENT (render_proto keeps content current drops): {n_imp}")
    print(f"  NEUTRAL (identical content):                           {n_neu}")
    print("\ntop content-words render_proto drops (regression detail):")
    for w, n in lost_words.most_common(25):
        print(f"  {n:6d}  {w}")
    print("\nsample regressing articles (title | words-lost | examples):")
    for title, nlost, ex in sorted(samples, key=lambda r: -r[1]):
        print(f"  {nlost:4d}  {title}: {ex}")


if __name__ == "__main__":
    main()

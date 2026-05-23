"""Corpus-wide over-absorption audit for the structural figure recognizer.

Replicates the walker's left-to-right scan (wrapper entry, then image+tail) on
every figure article and records what the recognizer would absorb BEYOND the
image — the figure tail.  The recognizer only ever absorbs RECOGNIZED
structures (caption templates, `{|`/`<table>` legends, `Fig.`/attribution
lines), so the only way it can grab body is if a body block happens to open
with one of those markers.  That shows up as:

  * a long tail, or
  * a multi-block tail (the loop chained across one or more `\\n\\n`).

So we histogram tails by block-count and length and SAMPLE the longest /
most-chained ones for eyeballing.  Read-only; per-volume flushed progress.
"""
import argparse
import io
import re
import sys
from collections import Counter

sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.pipeline.stages.elements._walker import _IMAGE_RE, _IMAGE_FLOAT_RE
from britannica.pipeline.stages.elements._figure import (
    figure_tail_end, figure_wrapper_end,
)

_HY = re.compile(r"(\w)-\n(\x01PAGE:\d+\x01)(\w)")
_OPEN = re.compile(
    r"\{\{\s*(?:center|block\s*center)\s*\||"
    r"\[\[(?:File|Image):|\{\{\s*(?:img float|figure|FI)\b", re.IGNORECASE)


def inp(s, aid):
    segs = (s.query(ArticleSegment).join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
            .filter(ArticleSegment.article_id == aid).order_by(ArticleSegment.sequence_in_article)
            .add_columns(SourcePage.page_number).all())
    parts = [f"\x01PAGE:{pn}\x01{(seg.segment_text or '')}" for seg, pn in segs]
    return _HY.sub(r"\1\2\3", "\n".join(parts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volumes", default="all")
    args = ap.parse_args()
    s = SessionLocal()
    if args.volumes == "all":
        vols = [v for (v,) in s.query(Article.volume).distinct()
                .order_by(Article.volume) if v and v < 29]
    else:
        vols = [int(x) for x in args.volumes.split(",")]

    spans = tails = 0
    blockhist = Counter()
    longest = []   # (taillen, vol, title, tail)
    chained = []   # (nblocks, vol, title, tail)
    print(f"{'vol':>3} {'figs':>5} {'tails':>6}", flush=True)
    for v in vols:
        aids = [a for (a,) in s.query(Article.id)
                .filter(Article.volume == v, Article.article_type == "article",
                        Article.body.like("%{{IMG:%")).all()]
        vt = 0
        for aid in aids:
            txt = inp(s, aid)
            title = s.get(Article, aid).title
            pos = 0
            while True:
                h = _OPEN.search(txt, pos)
                if not h:
                    break
                p = h.start()
                w = figure_wrapper_end(txt, p)
                if w is not None:
                    spans += 1
                    pos = w
                    continue
                m = _IMAGE_RE.match(txt, p) or _IMAGE_FLOAT_RE.match(txt, p)
                if not m:
                    pos = p + 2
                    continue
                spans += 1
                end = figure_tail_end(txt, m.end())
                tail = txt[m.end():end]
                if tail.strip():
                    tails += 1
                    vt += 1
                    nb = tail.count("\n\n")
                    blockhist[nb] += 1
                    longest.append((len(tail), v, title, tail))
                    if nb >= 1:
                        chained.append((nb, v, title, tail))
                pos = end if end > p else p + 1
        print(f"{v:>3} {len(aids):>5} {vt:>6}", flush=True)

    print(f"\nspans={spans}  with-tail={tails}")
    print("tail block-count histogram (0 = single-block caption/legend):")
    for nb in sorted(blockhist):
        print(f"  {nb} extra \\n\\n : {blockhist[nb]}")
    print("\n--- 20 LONGEST tails (over-absorption shows up as length) ---")
    for ln, v, t, tail in sorted(longest, reverse=True)[:20]:
        print(f"  [{ln}] v{v} {t}: {tail[:160]!r}")
    print("\n--- 20 most-CHAINED tails (absorbed across \\n\\n) ---")
    for nb, v, t, tail in sorted(chained, reverse=True)[:20]:
        print(f"  [{nb}bk] v{v} {t}: {tail[:160]!r}")


if __name__ == "__main__":
    main()

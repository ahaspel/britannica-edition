"""Plate experiment — does the GENERIC recursive producer reproduce plate
composition as well as the bespoke `parsers/plate/`?

For each vol-1 plate, render its raw page two ways:
  • OLD: `parse_plate(raw)`        — the bespoke 4-stage plate parser
  • NEW: `render_markers(raw)`     — the generic recursive producer (marker form)
Both emit the SAME marker contract ({{IMG:}}/{{LEGEND:}}/«HTMLTABLE:»/…), so we
compare structurally (marker counts) and on content-words (what each drops/adds),
and dump the divergent ones for the eye.  No DB writes, old path untouched.

Usage: uv run python tools/diagnostics/plate_render_diff.py [VOL]   (default 1)
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools" / "diagnostics"))
import render_proto as R
from britannica.parsers.plate import parse_plate
from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment

STOP = set("the a an of in on at to and or for with by from as is are was were be "
           "this that these those it its fig plate i ii iii iv v vi vii viii ix x".split())


def words(s: str) -> set[str]:
    s = re.sub(r"«[^»]*»|\{\{[^}]*|\}TABLE\}|\}VERSE\}|\}LEGEND\}|<[^>]+>", " ", s)
    return {w for w in re.findall(r"[a-z]+", s.lower()) if w not in STOP and len(w) > 2}


def markers(s: str) -> dict[str, int]:
    return {
        "IMG": len(re.findall(r"\{\{IMG:", s)),
        "LEGEND": len(re.findall(r"\{\{LEGEND:", s)),
        "TABLE": len(re.findall(r"«HTMLTABLE:|\{\{TABLE", s)),
        "OUTLINE": len(re.findall(r"«(?:PLATE_)?OUTLINE", s)),
        "CTR": len(re.findall(r"«CTR»", s)),
    }


def main() -> None:
    vol = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    s = SessionLocal()
    plates = (s.query(Article)
              .filter(Article.article_type == "plate", Article.volume == vol)
              .order_by(Article.page_start).all())
    print(f"=== vol {vol}: {len(plates)} plates — parse_plate (OLD) vs render_markers (NEW) ===\n")
    agg = {"identical_words": 0, "new_loses": 0, "new_gains": 0, "struct_diff": 0, "err": 0}
    diverged = []
    for a in plates:
        segs = (s.query(ArticleSegment).filter_by(article_id=a.id)
                .order_by(ArticleSegment.sequence_in_article).all())
        raw = segs[0].segment_text if segs else ""
        if not raw:
            continue
        try:
            old = parse_plate(raw)
            new = R.render_markers(raw)
        except Exception as e:
            agg["err"] += 1
            print(f"  ERR {a.title}: {type(e).__name__}: {e}")
            continue
        wo, wn = words(old), words(new)
        lost, gained = wo - wn, wn - wo
        mo, mn = markers(old), markers(new)
        struct = {k: (mo[k], mn[k]) for k in mo if mo[k] != mn[k]}
        if not lost and not gained:
            agg["identical_words"] += 1
        if lost:
            agg["new_loses"] += 1
        if gained:
            agg["new_gains"] += 1
        if struct:
            agg["struct_diff"] += 1
        if lost or struct:
            diverged.append((a.title, sorted(lost)[:12], sorted(gained)[:12], struct, old, new))
    s.close()
    print(f"summary: {agg}\n")
    print(f"=== {len(diverged)} plates where NEW loses words or differs structurally ===")
    for title, lost, gained, struct, old, new in diverged[:14]:
        print(f"\n----- {title} -----")
        print(f"  struct(old→new): {struct}")
        if lost:
            print(f"  NEW LOSES: {lost}")
        if gained:
            print(f"  NEW GAINS: {gained}")
        print(f"  OLD[:240]: {old[:240]!r}")
        print(f"  NEW[:240]: {new[:240]!r}")


if __name__ == "__main__":
    main()

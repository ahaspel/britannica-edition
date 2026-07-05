"""One-off: find articles a rebuild would STILL leave with an un-anchored major
section — the residual of stamp_sections' lone-head gate.

`_find_heads` stamps a LONE centered-small-caps heading only when a shoulder
heading FOLLOWS it (`_SHOULDER.search(raw, off)`).  POLAND/NORWAY pass because
shoulders happen to follow their sole heading.  This scan asks: is there an
article whose sole heading has shoulders only BEFORE it (BEFORE-ONLY) — i.e. a
real section the current gate misses, that broadening to `_SHOULDER.search(raw)`
(shoulder anywhere) would catch?  NO-SHOULDER (no shoulder at all) is reported
for context only; broadening does NOT change those (still declined).

Read-only.  Prints a log; writes nothing.
"""
import re
import sys
import time

from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.pipeline.stages.transform_articles import produce_title
import britannica.pipeline.stages.transform_articles.sections as S


def _valid_lone_head(body):
    """Re-derive the gate-valid heads exactly as `_find_heads` collects them,
    returning the list of (offset, name).  Used only when `_find_heads` already
    returned [] — to learn WHY (how many valid heads, shoulder before/after)."""
    valid = []
    for m in S._HEAD_OPEN.finditer(body):
        nl = body.rfind("\n", 0, m.start())
        before = S._PREHEAD.sub("", body[nl + 1:m.start()])
        if before and before[-1] not in "}>":
            continue
        end = S._balanced_end(body, m.start())
        if end < 0:
            end = body.find("\n", m.start())
            end = end if end >= 0 else len(body)
        full = body[m.start():end]
        kind = m.group(1).lower()
        if kind in ("c", "center") and "{{sc" not in full.lower():
            continue
        if "[[File:" in full or "{{IMG" in full:
            continue
        inner = body[m.end():end]
        inner = inner[:-2] if inner.endswith("}}") else inner.rstrip("}")
        name = S._visible(inner).split("\n")[0].strip()
        name = re.sub(r"[{}«»]", "", name).replace("|", "/")
        if not name or S._CAPWORD.match(name):
            continue
        if not S._NUMERAL.match(name):
            after = body[end:end + 40].lstrip()
            if after.startswith("{|") or after.lower().startswith("<table"):
                continue
        valid.append((m.start(), name))
    return valid


def classify(body):
    if S._find_heads(body):
        return None  # already stamped by current code
    valid = _valid_lone_head(body)
    if len(valid) != 1:
        return None  # 0 valid, or >=2 (would have stamped) — not this class
    off, name = valid[0]
    if S._SHOULDER.search(body, off):
        return None  # shoulder after — would have stamped
    if S._SHOULDER.search(body[:off]):
        return ("BEFORE-ONLY", name)
    return ("NO-SHOULDER", name)


def main():
    s = SessionLocal()
    arts = s.query(Article).order_by(Article.volume, Article.page_start).all()
    total = len(arts)
    t0 = time.time()
    before_only, no_shoulder = [], []
    for i, a in enumerate(arts):
        segs = (s.query(ArticleSegment)
                .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
                .filter(ArticleSegment.article_id == a.id)
                .order_by(ArticleSegment.sequence_in_article).all())
        joined = "".join(seg.segment_text or "" for seg in segs)
        if not joined:
            continue
        body, _ = produce_title(joined, a.section_name)
        r = classify(body)
        if r is None:
            continue
        cls, name = r
        rec = f"v{a.volume} p{a.page_start} {a.title!r} :: {name!r}"
        if cls == "BEFORE-ONLY":
            before_only.append(rec)
            print(f"[BEFORE-ONLY] {rec}", flush=True)
        else:
            no_shoulder.append(rec)
        if i % 2000 == 0:
            print(f"... {i}/{total}  ({time.time()-t0:.0f}s)  "
                  f"before-only={len(before_only)} no-shoulder={len(no_shoulder)}",
                  flush=True)
    print("\n" + "=" * 60)
    print(f"DONE {total} articles in {time.time()-t0:.0f}s")
    print(f"BEFORE-ONLY (residual the broadened gate WOULD catch): {len(before_only)}")
    for r in before_only:
        print(f"   {r}")
    print(f"\nNO-SHOULDER (unchanged by broadening; likely decorative): {len(no_shoulder)}")
    for r in no_shoulder[:40]:
        print(f"   {r}")
    if len(no_shoulder) > 40:
        print(f"   ... (+{len(no_shoulder)-40} more)")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()

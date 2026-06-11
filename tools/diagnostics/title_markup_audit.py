"""Audit: how many article titles carry markup that clean_title strips?

The title heading raw is NOT preserved post-boundary-detection
(segment_text is the body), so we re-derive each heading from its
SOURCE PAGE: scan «B» spans, run the LIVE extractor
(elements/_title.py:_title_span), and match the flattened result to the
stored plain Article.title.  The matching span is the heading; we
categorize the markup inside it that the plain title flattens away.

Reports match rate (so we know the audit's coverage) and the markup
split (mixed bold/ital, small-caps, links, templates).  Pre-heading
footnotes (ODO) are counted separately from the body (a leading <ref>).
Read-only; per-volume flushed.
"""
import io, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, "src")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from britannica.db.session import SessionLocal
from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.pipeline.stages.elements._title import _title_span, clean_title

s = SessionLocal()
_SC = re.compile(r"\{\{\s*(?:sc|asc|small[\s\-]?caps?)\b", re.IGNORECASE)
_TMPL = re.compile(r"\{\{")
_LEAD_REF = re.compile(r"^\s*<ref", re.IGNORECASE)


def _norm(t: str) -> str:
    return re.sub(r"\s+", " ", t).strip().upper().rstrip(",.;:")


cat = Counter()
samples = defaultdict(list)
matched = unmatched = footnote = 0

vols = [v for (v,) in s.query(Article.volume).distinct().order_by(Article.volume)
        if v and v < 29]
print(f"{'vol':>3} {'arts':>6} {'match':>6} {'fmt':>5}", flush=True)
for v in vols:
    pages = {pn: (wt or "") for pn, wt in
             s.query(SourcePage.page_number, SourcePage.wikitext)
             .filter(SourcePage.volume == v)}
    arts = s.query(Article.id, Article.title, Article.page_start).filter(
        Article.volume == v, Article.article_type == "article").all()
    vmatch = vfmt = 0
    for aid, title, pstart in arts:
        # footnote half (from the body): leading <ref>
        seg = (s.query(ArticleSegment.segment_text)
               .filter(ArticleSegment.article_id == aid)
               .order_by(ArticleSegment.sequence_in_article).first())
        if seg and seg[0] and _LEAD_REF.match(seg[0]):
            footnote += 1
        # formatting half: re-derive heading from the source page
        w = pages.get(pstart, "")
        want = _norm(title)
        title_raw = None
        for m in re.finditer("«B»", w):
            tr, _ = _title_span(w[m.start():])
            if tr and _norm(clean_title(tr)) == want:
                title_raw = tr
                break
        if title_raw is None:
            unmatched += 1
            continue
        matched += 1
        vmatch += 1
        kinds = set()
        if "«I»" in title_raw:
            kinds.add("italic")
        if _SC.search(title_raw):
            kinds.add("small-caps")
        if title_raw.count("«B»") > 1:
            kinds.add("multi-bold")
        if "[[" in title_raw:
            kinds.add("link")
        if _TMPL.search(title_raw) and not _SC.search(title_raw):
            kinds.add("other-template")
        for k in kinds:
            cat[k] += 1
            if len(samples[k]) < 6:
                samples[k].append((title, title_raw[:80]))
        if kinds:
            vfmt += 1
        else:
            cat["plain-bold-only"] += 1
    print(f"{v:>3} {len(arts):>6} {vmatch:>6} {vfmt:>5}", flush=True)

print(f"\n=== matched {matched} headings, unmatched {unmatched} "
      f"({100*matched/max(matched+unmatched,1):.1f}% coverage) ===")
print(f"title-footnotes (body starts with <ref>): {footnote}")
print("\nformatting markup in matched headings:")
for k, n in cat.most_common():
    print(f"  {k:18}{n}")
print("\n--- samples ---")
for k in cat:
    if k == "plain-bold-only":
        continue
    print(f"  [{k}]")
    for title, snip in samples[k]:
        print(f"    {title!r}  <=  {snip!r}")

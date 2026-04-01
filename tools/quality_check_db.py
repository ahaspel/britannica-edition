#!/usr/bin/env python3
"""Database-level quality analysis of articles."""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from britannica.db.models import Article, ArticleSegment, CrossReference, SourcePage
from britannica.db.session import SessionLocal


def main():
    session = SessionLocal()
    try:
        articles = (
            session.query(Article)
            .filter(Article.article_type == "article")
            .order_by(Article.volume, Article.page_start)
            .all()
        )
        print(f"Total articles: {len(articles)}")
        print()

        # ── By body length (word count) ──
        buckets = {
            "0 words (empty)": [],
            "1-5 words": [],
            "6-20 words": [],
            "21-100 words": [],
            "101-500 words": [],
            "501-2000 words": [],
            "2001-10000 words": [],
            "10001+ words": [],
        }
        for a in articles:
            wc = len((a.body or "").split())
            if wc == 0:
                buckets["0 words (empty)"].append(a)
            elif wc <= 5:
                buckets["1-5 words"].append(a)
            elif wc <= 20:
                buckets["6-20 words"].append(a)
            elif wc <= 100:
                buckets["21-100 words"].append(a)
            elif wc <= 500:
                buckets["101-500 words"].append(a)
            elif wc <= 2000:
                buckets["501-2000 words"].append(a)
            elif wc <= 10000:
                buckets["2001-10000 words"].append(a)
            else:
                buckets["10001+ words"].append(a)

        print("=== Article length distribution ===")
        for label, arts in buckets.items():
            print(f"  {label:25s} {len(arts):6d}", end="")
            if len(arts) <= 5 and arts:
                print(f"  [{', '.join(a.title for a in arts)}]", end="")
            print()
        print()

        # ── By title length ──
        title_buckets = {
            "1 char": [],
            "2 chars": [],
            "3-5 chars": [],
            "6-15 chars": [],
            "16-30 chars": [],
            "31-50 chars": [],
            "51+ chars": [],
        }
        for a in articles:
            tlen = len(a.title)
            if tlen == 1:
                title_buckets["1 char"].append(a)
            elif tlen == 2:
                title_buckets["2 chars"].append(a)
            elif tlen <= 5:
                title_buckets["3-5 chars"].append(a)
            elif tlen <= 15:
                title_buckets["6-15 chars"].append(a)
            elif tlen <= 30:
                title_buckets["16-30 chars"].append(a)
            elif tlen <= 50:
                title_buckets["31-50 chars"].append(a)
            else:
                title_buckets["51+ chars"].append(a)

        print("=== Title length distribution ===")
        for label, arts in title_buckets.items():
            print(f"  {label:25s} {len(arts):6d}", end="")
            if len(arts) <= 5 and arts:
                print(f"  [{', '.join(a.title for a in arts)}]", end="")
            print()
        print()

        # ── Titles with punctuation ──
        import re
        punct_categories = {
            "contains period": [],
            "contains parentheses": [],
            "contains colon": [],
            "contains semicolon": [],
            "contains numbers": [],
            "contains lowercase": [],
            "starts lowercase": [],
        }
        for a in articles:
            t = a.title
            if "." in t:
                punct_categories["contains period"].append(a)
            if "(" in t or ")" in t:
                punct_categories["contains parentheses"].append(a)
            if ":" in t:
                punct_categories["contains colon"].append(a)
            if ";" in t:
                punct_categories["contains semicolon"].append(a)
            if re.search(r"\d", t):
                punct_categories["contains numbers"].append(a)
            if re.search(r"[a-z]", t):
                punct_categories["contains lowercase"].append(a)
            if t and t[0].islower():
                punct_categories["starts lowercase"].append(a)

        print("=== Title punctuation/oddities ===")
        for label, arts in punct_categories.items():
            print(f"  {label:25s} {len(arts):6d}", end="")
            if len(arts) <= 5 and arts:
                print(f"  [{', '.join(a.title for a in arts)}]", end="")
            elif arts:
                # Show a few examples
                print(f"  e.g. {', '.join(a.title for a in arts[:3])}", end="")
            print()
        print()

        # ── Articles that are xref-only (mentioned but have minimal body) ──
        print("=== Potential xref-only stubs ===")
        xref_stubs = []
        for a in articles:
            body = a.body or ""
            wc = len(body.split())
            if wc <= 20:
                xref_count = (
                    session.query(CrossReference)
                    .filter(CrossReference.article_id == a.id)
                    .count()
                )
                if xref_count > 0 and wc <= 10:
                    xref_stubs.append((a, wc, xref_count))
        print(f"  Short articles (<=10 words) with xrefs: {len(xref_stubs)}")
        for a, wc, xc in xref_stubs[:10]:
            print(f"    Vol {a.volume:2d} [{a.title}] {wc} words, {xc} xrefs: {(a.body or '')[:60]}")
        print()

        # ── Body starts with lowercase (potential continuation) ──
        lc_start = [a for a in articles if a.body and a.body[0].islower()]
        print(f"=== Body starts lowercase: {len(lc_start)} ===")
        # Subcategorize
        lc_legit = []
        lc_continuation = []
        for a in lc_start:
            if re.match(r"^(a |an |the |or |\()", a.body, re.IGNORECASE):
                lc_legit.append(a)
            else:
                lc_continuation.append(a)
        print(f"  Likely legitimate (article def): {len(lc_legit)}")
        print(f"  Likely continuation: {len(lc_continuation)}")
        for a in lc_continuation[:10]:
            print(f"    Vol {a.volume:2d} p{a.page_start} [{a.title}] {a.body[:60]}")
        print()

        # ── Borderline: named sections without bold that were treated as continuation ──
        print("=== Borderline: named sections folded as continuation ===")
        borderline = []
        pages = (
            session.query(SourcePage)
            .order_by(SourcePage.volume, SourcePage.page_number)
            .all()
        )
        for page in pages:
            text = page.cleaned_text or ""
            for m in re.finditer(r"\u00abSEC:([^\u00bb]+)\u00bb", text):
                sec_id = m.group(1)
                if re.match(r"^s\d+$", sec_id):
                    continue  # anonymous section
                after = text[m.end():m.end() + 200].strip()
                has_bold = after.startswith("\u00abB\u00bb")
                if has_bold:
                    continue  # new article — not borderline
                first_line = after.split("\n")[0][:80] if after else ""
                # Only flag ones that start uppercase (ambiguous)
                if first_line and not first_line[0].islower():
                    borderline.append((
                        page.volume, page.page_number,
                        sec_id, first_line,
                    ))

        print(f"  Total borderline (named, no bold, uppercase start): {len(borderline)}")
        # Subcategorize
        looks_like_heading = []
        looks_like_data = []
        for vol, pg, sec_id, first_line in borderline:
            clean = re.sub(r"\u00ab[^»]*\u00bb", "", first_line)
            if re.match(r"^[A-Z][A-Z\s,.\-]{2,}", clean):
                looks_like_heading.append((vol, pg, sec_id, first_line))
            else:
                looks_like_data.append((vol, pg, sec_id, first_line))

        print(f"  Looks like missed article heading: {len(looks_like_heading)}")
        for vol, pg, sec_id, fl in looks_like_heading[:15]:
            print(f"    Vol {vol:2d} p{pg:4d} [{sec_id}] {fl}")
        if len(looks_like_heading) > 15:
            print(f"    ... and {len(looks_like_heading) - 15} more")

        print(f"  Looks like data/text (probably correct continuation): {len(looks_like_data)}")
        for vol, pg, sec_id, fl in looks_like_data[:10]:
            print(f"    Vol {vol:2d} p{pg:4d} [{sec_id}] {fl}")
        if len(looks_like_data) > 10:
            print(f"    ... and {len(looks_like_data) - 10} more")
        print()

        # ── Alphabetical gaps ──
        print("=== Alphabetical gaps (large jumps between consecutive titles) ===")
        gaps = []
        for vol in sorted(set(a.volume for a in articles)):
            vol_arts = sorted(
                [a for a in articles if a.volume == vol],
                key=lambda a: (a.page_start, a.title),
            )
            for i in range(1, len(vol_arts)):
                prev_t = vol_arts[i - 1].title
                curr_t = vol_arts[i].title
                # Compare first 3 chars — if they jump more than a couple letters, flag it
                prev_prefix = prev_t[:3].upper()
                curr_prefix = curr_t[:3].upper()
                if prev_prefix and curr_prefix and prev_prefix.isalpha() and curr_prefix.isalpha():
                    # Check if first letter changes AND there's a multi-letter gap
                    if prev_prefix[0] != curr_prefix[0]:
                        continue  # letter boundary, normal
                    if len(prev_prefix) >= 2 and len(curr_prefix) >= 2:
                        if abs(ord(curr_prefix[1]) - ord(prev_prefix[1])) > 3:
                            gaps.append((
                                vol, vol_arts[i - 1].page_end,
                                prev_t, curr_t,
                            ))
        print(f"  Large alphabetical jumps: {len(gaps)}")
        for vol, pg, prev_t, curr_t in gaps[:15]:
            print(f"    Vol {vol:2d} p{pg:4d}: [{prev_t}] -> [{curr_t}]")
        if len(gaps) > 15:
            print(f"    ... and {len(gaps) - 15} more")
        print()

        # ── Page coverage ──
        print("=== Uncovered pages (not claimed by any article) ===")
        uncovered_total = 0
        for vol in sorted(set(a.volume for a in articles)):
            vol_pages = (
                session.query(SourcePage)
                .filter(SourcePage.volume == vol)
                .all()
            )
            covered_page_ids = set(
                seg.source_page_id for seg in
                session.query(ArticleSegment.source_page_id)
                .join(Article, ArticleSegment.article_id == Article.id)
                .filter(Article.volume == vol)
                .all()
            )
            all_page_ids = {p.id for p in vol_pages}
            uncovered = all_page_ids - covered_page_ids
            if uncovered:
                uncovered_pages = sorted(
                    p.page_number for p in vol_pages if p.id in uncovered
                )
                uncovered_total += len(uncovered)
                if len(uncovered) <= 10:
                    print(f"  Vol {vol:2d}: {len(uncovered)} uncovered pages: {uncovered_pages}")
                else:
                    print(f"  Vol {vol:2d}: {len(uncovered)} uncovered pages: {uncovered_pages[:5]}...{uncovered_pages[-3:]}")
        print(f"  Total uncovered: {uncovered_total}")
        print()

        # ── Embedded bold headings (possible missed split) ──
        print("=== Embedded bold headings in article body ===")
        embedded = []
        bold_open = "\u00abB\u00bb"
        bold_close = "\u00ab/B\u00bb"
        for a in articles:
            body = a.body or ""
            # Skip the very start — that's the article's own heading remnant
            search_body = body[20:] if len(body) > 20 else ""
            for m in re.finditer(
                re.escape(bold_open) + r"([A-Z][A-Z\s,.\-']+)" + re.escape(bold_close),
                search_body,
            ):
                candidate = m.group(1).strip().rstrip(",.")
                # Skip short matches (bold emphasis, not headings)
                if len(candidate) < 3:
                    continue
                # Skip if it's clearly mid-sentence emphasis
                before = search_body[max(0, m.start() - 5):m.start()]
                if before and not before.rstrip().endswith(("\n", ".")):
                    continue
                # This looks like a heading that should be its own article
                embedded.append((a.volume, a.page_start, a.title, candidate))
                break  # one per article is enough

        print(f"  Articles with embedded bold headings: {len(embedded)}")
        for vol, pg, title, heading in embedded[:15]:
            print(f"    Vol {vol:2d} p{pg:4d} [{title}] contains: {heading}")
        if len(embedded) > 15:
            print(f"    ... and {len(embedded) - 15} more")
        print()

        # ── Per-volume summary ──
        print("=== Per-volume article counts ===")
        from collections import Counter
        vol_counts = Counter(a.volume for a in articles)
        for vol in sorted(vol_counts):
            print(f"  Vol {vol:2d}: {vol_counts[vol]:5d} articles")

    finally:
        session.close()


if __name__ == "__main__":
    main()

"""Structural fingerprint audit across every plate article.

For each ``article_type='plate'`` segment, extract a structural
fingerprint of its raw wikitext and group plates by fingerprint.  The
goal: enumerate the actual variation in plate source markup so a
single parser can handle each shape correctly, rather than accreting
case-by-case fixes.

Each plate's fingerprint is a tuple of structural features:

* outer:       outermost element type before any image
                ({|, <table>, {{c|, plain)
* wikitables:  count of {|…|} wiki tables
* htmltables:  count of <table…</table> HTML tables
* illus:       count of <table summary="Illustration"> blocks
* images:      count of [[Image:…]] / [[File:…]] references
* colspan:     count of explicit colspan>1 cells
* shared_cap:  legend-shaped row (colspan + descriptive prose)?
* nested:      max nesting depth of {| inside another {|
* top_legend:  has a centered ``{{c|…}}`` block before the first image?
* multipage:   article has >1 segment

Output: a frequency table sorted by count, plus a list of ALL
plates and their fingerprints (for spot-checking).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict

from britannica.db.models import Article, ArticleSegment
from britannica.db.session import SessionLocal


def fingerprint(raw: str) -> dict:
    """Compute a structural fingerprint dict for one plate page."""
    text = re.sub(r"<noinclude>.*?</noinclude>", "", raw,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    images = re.findall(r"\[\[(?:File|Image):", text, re.IGNORECASE)
    wikitables = re.findall(r"^\{\|", text, re.MULTILINE)
    htmltables = re.findall(r"<table\b", text, re.IGNORECASE)
    illus = re.findall(r'<table[^>]*summary="Illustration"', text, re.IGNORECASE)
    colspans = re.findall(r'colspan\s*=\s*"?[2-9]\d*', text, re.IGNORECASE)

    # Outermost element classifier: walk forward until the first
    # structural opener.
    classifiers = [
        (r'^\s*\{\|', "wikitable"),
        (r'^\s*<table\b[^>]*summary="Illustration"', "illustration_html"),
        (r'^\s*<table\b', "html_table"),
        (r'^\s*\{\{\s*c\s*\|', "c_centered"),
        (r'^\s*\{\{\s*center\b', "center_template"),
        (r'^\s*\[\[(?:File|Image):', "bare_image"),
    ]
    outer = "other"
    for pat, name in classifiers:
        if re.search(pat, text, re.IGNORECASE | re.MULTILINE):
            outer = name
            break

    # Nesting depth: walk through the text tracking {| / |} balance and
    # record max depth.
    depth = 0
    max_depth = 0
    i = 0
    while i < len(text):
        if text[i:i + 2] == "{|":
            depth += 1
            max_depth = max(max_depth, depth)
            i += 2
        elif text[i:i + 2] == "|}":
            depth = max(0, depth - 1)
            i += 2
        else:
            i += 1

    # Top-legend probe: any ``{{c|…}}`` containing a {{larger}} or
    # all-caps title BEFORE the first wiki/html table?
    first_table_pos = len(text)
    for pat in (r"^\{\|", r"<table\b"):
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            first_table_pos = min(first_table_pos, m.start())
    pre_table = text[:first_table_pos]
    top_legend = bool(
        re.search(r"\{\{\s*c\s*\|.*[A-Z]{4,}", pre_table, re.DOTALL)
        or re.search(r"\{\{\s*center\b.*[A-Z]{4,}", pre_table, re.DOTALL)
    )

    return {
        "outer": outer,
        "wikitables": len(wikitables),
        "htmltables": len(htmltables),
        "illus": len(illus),
        "images": len(images),
        "colspan": len(colspans),
        "max_depth": max_depth,
        "top_legend": top_legend,
    }


def signature(fp: dict, multipage: bool) -> tuple:
    """Reduce a fingerprint to a hashable signature for clustering.

    Use only features that drive parser-handler choice — outer element
    type, presence/absence of structural features, max nesting depth.
    Image count, caption count, colspan count don't change the
    *handler*, only its inputs, so they're elided.
    """
    return (
        fp["outer"],
        f"depth={fp['max_depth']}",
        "wt=multi" if fp["wikitables"] >= 2 else (
            "wt=1" if fp["wikitables"] == 1 else "wt=0"
        ),
        "ht=multi" if fp["htmltables"] >= 2 else (
            "ht=1" if fp["htmltables"] == 1 else "ht=0"
        ),
        "has_illus" if fp["illus"] else "",
        "has_colspan" if fp["colspan"] else "",
        "toplegend" if fp["top_legend"] else "",
        "multipage" if multipage else "",
        "no_image" if fp["images"] == 0 else "",
    )


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    s = SessionLocal()
    plates = s.query(Article).filter(Article.article_type == "plate").all()

    sig_counts: Counter = Counter()
    sig_examples: dict = defaultdict(list)
    rows: list = []

    for art in plates:
        segs = (
            s.query(ArticleSegment)
            .filter(ArticleSegment.article_id == art.id)
            .order_by(ArticleSegment.sequence_in_article)
            .all()
        )
        if not segs:
            continue
        # Fingerprint the FIRST segment only — multi-page plates have
        # the structural variety in their first page.
        raw = segs[0].segment_text or ""
        fp = fingerprint(raw)
        sig = signature(fp, multipage=len(segs) > 1)
        sig_counts[sig] += 1
        if len(sig_examples[sig]) < 4:
            sig_examples[sig].append((art.title, art.volume))
        rows.append((art.title, art.volume, fp, sig, len(segs)))

    s.close()

    print(f"Total plates: {len(rows)}")
    print(f"Distinct signatures: {len(sig_counts)}")
    print()
    print("=== Top signatures by frequency ===")
    print(f"{'count':>5}  signature  examples")
    print("-" * 110)
    for sig, n in sig_counts.most_common():
        sig_str = " ".join(s for s in sig if s)
        ex = ", ".join(f"{t} (v{v:02d})" for t, v in sig_examples[sig][:3])
        print(f"{n:>5}  {sig_str}")
        print(f"        ex: {ex}")
        print()


if __name__ == "__main__":
    main()

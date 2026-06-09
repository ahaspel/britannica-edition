"""Corpus-wide audit: are all block markers paragraph-anchored?

A block marker (LEGEND / VERSE / OUTLINE / PRE / CHEM) is rendered by an
``^…$``-anchored regex in the viewer.  If the marker's containing paragraph
doesn't match that regex — because surrounding prose sits in the same
paragraph — the marker text leaks into the rendered HTML.

This script re-transforms every article with the current producer code,
scans the body for each block marker, and flags any whose paragraph is
not exactly ``^<marker>$``.

The 4 known nested-in-TABLE survivors (HYDRAULICS / LAMENTATIONS / PARIS
verses; CRUSTACEA outline) are reported but architecturally are NOT text
leaks — the inner marker is inside a TABLE cell, whose own renderer
handles cell content.  An audit run that turns up new survivors outside
that pattern is a regression flag.

Run from the repo root:
    uv run python tools/diagnostics/audit_block_marker_anchoring.py

Sample only first N articles (faster smoke check):
    uv run python tools/diagnostics/audit_block_marker_anchoring.py --limit 2000
"""
from __future__ import annotations

import argparse
import re
import sys
import time

from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal
from britannica.pipeline.stages.elements import ElementContext, process_elements


# Block markers whose viewer renderer matches ``^…$`` per paragraph.
PATTERNS: dict[str, str] = {
    "LEGEND":  r"\{\{LEGEND:[\s\S]*?\}LEGEND\}",
    "VERSE":   r"\{\{VERSE(?:\[style:[^\]]*\])?:[\s\S]*?\}VERSE\}",
    "OUTLINE": r"«OUTLINE:[\s\S]*?«/OUTLINE»",
    "CHEM":    r"«CHEM:[\s\S]*?«/CHEM»",
}

# Articles where the inner block marker sits inside a `{{TABLE:` cell —
# the inner is paragraph-unanchored as a STRUCTURAL fact, not a text leak.
# Failures in this set are not new regressions.
KNOWN_NESTED_IN_TABLE: set[str] = {
    "HYDRAULICS", "LAMENTATIONS", "PARIS", "CRUSTACEA",
}


def _retransform(session, article: Article) -> str | None:
    segs = (session.query(ArticleSegment, SourcePage.page_number)
            .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
            .filter(ArticleSegment.article_id == article.id)
            .order_by(ArticleSegment.sequence_in_article).all())
    if not segs:
        return None
    raw = "".join(seg.segment_text or "" for seg, pn in segs)
    try:
        return process_elements(raw, ElementContext(volume=article.volume, page_number=segs[0][1]))
    except Exception as e:
        sys.stdout.buffer.write(
            f"  EXCEPTION {article.title}: {e}\n".encode("utf-8"))
        return None


def _apply_viewer_protection(body: str) -> str:
    """Mirror the viewer's paragraph-protection step.  Internal ``\\n\\n``
    in block markers collapses to ``\\n`` before paragraph split so the
    marker doesn't fragment.  See viewer.html's `_BLOCK_MARKER_RES`.
    """
    protections = [
        r"«HTMLTABLE:[\s\S]*?«/HTMLTABLE»",
        r"\{\{TABLEH?(?:\[style:[^\]]*\])?:[\s\S]*?\}TABLE\}",
        r"\{\{VERSE(?:\[style:[^\]]*\])?:[\s\S]*?\}VERSE\}",
        r"\{\{LEGEND:[\s\S]*?\}LEGEND\}",
        r"«OUTLINE:[\s\S]*?«/OUTLINE»",
        r"«PLATE_OUTLINE:[\s\S]*?«/PLATE_OUTLINE»",
        r"«CHEM:[\s\S]*?«/CHEM»",
    ]
    for pat in protections:
        body = re.sub(pat, lambda m: re.sub(r"\n\n+", "\n", m.group(0)), body)
    return body


def _paragraph_of(body: str, start: int, end: int) -> str:
    ps = body.rfind("\n\n", 0, start) + 2
    pe = body.find("\n\n", end)
    if pe < 0:
        pe = len(body)
    return body[ps:pe]


# Block-marker pattern used by the viewer's split-and-recurse.  When a
# paragraph contains one of these AND surrounding content, the renderer
# splits at marker boundaries and recurses on each piece, so the marker
# ends up as its own paragraph for the anchored renderer.  Mirror that
# logic here before checking anchoring.
_BLOCK_MARKER_SCAN_RE = re.compile(
    r"\{\{TABLEH?(?:\[style:[^\]]*\])?:[\s\S]*?\}TABLE\}"
    r"|\{\{VERSE(?:\[style:[^\]]*\])?:[\s\S]*?\}VERSE\}"
    r"|\{\{LEGEND:[\s\S]*?\}LEGEND\}"
    r"|\{\{IMG:[^}]*\}\}"
    r"|«OUTLINE:[\s\S]*?«/OUTLINE»"
    r"|«PLATE_OUTLINE:[\s\S]*?«/PLATE_OUTLINE»"
    r"|«HTMLTABLE:[\s\S]*?«/HTMLTABLE»"
    r"|«CHEM:[\s\S]*?«/CHEM»"
)


def _viewer_split(body: str) -> list[str]:
    """Simulate the viewer's paragraph-split + split-at-block-marker.
    Returns the list of effective paragraphs the anchored renderer
    sees."""
    out: list[str] = []
    for para in body.split("\n\n"):
        if not para.strip():
            continue
        # Find block markers; if any AND content around them, split.
        matches = list(_BLOCK_MARKER_SCAN_RE.finditer(para))
        if matches and not (len(matches) == 1 and matches[0].group(0) == para.strip()):
            cursor = 0
            for m in matches:
                if m.start() > cursor:
                    before = para[cursor:m.start()]
                    if before.strip():
                        out.append(before)
                out.append(m.group(0))
                cursor = m.end()
            if cursor < len(para):
                after = para[cursor:]
                if after.strip():
                    out.append(after)
        else:
            out.append(para)
    return out


def audit(limit: int | None = None) -> dict[str, list[str]]:
    """Return per-marker list of article titles with unanchored markers."""
    session = SessionLocal()
    try:
        q = (session.query(Article)
             .filter(Article.article_type != "plate")
             .order_by(Article.id))
        if limit:
            q = q.limit(limit)
        arts = q.all()
        sys.stdout.buffer.write(
            f"Auditing {len(arts)} articles...\n".encode("utf-8"))

        unanchored: dict[str, list[str]] = {n: [] for n in PATTERNS}
        compiled = {n: (re.compile(p), re.compile(r"^\s*" + p + r"\s*$"))
                    for n, p in PATTERNS.items()}
        t0 = time.time()
        for i, art in enumerate(arts):
            if i % 2000 == 0:
                sys.stdout.buffer.write(
                    f"  ...{i}/{len(arts)} ({time.time() - t0:.0f}s)\n"
                    .encode("utf-8"))
            body = _retransform(session, art)
            if body is None:
                continue
            body = _apply_viewer_protection(body)
            # Simulate viewer split-and-recurse to get effective paragraphs.
            effective_paras = _viewer_split(body)
            paras_text = "\n\n".join(effective_paras)
            for nm, (pat, anchored) in compiled.items():
                for m in pat.finditer(paras_text):
                    para = _paragraph_of(paras_text, m.start(), m.end())
                    if not anchored.match(para):
                        unanchored[nm].append(art.title)
                        break
        sys.stdout.buffer.write(
            f"\nDone ({time.time() - t0:.0f}s).\n".encode("utf-8"))
        return unanchored
    finally:
        session.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None,
                    help="Sample only first N articles (default: full corpus)")
    args = ap.parse_args()

    unanchored = audit(limit=args.limit)

    new_regressions: list[tuple[str, str]] = []
    sys.stdout.buffer.write(
        f"\n{'Marker':12s} {'#Articles':>10s}\n".encode("utf-8"))
    for nm in PATTERNS:
        titles = unanchored[nm]
        sys.stdout.buffer.write(
            f"{nm:12s} {len(titles):>10d}\n".encode("utf-8"))
        for t in titles:
            if t not in KNOWN_NESTED_IN_TABLE:
                new_regressions.append((nm, t))

    if new_regressions:
        sys.stdout.buffer.write(b"\nNew regressions (outside known nested-in-TABLE set):\n")
        for nm, t in new_regressions:
            sys.stdout.buffer.write(f"  {nm}: {t}\n".encode("utf-8"))
        return 1

    sys.stdout.buffer.write(
        b"\nNo new regressions. All survivors are known nested-in-TABLE cases.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

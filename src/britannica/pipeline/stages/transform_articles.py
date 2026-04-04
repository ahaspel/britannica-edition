"""Transform raw wikitext article bodies into internal marker format.

This stage runs after boundary detection.  Each article's body contains
raw Wikisource wikitext at this point.  We convert it to the internal
marker format (``«B»``, ``«FN:``, ``{{IMG:``, etc.) by running the same
26 fetch stages and clean_pages transformations — but per-article instead
of per-page, and skipping stage 3 (section-tag conversion) since
boundaries have already been determined.

Articles are processed one at a time and committed individually so that
only one article body is in memory at any point.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal

# --- Import clean_pages helpers (always available via src/) ----------------
from britannica.cleaners.headers_footers import strip_headers
from britannica.cleaners.hyphenation import fix_hyphenation
from britannica.cleaners.reflow import reflow_paragraphs
from britannica.cleaners.unicode import normalize_unicode
from britannica.cleaners.whitespace import normalize_whitespace
from britannica.pipeline.stages.clean_pages import (
    _STRAY_CONTROL,
    _clean_plate_layout,
    _convert_img_float,
    _clean_leaked_table_markup,
    _fix_unclosed_footnotes,
    _fix_unclosed_tables,
)

# Fetch stages are loaded lazily — tools/fetch/ is not on sys.path at import
# time in all contexts (e.g. pytest collection).
_FETCH_STAGES = None


def _get_fetch_stages():
    global _FETCH_STAGES
    if _FETCH_STAGES is None:
        # Walk up from src/britannica/pipeline/stages/ to project root
        project_root = Path(__file__).resolve().parents[4]
        tools_fetch = str(project_root / "tools" / "fetch")
        if tools_fetch not in sys.path:
            sys.path.insert(0, tools_fetch)
        from fetch_wikisource_pages import STAGES
        _FETCH_STAGES = STAGES
    return _FETCH_STAGES


def _run_fetch_stages(text: str) -> str:
    """Run the 26 fetch conversion stages, skipping stage 3 (section tags).

    Stage 3 converts ``<section begin=...>`` to ``«SEC:...»`` markers.
    We skip it because boundaries are already locked in — the section tags
    have served their purpose and should simply be stripped.
    """
    stages = _get_fetch_stages()
    for i, stage_fn in enumerate(stages):
        if i == 2:  # stage 3 is index 2 (0-based)
            continue
        text = stage_fn(text)
    return text


def _run_clean_pages(text: str) -> str:
    """Run the clean_pages transformations on marker-format text."""
    text = normalize_unicode(text)
    text, _ = strip_headers(text)
    text, _ = fix_hyphenation(text)
    text = reflow_paragraphs(text)
    text = normalize_whitespace(text)
    text = _STRAY_CONTROL.sub("", text)
    text = text.replace("''", "")
    text = _clean_plate_layout(text)
    text = _convert_img_float(text)
    text = _clean_leaked_table_markup(text)
    text = _fix_unclosed_footnotes(text)
    text = _fix_unclosed_tables(text)
    return text


def _wrap_orphaned_table_rows(text: str) -> str:
    """Wrap orphaned wiki table rows (|- and | lines) that lack a {| opener.

    Multi-page wiki tables have {| in <noinclude> on continuation pages.
    After noinclude stripping, the rows are left bare.  Wrap them in
    {|...|} so the table converter can process them.
    """
    # Quick check: any |- rows present?
    if "\n|-" not in text and not text.startswith("|-"):
        return text
    # Already has a table opener — nothing to fix
    if "{|" in text:
        return text

    # Find the first |- and wrap everything from there to the last |}-or-end
    lines = text.split("\n")
    first_row = None
    last_row = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("|-") or (stripped.startswith("|") and "|" in stripped[1:]):
            if first_row is None:
                first_row = i
            last_row = i

    if first_row is None:
        return text

    # Wrap the table rows
    before = "\n".join(lines[:first_row])
    table = "\n".join(lines[first_row:last_row + 1])
    after = "\n".join(lines[last_row + 1:])
    parts = []
    if before.strip():
        parts.append(before)
    parts.append("{|\n" + table + "\n|}")
    if after.strip():
        parts.append(after)
    return "\n".join(parts)


def _transform_text(raw_wikitext: str) -> str:
    """Convert raw wikitext to the final internal marker format."""
    # Strip any remaining section tags (begin and end) — boundaries are done
    text = re.sub(r'<section\s+(?:begin|end)="[^"]*"\s*/?>', "", raw_wikitext, flags=re.IGNORECASE)
    text = _wrap_orphaned_table_rows(text)
    text = _run_fetch_stages(text)
    text = _run_clean_pages(text)
    return text


def transform_articles(volume: int) -> int:
    """Transform raw wikitext to internal marker format for all articles in a volume.

    Transforms each segment (page-sized) individually, then joins them
    into article.body with \\x01PAGE:N\\x01 markers at page boundaries.
    The markers are injected after transformation so they survive the
    control-character stripping in clean_pages.

    Processes one article at a time with per-article commits.
    """
    session = SessionLocal()
    try:
        article_ids = [
            aid for (aid,) in session.query(Article.id)
            .filter(Article.volume == volume)
            .all()
        ]

        for aid in article_ids:
            article = session.query(Article).get(aid)
            segments = (
                session.query(ArticleSegment)
                .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
                .filter(ArticleSegment.article_id == aid)
                .order_by(ArticleSegment.sequence_in_article)
                .add_columns(SourcePage.page_number)
                .all()
            )

            parts: list[str] = []
            for seg, page_number in segments:
                text = _transform_text(seg.segment_text) if seg.segment_text else ""
                text = text.strip()
                if not text:
                    continue
                marker = f"\x01PAGE:{page_number}\x01"
                if parts:
                    joiner = "\n\n" if re.match(r"\u00abIMG:", text) else " "
                    parts.append(joiner)
                else:
                    # First segment — marker goes at the very start
                    text = marker + text
                    parts.append(text)
                    continue
                parts.append(marker + text)

            article.body = "".join(parts).strip()
            session.commit()
            session.expire_all()

        return len(article_ids)
    finally:
        session.close()

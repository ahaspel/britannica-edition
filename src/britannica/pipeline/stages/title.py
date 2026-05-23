"""Title producer.

Within an article — a consecutive byte string emitted by the corpus
super-walker (``detect_boundaries``) — the title is the leading bold heading.
This module is the single owner of *producing* the title's product from that
heading byte string:

  * the clean **plain title** (`Article.title`) — flattened to plain text so
    xref / contributor / search match on string equality;
  * the **comma-consumed body** — the text after the title with the leading
    title-comma (and stray space/period) eaten, so the body doesn't open with
    orphaned punctuation.

`detect_boundaries` recognizes and classifies the heading (to find/merge
articles); it delegates *production* here. (Display formatting — a future
`title_html` mixing bold/ital — also belongs in this producer when it lands.)
"""
from __future__ import annotations

import re


def clean_title(title_raw: str) -> str:
    """Flatten title-internal markup to plain text.

    Removes:
      - `«B»/«I»/«SC»` formatting markers (the DB-level title is plain so
        xref/contributor/search match cleanly on string equality).
      - `«FN:…«/FN»` footnote markers and raw `<ref…>…</ref>`.
      - Wikilink shells: `[[Author:X|DISPLAY]]` / `[[X|Y]]` / `[[X]]`
        collapse to display text.
      - `{{sc|X}}` / `{{asc|X}}` / `{{smallcaps|X}}` small-caps templates —
        unwrap to inner content.
      - Any other `{{name|…}}` template (mono, fs, …) — flatten to inner
        content.  `{{uc|X}}` uppercases its content.  Iterated to a fixed
        point so nested templates unwrap fully.
    """
    t = title_raw
    # Strip footnote markers (not appropriate in titles)
    t = re.sub(r"«FN(?:\[[^\]]+\])?:.*?«/FN»", "", t, flags=re.DOTALL)
    # Strip raw <ref>…</ref>
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.DOTALL)
    t = re.sub(r"<ref[^/]*/\s*>", "", t)
    # Unwrap wikilinks
    t = re.sub(r"\[\[(?:Author:)?[^\]|]*\|([^\]]+)\]\]", r"\1", t)
    t = re.sub(r"\[\[([^\]|]+)\]\]", r"\1", t)
    # Small-caps variants — unwrap to plain content.
    t = re.sub(
        r"\{\{(?:sc|asc|small[\s\-]?caps?)\|([^{}|]*)\}\}",
        r"\1", t, flags=re.IGNORECASE,
    )
    # Iteratively unwrap remaining templates.
    for _ in range(8):
        before = t
        t = re.sub(r"\{\{uc\|([^{}|]*)\}\}",
                   lambda m: m.group(1).upper(), t, flags=re.IGNORECASE)
        t = re.sub(r"\{\{[^{}|]+\|[^{}]*\|([^{}|]*)\}\}", r"\1", t)
        t = re.sub(r"\{\{[^{}|]+\|([^{}|]*)\}\}", r"\1", t)
        t = re.sub(r"\{\{[^{}|]+\}\}", "", t)
        if t == before:
            break
    # Strip all formatting markers — title is plain text.
    t = re.sub(r"«/?(?:B|I|SC)»", "", t)
    t = re.sub(r"\s+", " ", t).strip().rstrip(",.;:")
    return t


def produce_title(title_raw: str, body_after: str) -> tuple[str, str]:
    """Produce ``(plain_title, comma_consumed_body)`` from the recognized
    bold-heading byte string and the text that immediately follows it.

    The single home for title production: flattening to the plain title and
    consuming the title-comma both happen here, once."""
    title = re.sub(r"\s+,", ",", clean_title(title_raw)).strip()
    body = body_after.lstrip(" \t,.")
    return title, body

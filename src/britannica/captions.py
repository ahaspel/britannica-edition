"""Canonical caption / legend text handling.

The image/caption problem in this corpus is fundamentally a *boundary*
problem — figuring out where a caption / legend / attribution starts and
ends in loosely-laid-out wikitext.  Once the boundary is right, cleaning
the text is comparatively easy.  This module is the cleanup half
(``clean_caption``), shared by:

* the plate parser (``britannica.parsers.plate``),
* the in-article figure walker
  (``britannica.pipeline.stages.transform_articles.legend_promote``),
* the image-element handlers (``…stages.elements._image``), and
* the export-time IMG patcher (``…export.article_json``).

Subsequent work will move the caption-*shape* recognition (the
``Fig. N.—…`` prefix, the photo-credit / figure-source predicate) here
too, so the plate parser and the figure walker share one notion of
"this text is a caption".
"""

from __future__ import annotations

import re


# ── caption-text cleanup ──────────────────────────────────────────────

# Style-only templates: their args are CSS tokens, not renderable text —
# drop the whole template including arguments.
_STYLE_ONLY_TEMPLATE_RE = re.compile(
    r"\{\{\s*(?:ts|tspy|dhr|gap|nop|clear|em|float\s+left|float\s+right)"
    r"(?:\s*\|[^{}]*)?\s*\}\}",
    re.IGNORECASE,
)
# Formatting templates whose argument *is* the text to keep.
_FMT_TEMPLATE_RE = re.compile(
    r"\{\{\s*(?:sc|small-caps|smaller|small|c|center|left|right|big|bold|"
    r"italic|nowrap|fs|lh|csc|x-larger|x-smaller|larger|block\s+center|"
    r"EB1911\s+Fine\s+Print|EB1911\s+article\s+link|uc|lc)\s*\|([^{}]*)\}\}",
    re.IGNORECASE,
)
# An *unclosed* `{{name|` opener (malformed source / a caption truncated
# mid-template by an upstream walker — AMICE's `({{left|Redrawn from
# Braun…)` has `{{left|` with no matching `}}`).  Strip just the opener,
# keep the content that follows.
_UNCLOSED_TMPL_OPEN_RE = re.compile(
    r"\{\{\s*(?:sc|small-caps|smaller|small|c|center|left|right|big|bold|"
    r"italic|nowrap|fs|lh|csc|x-larger|x-smaller|larger|block\s+center|"
    r"EB1911\s+Fine\s+Print|EB1911\s+article\s+link|uc|lc|ts|gap)\s*\|",
    re.IGNORECASE,
)
# A wiki cell-attribute string (`align="center"`, `style=text-align:right`,
# `colspan=2`).  The `=` is load-bearing — it stops the keyword from
# matching prose words ("align the figures", "Art Nouveau style").
_CELL_ATTR_RE = re.compile(
    r'\b(?:colspan|rowspan|style|align|valign|width|height|class|id|scope|'
    r'bgcolor|cellpadding|cellspacing|border)\s*=\s*'
    r'(?:"[^"]*"|\'[^\']*\'|[^\s|]+)',
    re.IGNORECASE,
)
_CELL_ATTR_PREFIX_RE = re.compile(
    r'^(?:(?:colspan|rowspan|style|align|valign|width|height|class|id|scope|'
    r'bgcolor|cellpadding|cellspacing|border)\s*=\s*'
    r'(?:"[^"]*"|\'[^\']*\'|[^\s|]+)\s*)+\|\s*'
)
_HTML_ENTITY_RE = re.compile(r"&#?\w+;")


def clean_caption(text: str) -> str:
    """Produce clean, plain caption / legend text from a fragment that
    may carry leaked markup of any kind.

    Handles multi-level template nesting, *unclosed* formatting-template
    openers, style-only templates, wiki cell-attribute strings,
    wiki-table markers, internal `«…»` markers, and any stray ``|`` /
    ``{`` / ``}`` (which would otherwise break the ``{{IMG:fn|cap}}`` /
    ``{{LEGEND:cap}LEGEND}`` marker syntax).  Idempotent — safe to run
    on already-clean text.  Does NOT strip trailing punctuation: a
    caption legitimately ends "Fig. 1." / "…Machine.", and stripping
    that churns ~650 captions for nothing."""
    if not text:
        return text
    # HTML entities first (some carry text-relevant punctuation).
    text = text.replace("&mdash;", "—").replace("&ndash;", "–")
    text = re.sub(r"&nbsp;|&emsp;|&ensp;|&thinsp;", " ", text)
    text = re.sub(r"&shy;|&zwj;|&zwnj;", "", text)
    text = text.replace("&amp;", "&").replace("&#39;", "'")
    text = _HTML_ENTITY_RE.sub(" ", text)
    # Existing internal markers (post-transform captions carry these).
    text = re.sub(r"«LN:[^|]*\|([^«]*)«/LN»", r"\1", text)
    text = re.sub(r"«B»(.*?)«/B»", r"\1", text)
    text = re.sub(r"«I»(.*?)«/I»", r"\1", text)
    text = re.sub(r"«SC»(.*?)«/SC»", r"\1", text)
    # A footnote in caption position is almost always a <ref> the
    # transcriber put in the caption slot ([[Image:tbl.png|<ref>Dimensions
    # in English feet.</ref>|800px]] — AGRIGENTUM), or a figure-
    # attribution ("…figures are from X, by permission…").  Either way
    # the *content* is the intended caption text — unwrap «FN…:…«/FN» to
    # its content (don't drop it), and unwrap a dangling «FN…: opener
    # too (its closer may already have been eaten by the «/?[A-Z]+» pass
    # below, so handle the marker with its content, not just the closer).
    text = re.sub(r"«FN(?:\[[^\]]*\])?:([\s\S]*?)«/FN»", r" \1 ", text)
    text = re.sub(r"«FN(?:\[[^\]]*\])?:([\s\S]*)$", r" \1", text)
    text = re.sub(r"«/?[A-Z]+»", "", text)
    # Style-only templates → drop whole; formatting templates → unwrap to
    # their argument; iterate until stable so nesting unwinds.
    for _ in range(8):
        before = text
        text = _STYLE_ONLY_TEMPLATE_RE.sub("", text)
        text = _FMT_TEMPLATE_RE.sub(r"\1", text)
        # Generic: multi-arg → last arg; two-arg → last arg.
        text = re.sub(r"\{\{[^{}|]+\|[^{}]*\|([^{}|]*)\}\}", r"\1", text)
        text = re.sub(r"\{\{[^{}|]+\|([^{}]*)\}\}", r"\1", text)
        if text == before:
            break
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)        # remaining bare templates
    text = _UNCLOSED_TMPL_OPEN_RE.sub("", text)       # unclosed `{{left|` etc.
    text = re.sub(r"'''|''", "", text)                # wiki bold/italic
    text = re.sub(r"\{\|[^\n]*", "", text)            # wiki-table open + attrs
    text = re.sub(r"\|\}", "", text)                  # wiki-table close
    text = re.sub(r"(?m)^\|-.*$", "", text)           # wiki-table row separator
    text = re.sub(r"-<br\s*/?>", "", text, flags=re.IGNORECASE)   # soft-hyphen line break
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)   # <br> → space
    text = re.sub(r"<[^>]+>", "", text)               # remaining HTML tags
    text = _CELL_ATTR_PREFIX_RE.sub("", text)         # `|attrs|content` prefix
    text = _CELL_ATTR_RE.sub("", text)                # mid-text `attr=value`
    text = re.sub(r"[|{}]", " ", text)                # any stray pipe/brace → space
    text = re.sub(r"\s+", " ", text).strip()
    # Strip a leftover leading row-separator dash (`- style="…"` → `-`
    # once the cell-attr string is removed) — but NOT trailing
    # punctuation (see docstring).
    return text.lstrip("-– ").strip()

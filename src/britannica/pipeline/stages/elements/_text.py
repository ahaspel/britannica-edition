"""Text utilities used across element processors.

These functions take a string and return a string. No registry, no
context, no DB access — they are safe to use from any handler.
"""

from __future__ import annotations

import re


_SUB_TRANS = str.maketrans({
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋", "=": "₌", "(": "₍", ")": "₎",
    "a": "ₐ", "e": "ₑ", "h": "ₕ", "i": "ᵢ", "j": "ⱼ",
    "k": "ₖ", "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ",
    "p": "ₚ", "r": "ᵣ", "s": "ₛ", "t": "ₜ", "u": "ᵤ",
    "v": "ᵥ", "x": "ₓ",
    # Math-italic letters (used in EB1911 chemical formulas like
    # C<sub>𝑛</sub>H<sub>2𝑛</sub>O<sub>2</sub>) → matching subscript
    "𝑎": "ₐ", "𝑒": "ₑ", "𝒽": "ₕ", "𝑖": "ᵢ", "𝑗": "ⱼ",
    "𝑘": "ₖ", "𝑙": "ₗ", "𝑚": "ₘ", "𝑛": "ₙ", "𝑜": "ₒ",
    "𝑝": "ₚ", "𝑟": "ᵣ", "𝑠": "ₛ", "𝑡": "ₜ", "𝑢": "ᵤ",
    "𝑣": "ᵥ", "𝑥": "ₓ",
})

_SUP_TRANS = str.maketrans({
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
    "i": "ⁱ", "n": "ⁿ",
    "𝑖": "ⁱ", "𝑛": "ⁿ",
})


def _convert_inline_sub_sup(text: str) -> str:
    """Convert <sub>/<sup> tags to Unicode sub/superscripts in cell
    content.  Run BEFORE generic HTML-tag stripping in table handlers
    so chemical formulas like C<sub>2</sub>H<sub>4</sub>O<sub>2</sub>
    survive as C₂H₄O₂ instead of being flattened to "C 2 H 4 O 2".
    Characters with no Unicode subscript form pass through unchanged."""
    text = re.sub(
        r"<sub>([^<]*)</sub>",
        lambda m: m.group(1).translate(_SUB_TRANS),
        text, flags=re.IGNORECASE,
    )
    text = re.sub(
        r"<sup>([^<]*)</sup>",
        lambda m: m.group(1).translate(_SUP_TRANS),
        text, flags=re.IGNORECASE,
    )
    return text


def _strip_br(text: str, replacement: str = " ") -> str:
    """Convert `<br>` to `replacement`, handling soft-hyphen line breaks.

    A `-<br>` pair indicates a word broken across lines by the
    typesetter — we strip both the hyphen and the `<br>` so
    "Circum-<br>ference" renders as "Circumference", not
    "Circum- ference". Plain `<br>` becomes the replacement (space).
    """
    text = re.sub(r"-<br\s*/?>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", replacement, text, flags=re.IGNORECASE)
    return text


def _clean_text(text: str) -> str:
    """Strip all internal markers and wiki templates from text, producing plain text."""
    # Strip link markers: «LN:target|display«/LN» → display
    text = re.sub(r"«LN:[^|]*\|([^«]*)«/LN»", r"\1", text)
    # Strip converted markers (post-fetch-stage)
    text = re.sub(r"«B»(.*?)«/B»", r"\1", text)
    text = re.sub(r"«I»(.*?)«/I»", r"\1", text)
    text = re.sub(r"«SC»(.*?)«/SC»", r"\1", text)
    text = re.sub(r"«/?[A-Z]+»", "", text)
    # Strip raw wiki templates (pre-fetch-stage): {{sc|text}} → text
    text = re.sub(r"\{\{[^{}|]*\|([^{}]*)\}\}", r"\1", text)
    # Strip remaining templates with no args
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode common HTML entities
    text = text.replace("&#8193;", "").replace("&nbsp;", " ")
    text = text.replace("&#39;", "'").replace("&amp;", "&")
    # Strip wiki bold/italic markers
    text = text.replace("'''", "").replace("''", "")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


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

    A robust superset of ``_clean_text``: handles multi-level template
    nesting, *unclosed* formatting-template openers, style-only
    templates, wiki cell-attribute strings, wiki-table markers, and any
    stray ``|`` / ``{`` / ``}`` (which would otherwise break the
    ``{{IMG:fn|cap}}`` / ``{{LEGEND:cap}LEGEND}`` marker syntax).
    Idempotent — safe to run on already-clean text.  Every caption /
    legend emit site routes through this (``elements/_image.py`` runs
    ``text_transform`` + ``_clean_text`` first, which subsumes most of
    it; the legend-promote and export ``_patch_img`` paths build
    captions from raw-ish text and need the full treatment)."""
    if not text:
        return text
    # HTML entities first (some carry the text-relevant punctuation).
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
    text = _strip_br(text, " ")                       # <br> → space (soft-hyphen aware)
    text = re.sub(r"<[^>]+>", "", text)               # remaining HTML tags
    text = _CELL_ATTR_PREFIX_RE.sub("", text)         # `|attrs|content` prefix
    text = _CELL_ATTR_RE.sub("", text)                # mid-text `attr=value`
    text = re.sub(r"[|{}]", " ", text)                # any stray pipe/brace → space
    text = re.sub(r"\s+", " ", text).strip()
    # Strip a leftover leading row-separator dash (`- style="…"` →
    # `-` once the cell-attr string is removed) — but NOT trailing
    # punctuation: a caption legitimately ends "Fig. 1." / "…Machine.",
    # and stripping that would churn ~650 captions for no reason.
    return text.lstrip("-– ").strip()

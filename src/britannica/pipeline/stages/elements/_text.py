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


# ``clean_caption`` lives in ``britannica.captions`` (the shared
# caption-text module).

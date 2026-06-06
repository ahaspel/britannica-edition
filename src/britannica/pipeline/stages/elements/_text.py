"""Text utilities used across element processors.

These functions take a string and return a string. No registry, no
context, no DB access — they are safe to use from any handler.
"""

from __future__ import annotations

import re


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
    # `_clean_text` flattens to PLAIN text (captions, cell text, etc.).
    # Image markers carry `|`-separated layout metadata; the generic
    # `{{name|content}}` rule below would otherwise mangle them into
    # stray text (`{{IMG:fn|align=inline}}` → `align=inline`).  A plain-
    # text context can't render a glyph, so drop image markers entirely.
    text = re.sub(r"\{\{IMG:[^{}]*\}\}", "", text)
    # Strip raw wiki templates (pre-fetch-stage): {{sc|text}} → text
    text = re.sub(r"\{\{[^{}|]*\|([^{}]*)\}\}", r"\1", text)
    # Strip remaining templates with no args
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode common HTML entities
    text = text.replace("&#8193;", "").replace("&nbsp;", " ")
    text = text.replace("&#39;", "'").replace("&amp;", "&")
    # Strip bold/italic markers (clean_pages converts source `'''/''`
    # to «B»/«I» markers upstream)
    text = (text.replace("«B»", "").replace("«/B»", "")
                .replace("«I»", "").replace("«/I»", ""))
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ``clean_caption`` lives in ``britannica.captions`` (the shared
# caption-text module).

"""Shared LLM-context excerpt cleaner for xref-resolution prompts.

Strips page markers, link markers, image markers, structured table/legend
blocks, and collapses whitespace, then truncates to ``max_chars``.
"""

import re

from britannica.markers import IMG_RE, strip_page_markers


def clean_excerpt(text: str, max_chars: int) -> str:
    text = strip_page_markers(text)
    text = re.sub(r"«LN:[^|]*\|([^«]*)«/LN»", r"\1", text)
    text = re.sub(r"«[^»]*»", "", text)
    text = IMG_RE.sub("", text)
    text = re.sub(r"\{\{LEGEND:[\s\S]*?\}LEGEND\}", "", text)
    text = re.sub(r"\{\{TABLE[A-Z]?:[\s\S]*?\}TABLE\}", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]

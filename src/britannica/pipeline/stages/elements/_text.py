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

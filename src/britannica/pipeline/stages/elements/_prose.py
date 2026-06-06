"""The leaf text-transform, lifted out of body_text (deleted).

`_apply_markup` is the leaf `text_transform` the walker hands every producer — IDENTITY.
`_transform_body_text` is the BODY producer for SHAPE_BODY — also IDENTITY: the residual
prose run is NOT pure leaf, it carries inline element markers («SC», «LN», …) and
placeholders that belong to the recursion.  Any across-the-board pass over it (whitespace
collapse, `<br>`→«BR», `:`-sigil strip) would reach INTO content the body doesn't own — a
mini-sweeper.  The body assembles by concatenation and transforms nothing.

(`<br>` as its own walker element, and any genuine article-assembly glue, are step 3 —
they don't get smuggled back in as a blanket body pass.)
"""

from __future__ import annotations


def _apply_markup(text: str) -> str:
    """Leaf text-transform — IDENTITY.  The walker's recognized elements do the markup
    work; whatever it doesn't recognize leaks, and the leak audit is the to-do list."""
    return text


def _transform_body_text(text: str) -> str:
    """BODY producer (SHAPE_BODY) — IDENTITY.  No across-the-board pass: the run carries
    inner element markers the body does not own."""
    return text

"""Plate-page parser: structure-agnostic, four-stage pipeline.

A plate page (``article_type='plate'``) consists of three semantic
parts: an optional header (centered title text), a required collection
of image+caption pairs, and an optional footer (credits, legends).
The wikisource markup that expresses this varies wildly — wikitables,
HTML tables, ``{{c|…}}`` centering, ``{{img float}}``, ``{{FI}}``,
``{{raw image}}``, and combinations and nestings — but the SEMANTIC
shape is always the same.

This parser deliberately ignores structure during collection and uses
positional information for pairing, so it handles all 29 structural
signatures with one code path.

Pipeline:

* :func:`collect_images`   — every image reference, regardless of
                             markup form, with source-byte positions.
* :func:`collect_captions` — every caption-shaped text fragment,
                             positively detected by prefix shape.
* :func:`derive_bookends`  — header (non-caption text before the
                             first matter), footer (after the last).
* :func:`pair_images_with_captions` — position-based pairing with
                             explicit-number override and shared-
                             caption (colspan) detection.
* :func:`parse_plate`      — entry point; renders the assembled plate
                             body in the same ``{{IMG:fn|cap}}`` /
                             ``{{LEGEND:…}LEGEND}`` marker scheme the
                             rest of the pipeline emits.
"""
from __future__ import annotations

import re

from britannica.cleaners.unicode import replace_print_artifacts
from britannica.parsers import img_float as _img_float_parser
from britannica.parsers.plate.bookends import (
    _strip_bookend_markup,
    derive_bookends,
)
from britannica.parsers.plate.captions import (
    _caption_end,
    _find_bare_descriptive_captions,
    _is_credit,
    _normalize_for_capture,
    _roman_to_int,
    _strip_caption_markup,
    collect_captions,
)
from britannica.parsers.plate.images import (
    _djvu_filename,
    _filename_number,
    _preclean,
    collect_images,
)
from britannica.parsers.plate.models import CaptionFrag, ImageRef, PlateBlock
from britannica.parsers.plate.pair import (
    _try_render_as_outline_plate,
    pair_images_with_captions,
)

# ---------------------------------------------------------------------------
# Stage 0: pre-clean
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Stage 1: collect images
# ---------------------------------------------------------------------------

# `[[Image:fn|opts]]` / `[[File:fn|opts]]` — the most common form.
# `{{raw image|filename}}` — full-page DjVu plate renders, etc.
# `{{img float|…}}` and `{{FI|…}}` — both delegate to the unified
# img_float parser for filename + caption extraction.  Brace-balanced
# match supporting up to 4 levels of nesting in the body (CASTLE Fig 9
# ``cap={{Fs85|{{center|{{EB1911 Fine Print|{{sc|Fig.}}…}}}}}}`` is 4).

# ---------------------------------------------------------------------------
# Stage 2: collect captions
# ---------------------------------------------------------------------------

# Formatting templates to unwrap before caption detection.  The
# unwrapping pads to original byte length so caption-position offsets
# in the normalized text equal positions in the source.  Without this
# step, ``{{sc|Fig.}}1.—CLÉMENT`` (AERONAUTICS-style) hides the
# ``Fig.`` prefix from the caption-shape predicate and the actual
# caption is missed.
# Case-changing templates: {{uc|X}} → X.upper(), {{lc|X}} → X.lower().
# Wikisource SHEEP plate captions like ``{{uc|Lincoln Longwool Ram}}``
# render as ``LINCOLN LONGWOOL RAM`` in the wiki — without applying the
# case change here, the bare-descriptive caption predicate
# (predominantly uppercase letters) rejects the unwrapped text.
# Multi-arg layout templates (running-header etc.) — keep all args,
# joined by a space, padded to the original length.
# Style-only templates carry CSS tokens (margins, line-heights,
# spacers), not renderable text.  Dropping the whole template incl.
# arguments is the only correct unwrap; keeping the last arg leaks
# layout strings like ``lh1``, ``mc``, ``70%`` into captions and
# bookends, AND leaving the template in place blocks outer-template
# unwrap because the nested braces defeat ``[^{}]*``.

# `1.`, `1.—`, `1. `, `Fig. 1.`, `Plate I.—`, ``a.``, ``(b)`` etc.
# IGNORECASE is *not* set: the trailing lookahead specifically
# requires an UPPERCASE letter to start the caption text, distinguishing
# real caption prefixes from mid-sentence matches like
# ``King Edward VII. and the smaller "Cullinan"…`` (REGALIA Plate I —
# IGNORECASE made ``[A-Z]`` match the lowercase ``a`` in ``and`` and
# emit a phantom caption #7).  Case variants of the optional ``Fig`` /
# ``Plate`` words are listed explicitly.

# Photo credits are a distinct caption *role* — they identify the
# source of the photograph rather than describing the subject.  When
# both a credit and a descriptive caption sit between two images, the
# descriptive one is the primary; the credit attaches as a
# parenthetical.  Detected by the cleaned-text shape since the wiki
# markup is too varied (``''Photo, X''``, ``{{smaller|(''Photo, X.'')}}``,
# bare ``Photo, X.``) to predicate on the source.
# Tightened so descriptive captions that happen to start with the
# word ``Photograph`` aren't mistaken for credits.  A real credit
# shape has Photo/Photograph immediately followed by a comma, period,
# parenthesis, ``by``, or ``from`` — denoting attribution rather than
# a sentence about a photograph.

# ---------------------------------------------------------------------------
# Stage 3: header / footer
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Stage 4: pair images with captions
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_plate(raw: str) -> str:
    """Render a plate page's body from its raw wikitext.

    Output is the same ``{{IMG:fn|cap}}`` / ``{{LEGEND:…}LEGEND}``
    marker scheme used by every other ``article_type`` so the viewer
    needs no plate-specific rendering path.
    """
    if not raw or not raw.strip():
        return ""
    text = _preclean(raw)
    images = collect_images(text)

    # Single composite image followed by a hierarchical numbered
    # caption block (GEMS PLATE I): emit IMG + OUTLINE rather than
    # mashing all 26 numbered items into one IMG caption.
    outline_result = _try_render_as_outline_plate(text, images)
    if outline_result is not None:
        return outline_result

    captions = collect_captions(text, images)

    # ``is_shared`` captions (colspan-marked plate-wide titles like
    # DOG PLATE IV's ``TYPICAL TOY DOGS``) decorate the plate as
    # header or footer based on source position, not as per-image
    # captions.  Excluding them from bookend matter-computation lets
    # ``derive_bookends`` ignore them when deciding what counts as
    # "before-the-first-matter" / "after-the-last-matter".
    per_image_caps = [c for c in captions if not c.is_shared]
    shared_caps = [c for c in captions if c.is_shared]

    header, footer = derive_bookends(text, images, per_image_caps)
    pairs, legends = pair_images_with_captions(images, captions)

    # Distribute *between-image* shared captions to ``legends``.
    # Pre-first-image and post-last-image shared captions are already
    # included in header / footer text by ``derive_bookends`` —
    # ``per_image_caps`` excludes is_shared from the matter region,
    # so the bytes spanned by those colspan cells fall into the
    # bookend ranges and ``_strip_bookend_markup`` cleans them.
    # Re-appending here would duplicate the text (HORSE PLATE I had
    # this exact bug — footer ended up "BREEDS OF HORSES… BREEDS OF
    # HORSES…" repeated).  Only between-image shared caps need
    # explicit handling because they sit inside the matter region.
    if images and shared_caps:
        first_img_pos = min(r.pos for r in images)
        last_img_end = max(r.end_pos for r in images)
        for sc in sorted(shared_caps, key=lambda c: c.pos):
            if first_img_pos <= sc.pos < last_img_end:
                legends.append(sc.text)

    parts: list[str] = []
    if header:
        parts.append(header)
    for fn, cap in pairs:
        if cap:
            parts.append(f"{{{{IMG:{fn}|{cap}}}}}")
        else:
            parts.append(f"{{{{IMG:{fn}}}}}")
    for legend in legends:
        parts.append(f"{{{{LEGEND:{legend}}}LEGEND}}")
    if footer:
        parts.append(footer)
    text = "\n\n".join(parts)
    # Normalize codepoints (fullwidth `=` `+` `-`, ligature glyphs like
    # `℔` `℥`) and collapse excessive blank lines at the plate's exit
    # point — `_transform_text_v2` does the same for non-plate
    # articles, so each path produces its body cleanly in isolation.
    text = replace_print_artifacts(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text

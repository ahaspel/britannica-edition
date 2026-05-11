"""Stage 1: collect every image reference in a plate's wikitext.

Walks the source byte-for-byte looking for the four image-reference
shapes used in EB1911 plate pages: ``[[File:…]]``, ``[[Image:…]]``,
``{{IMG:…}}``, ``{{raw image|…}}``, ``{{img float|file=…}}``, and
``{{FI|file=…}}``.  Returns a positional list of ``ImageRef`` so
``pair_images_with_captions`` can match captions by relative position.
"""

from __future__ import annotations

import re

from britannica.parsers import img_float as _img_float_parser
from britannica.parsers.plate.models import ImageRef

def _preclean(raw: str) -> str:
    """Strip noinclude / section / comment shells.  Preserve everything
    else verbatim — stages 1-2 need accurate source byte offsets."""
    text = re.sub(r"<noinclude>.*?</noinclude>", "", raw,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<section[^>]+>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # ``&shy;`` (soft hyphen) and ``&zwj;``/``&zwnj;`` (zero-width
    # joiners) are invisible word-break / glyph-shaping hints; they
    # interrupt single words for line-wrapping (``repro&shy;duced``).
    # Stripping them here — before image-collection takes byte
    # positions — keeps the source's word boundaries intact.  Doing
    # it later (in normalize/strip_caption) replaces with a space,
    # which collapses but still splits the word in two.
    text = re.sub(r"&shy;|&zwj;|&zwnj;", "", text)
    return text


_FILE_LINK_RE = re.compile(
    r"\[\[(?:File|Image):([^|\]]+)(?:\|[^\]]*)?\]\]",
    re.IGNORECASE,
)

_RAW_IMAGE_RE = re.compile(
    r"\{\{\s*raw\s+image\s*\|\s*([^{}|]+?)\s*\}\}",
    re.IGNORECASE,
)

_IMG_TEMPLATE_RE = re.compile(
    r"\{\{\s*(?:img\s+float|figure|FI)\s*"
    r"((?:[^{}]|\{\{(?:[^{}]|\{\{(?:[^{}]|\{\{[^{}]*\}\})*\}\})*\}\})*)\}\}",
    re.IGNORECASE | re.DOTALL,
)

def _djvu_filename(raw_filename: str) -> str:
    """Translate a Commons DjVu page reference to its local cache name.

    ``EB1911 - Volume 24.djvu/1037`` → ``djvu_vol24_page1037.jpg``,
    matching the layout produced by ``download_djvu_crops.py``.  Other
    filenames pass through unchanged.
    """
    m = re.match(
        r"EB1911\s*-\s*Volume\s*(\d+)\.djvu/(\d+)",
        raw_filename.strip(),
        re.IGNORECASE,
    )
    if not m:
        return raw_filename.strip()
    vol = int(m.group(1))
    page = int(m.group(2))
    return f"djvu_vol{vol:02d}_page{page:04d}.jpg"


def _filename_number(filename: str) -> int | None:
    """Extract a trailing figure number from a filename.

    ``EB1911 Regalia, Plate I, 3.jpg`` → 3.  ``Fig. 17.jpg`` → 17.
    Returns None when no plausible figure number is at the end.
    """
    stem = re.sub(r"\.(?:jpg|jpeg|png|gif|svg)$", "", filename,
                  flags=re.IGNORECASE)
    # Trailing ", N" or "- N" or " Fig. N"
    m = re.search(r"(?:[,\s\-]|Fig\.?\s*)(\d+)\s*$", stem, re.IGNORECASE)
    return int(m.group(1)) if m else None


def collect_images(text: str) -> list[ImageRef]:
    """Walk ``text`` (post-preclean) and return every image reference
    in source order, regardless of which markup form expresses it.

    Image markers are non-overlapping: an ``[[Image:…]]`` inside the
    ``cap=`` field of a ``{{img float}}`` is part of THAT template's
    span and isn't double-counted.
    """
    found: list[ImageRef] = []

    # Walk template-form images first so their spans are claimed
    # before we look for inner [[Image:]] links.
    claimed: list[tuple[int, int]] = []

    for m in _IMG_TEMPLATE_RE.finditer(text):
        body = m.group(1)
        parsed = _img_float_parser.parse(body)
        if parsed is None:
            continue
        filename = _djvu_filename(parsed.filename)
        found.append(ImageRef(
            filename=filename,
            pos=m.start(),
            end_pos=m.end(),
            inline_caption=(parsed.caption or None),
            raw=m.group(0),
            number=_filename_number(filename),
        ))
        claimed.append((m.start(), m.end()))

    for m in _RAW_IMAGE_RE.finditer(text):
        if any(s <= m.start() < e for s, e in claimed):
            continue
        filename = _djvu_filename(m.group(1))
        found.append(ImageRef(
            filename=filename,
            pos=m.start(),
            end_pos=m.end(),
            raw=m.group(0),
            number=_filename_number(filename),
        ))
        claimed.append((m.start(), m.end()))

    for m in _FILE_LINK_RE.finditer(text):
        if any(s <= m.start() < e for s, e in claimed):
            continue
        filename = m.group(1).strip()
        found.append(ImageRef(
            filename=filename,
            pos=m.start(),
            end_pos=m.end(),
            raw=m.group(0),
            number=_filename_number(filename),
        ))
        claimed.append((m.start(), m.end()))

    found.sort(key=lambda r: r.pos)
    return found



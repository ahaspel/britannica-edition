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
from dataclasses import dataclass, field

from britannica.parsers import img_float as _img_float_parser


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ImageRef:
    """One image reference found in the source.

    ``inline_caption`` is the caption that lived INSIDE the image
    template (``{{img float|file=X|cap=Y}}`` carries Y on its own); if
    set, this image is already paired and stage 4 won't try to attach
    a separate caption to it.
    """
    filename: str
    pos: int                      # start byte position in the source
    end_pos: int                  # one past last byte
    inline_caption: str | None = None
    raw: str = ""                 # the matched markup, for debugging
    number: int | None = None     # number embedded in filename if any


@dataclass
class CaptionFrag:
    """One caption-shaped text fragment found in the source."""
    text: str                     # cleaned caption text
    pos: int
    end_pos: int
    number: int | None = None     # explicit prefix number if any
    is_credit: bool = False       # italic credit line, no figure number
    is_shared: bool = False       # colspan row → applies to multiple imgs
    raw: str = ""


@dataclass
class PlateBlock:
    header: str = ""
    pairs: list[tuple[str, str]] = field(default_factory=list)  # (filename, caption)
    shared_legends: list[str] = field(default_factory=list)
    footer: str = ""


# ---------------------------------------------------------------------------
# Stage 0: pre-clean
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Stage 1: collect images
# ---------------------------------------------------------------------------

# `[[Image:fn|opts]]` / `[[File:fn|opts]]` — the most common form.
_FILE_LINK_RE = re.compile(
    r"\[\[(?:File|Image):([^|\]]+)(?:\|[^\]]*)?\]\]",
    re.IGNORECASE,
)

# `{{raw image|filename}}` — full-page DjVu plate renders, etc.
_RAW_IMAGE_RE = re.compile(
    r"\{\{\s*raw\s+image\s*\|\s*([^{}|]+?)\s*\}\}",
    re.IGNORECASE,
)

# `{{img float|…}}` and `{{FI|…}}` — both delegate to the unified
# img_float parser for filename + caption extraction.  Brace-balanced
# match supporting up to 4 levels of nesting in the body (CASTLE Fig 9
# ``cap={{Fs85|{{center|{{EB1911 Fine Print|{{sc|Fig.}}…}}}}}}`` is 4).
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


# ---------------------------------------------------------------------------
# Stage 2: collect captions
# ---------------------------------------------------------------------------

# Formatting templates to unwrap before caption detection.  The
# unwrapping pads to original byte length so caption-position offsets
# in the normalized text equal positions in the source.  Without this
# step, ``{{sc|Fig.}}1.—CLÉMENT`` (AERONAUTICS-style) hides the
# ``Fig.`` prefix from the caption-shape predicate and the actual
# caption is missed.
_FORMATTING_TEMPLATE_RE = re.compile(
    r"\{\{\s*"
    r"(?:sc|small-caps|smaller|small|c|center|block\s+center|csc|"
    r"big|bold|nowrap|"
    r"x-larger|x-smaller|larger|fs|lh|"
    r"EB1911\s+(?:Fine\s+Print|article\s+link)|"
    r"float\s+left|float\s+right|right|left)"
    r"\s*\|"
    # Optional first arg (CSS value like ``88%`` or ``85``) followed
    # by ``|``.  ``{{lh|88%|TEXT}}`` is two-arg: the content is the
    # LAST arg, not the whole arg-list.  Without this, ``88%|`` leaks
    # into the unwrapped text and breaks downstream caption detection
    # (the ``|`` ends up inside what should be flat caption text).
    r"(?:[^{}|]*\|)?"
    r"([^{}]*)\}\}",
    re.IGNORECASE,
)

# Case-changing templates: {{uc|X}} → X.upper(), {{lc|X}} → X.lower().
# Wikisource SHEEP plate captions like ``{{uc|Lincoln Longwool Ram}}``
# render as ``LINCOLN LONGWOOL RAM`` in the wiki — without applying the
# case change here, the bare-descriptive caption predicate
# (predominantly uppercase letters) rejects the unwrapped text.
_UC_TEMPLATE_RE = re.compile(
    r"\{\{\s*uc\s*\|([^{}]*)\}\}", re.IGNORECASE,
)
_LC_TEMPLATE_RE = re.compile(
    r"\{\{\s*lc\s*\|([^{}]*)\}\}", re.IGNORECASE,
)

# Multi-arg layout templates (running-header etc.) — keep all args,
# joined by a space, padded to the original length.
_MULTI_ARG_LAYOUT_RE = re.compile(
    r"\{\{\s*(?:rh|RunningHeader)\s*\|([^{}]*)\}\}",
    re.IGNORECASE,
)

# Style-only templates carry CSS tokens (margins, line-heights,
# spacers), not renderable text.  Dropping the whole template incl.
# arguments is the only correct unwrap; keeping the last arg leaks
# layout strings like ``lh1``, ``mc``, ``70%`` into captions and
# bookends, AND leaving the template in place blocks outer-template
# unwrap because the nested braces defeat ``[^{}]*``.
_STYLE_ONLY_TEMPLATE_RE = re.compile(
    r"\{\{\s*(?:ts|tspy|dhr|gap|nop|clear|em|float\s+left|float\s+right)"
    r"(?:\s*\|[^{}]*)?\s*\}\}",
    re.IGNORECASE,
)


def _normalize_for_capture(text: str, image_spans: list[tuple[int, int]]) -> str:
    """Return a copy of ``text`` with formatting and layout templates
    unwrapped to their inner text, PADDED with spaces so byte offsets
    in the result match the original source.  Spans claimed by image
    templates (``image_spans``) are left untouched so stage-1 image
    bytes aren't mutated.
    """
    out = list(text)

    def in_image_span(p: int) -> bool:
        return any(s <= p < e for s, e in image_spans)

    # Decode HTML entities in-place (length-preserving where possible)
    # so caption-prefix detection sees real punctuation.  ``&mdash;``
    # (7 chars) → ``—`` + 6 spaces; ``&nbsp;`` etc. all collapse to
    # padded spaces.  Image-span bytes are skipped.
    entity_map = {
        "&mdash;": "—",
        "&ndash;": "–",
        "&nbsp;": " ",
        "&emsp;": " ",
        "&ensp;": " ",
        "&thinsp;": " ",
        # Soft-hyphen and zero-width joiners are invisible
        # word-break / glyph-shaping hints; collapse to spaces in
        # normalized text so caption detection treats them as
        # whitespace rather than word characters.
        "&shy;": " ",
        "&zwj;": " ",
        "&zwnj;": " ",
        "&amp;": "&",
        "&quot;": '"',
        "&apos;": "'",
        "&lt;": "<",
        "&gt;": ">",
    }
    pos = 0
    while pos < len(out):
        ch = out[pos]
        if ch == "&":
            for ent, repl in entity_map.items():
                if "".join(out[pos:pos + len(ent)]) == ent:
                    if not in_image_span(pos):
                        replacement = repl + " " * (len(ent) - len(repl))
                        for i, c in enumerate(replacement):
                            out[pos + i] = c
                    pos += len(ent) - 1
                    break
        pos += 1

    # ``<br>`` / ``<br/>`` / ``<br />`` plays two roles in EB1911
    # plates: a visual line-wrap inside one caption's text (Babylonia
    # PLATE I's ``RELIEF REPRESENTING ASSUR-<br>BANI-PAL SPEARING A
    # LION.``) or a logical boundary between caption units
    # (``}}<br/>{{c|...``, or a sub-caption following a fully-stopped
    # phrase like ``Archaeology PLATE V``'s ``SEPULCHRAL POTTERY,
    # BRITISH ISLES.<br>1-3, Drinking cups...``).
    #
    # Distinguish by what sits *immediately before* the tag:
    #   - alphanumeric / ``-`` / ``,`` / ``;`` → mid-phrase wrap.
    #     Replace with space so the line-scanner reads the caption as
    #     one continuous line.
    #   - anything else (``.``, ``}``, ``>``, paren, etc.) → boundary.
    #     Leave intact so line_re's ``<br>`` lookbehind still kicks in
    #     and the next caption unit is recognised.
    _wrap_chars = set("-,;")
    for br_tag in ("<br />", "<br/>", "<br>"):
        idx = 0
        current = "".join(out)
        while True:
            idx = current.find(br_tag, idx)
            if idx == -1:
                break
            if not in_image_span(idx):
                prev_char = current[idx - 1] if idx > 0 else ""
                is_wrap = prev_char.isalnum() or prev_char in _wrap_chars
                if is_wrap:
                    for i in range(len(br_tag)):
                        out[idx + i] = " "
            idx += len(br_tag)

    # Style-only templates: drop entire template (incl. arguments)
    # length-preservingly.  These templates carry CSS tokens, not
    # text content, so leaving them in place blocks the outer-template
    # unwrap loop below — ``[^{}]*`` in _FORMATTING_TEMPLATE_RE can't
    # pass the nested braces.  Archaeology PLATE VI's ``{{center|…
    # {{dhr|60%}}…}}`` was a textbook case: ``{{dhr}}`` had to drop
    # before the outer ``{{center}}`` could unwrap and expose the
    # caption text.
    current = "".join(out)
    for m in _STYLE_ONLY_TEMPLATE_RE.finditer(current):
        if in_image_span(m.start()):
            continue
        if any(m.start() <= s < m.end() for s, e in image_spans):
            continue
        full_len = m.end() - m.start()
        for i in range(full_len):
            out[m.start() + i] = " "

    # Apply iteratively to handle nested wrappers.
    for _ in range(6):
        changed = False
        # Case-changing templates first so subsequent passes see the
        # final-cased text.
        for pat, transform in (
            (_UC_TEMPLATE_RE, str.upper),
            (_LC_TEMPLATE_RE, str.lower),
        ):
            current = "".join(out)
            for m in pat.finditer(current):
                if in_image_span(m.start()):
                    continue
                if any(m.start() <= s < m.end() for s, e in image_spans):
                    continue
                inner = transform(m.group(1))
                full_len = m.end() - m.start()
                pad = " " * (full_len - len(inner))
                replacement = inner + pad
                for i, ch in enumerate(replacement):
                    out[m.start() + i] = ch
                changed = True
        for pat in (_FORMATTING_TEMPLATE_RE, _MULTI_ARG_LAYOUT_RE):
            current = "".join(out)
            for m in pat.finditer(current):
                if in_image_span(m.start()):
                    continue
                # Don't normalize templates that span image links — the
                # rewrite would overwrite the link's bytes and shift its
                # position out of sync with the image_span list.
                # ``{{center|[[image:X]]<br>caption}}`` is the canonical
                # case (BREWING).  Leave such templates untouched; their
                # caption text remains discoverable via the cell-only or
                # numbered-prefix predicates without unwrapping.
                if any(m.start() <= s < m.end() for s, e in image_spans):
                    continue
                inner = m.group(1)
                if pat is _MULTI_ARG_LAYOUT_RE:
                    inner = inner.replace("|", " ")
                # Newlines INSIDE a formatting template's content are
                # source-layout artefacts (the editor wrapped a long
                # caption); they aren't logical line breaks.  Without
                # this collapse, multi-line captions like Theatre
                # PLATE II's ``{{c|{{smaller|ASPENDUS, INTERIOR OF
                # THE UPPER\nGALLERY OF THE THEATRE.}}}}`` get
                # clipped at the first ``\n`` by line_re's
                # newline-excluding charclass.
                inner = inner.replace("\n", " ")
                full_len = m.end() - m.start()
                pad = " " * (full_len - len(inner))
                replacement = inner + pad
                for i, ch in enumerate(replacement):
                    out[m.start() + i] = ch
                changed = True
        if not changed:
            break

    return "".join(out)


# `1.`, `1.—`, `1. `, `Fig. 1.`, `Plate I.—`, ``a.``, ``(b)`` etc.
# IGNORECASE is *not* set: the trailing lookahead specifically
# requires an UPPERCASE letter to start the caption text, distinguishing
# real caption prefixes from mid-sentence matches like
# ``King Edward VII. and the smaller "Cullinan"…`` (REGALIA Plate I —
# IGNORECASE made ``[A-Z]`` match the lowercase ``a`` in ``and`` and
# emit a phantom caption #7).  Case variants of the optional ``Fig`` /
# ``Plate`` words are listed explicitly.
_CAPTION_PREFIX_RE = re.compile(
    r"(?:^|(?<=[\s|}\)\]])|(?<=^))"      # boundary at line/word/cell start
    r"((?:Fig|fig|FIG|Plate|plate|PLATE)\.?\s*)?"  # group 1: optional prefix word
    r"(\d+|[IVXivx]+)"                    # group 2: number (arabic or roman)
    r"(\s*\.\s*[—–\-]?\s*)"               # group 3: period + optional dash
    # Permit wikitext italic/bold markers (``''text''`` / ``'''text'''``)
    # between the prefix and the first uppercase letter.  PALAEOBOTANY
    # ``Fig. 1.—''Calamites''`` and similar patterns put the Latin
    # binomial in italics — without this, the prefix matches but the
    # uppercase-letter lookahead fails.
    r"(?=[']*[A-Z])",
)


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
_CREDIT_TEXT_RE = re.compile(
    r"^\(?\s*(?:"
    r"Photo(?:graph)?s?\s*(?:[,\.\)]|by\s|from\s)|"
    r"By\s+permission"
    r")",
    re.IGNORECASE,
)


def _is_credit(text: str) -> bool:
    return bool(_CREDIT_TEXT_RE.match(text.strip()))


def _strip_caption_markup(text: str) -> str:
    """Clean a caption text fragment of markup that doesn't belong in
    the rendered caption."""
    # Decode HTML entities common in EB1911 plates.
    text = re.sub(r"&mdash;", "—", text)
    text = re.sub(r"&ndash;", "–", text)
    text = re.sub(r"&nbsp;|&emsp;|&ensp;|&thinsp;", " ", text)
    # ``&shy;`` (soft hyphen) and ``&zwj;``/``&zwnj;`` (zero-width
    # joiners) are invisible word-break / glyph-shaping hints used in
    # the source for line-wrapping — they have no place in flat
    # caption text.  REGALIA Plate I's plate-wide credit had ``repro
    # &shy;duced`` and ``pos&shy;session`` — without this strip they
    # leaked verbatim into the LEGEND.
    text = re.sub(r"&shy;|&zwj;|&zwnj;", "", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&#\d+;", " ", text)
    # Style-only templates: drop ENTIRE template incl. arguments.  The
    # arguments are CSS-style tokens, not renderable text.  Without
    # this, ``{{ts|mc|fs085|lh110}}`` would unwrap to its last arg
    # ``lh110`` (via the multi-arg unwrap below) and leak a layout
    # token into the caption / bookend.  The list is closed and small;
    # add new entries only when a new style-only template name is
    # observed in the corpus.
    text = re.sub(
        r"\{\{\s*(?:ts|tspy|dhr|gap|nop|clear|float\s+left|float\s+right)"
        r"(?:\s*\|[^{}]*)?\s*\}\}",
        "",
        text,
        flags=re.IGNORECASE,
    )
    # Unwrap formatting templates iteratively (keep inner text).
    for _ in range(8):
        before = text
        # Single-arg formatting templates.
        text = re.sub(
            r"\{\{\s*(?:sc|small-caps|smaller|small|c|center|big|bold|"
            r"italic|nowrap|fs|lh|x-larger|x-smaller|larger|"
            r"EB1911 Fine Print|float\s+left|float\s+right)\s*\|"
            r"([^{}]*)\}\}",
            r"\1", text, flags=re.IGNORECASE,
        )
        # Multi-arg pipe templates: keep last arg.
        text = re.sub(
            r"\{\{[^{}|]+\|[^{}]*\|([^{}|]*)\}\}",
            r"\1", text,
        )
        # Two-arg pipe templates: keep last arg (handles ``{{Fs|85|text}}``).
        text = re.sub(
            r"\{\{[^{}|]+\|([^{}]*)\}\}",
            r"\1", text,
        )
        if text == before:
            break
    # Strip remaining bare templates.
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # Strip wiki bold/italic markers.
    text = re.sub(r"'''|''", "", text)
    # Strip wiki-table markers (defensive — these never belong in a caption).
    text = re.sub(r"\{\|[^\n]*", "", text)
    text = re.sub(r"\|\}", "", text)
    # Strip HTML tags.
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    # Strip wiki cell-attribute prefixes left by upstream walking.
    # Wiki cell syntax is ``|<attrs>|<content>`` where attr values may
    # be quoted (``align="right"``) or unquoted (``style=text-align:right``,
    # ``colspan=2``).  The unquoted form is what leaked through before
    # this regex was extended to accept it.
    text = re.sub(
        r'^(?:(?:align|valign|width|height|colspan|rowspan|style|class|'
        r'id|scope|bgcolor|cellpadding|cellspacing)'
        r'\s*=\s*'
        r'(?:"[^"]*"|\'[^\']*\'|[^\s|]+)'
        r'\s*)+'
        r'\|\s*',
        "", text,
    )
    # Defensive — caption text never contains pipes (wiki cell
    # separator) or stray braces (template-close fragments).  Without
    # this strip, emitting ``{{IMG:fn|cap}}`` breaks the marker syntax
    # when cap contains ``|`` or ``}}``: the AERONAUTICS rh-template
    # closing braces leak through and make the marker swallow
    # subsequent IMG markers in the body.
    text = re.sub(r"[|{}]", " ", text)
    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()
    return text.rstrip(",.|; ")


def _roman_to_int(s: str) -> int | None:
    s = s.upper()
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    if not all(c in values for c in s):
        return None
    total = 0
    prev = 0
    for c in reversed(s):
        v = values[c]
        total += v if v >= prev else -v
        prev = v
    return total or None


def _caption_end(text: str, start: int) -> int:
    """Find the end of a caption that begins at byte offset ``start``.

    A caption ends at:
      * the next caption-prefix on the same or following line
      * the next image marker (caller must mask those out before calling)
      * a blank line / paragraph break
      * the next wikitable cell separator (``\\n|`` not part of ``\\n|}``)
      * the next ``</td>`` / ``</tr>`` / ``</table>``
      * end of string
    """
    # Search window starts right after the prefix's last matched char.
    best = len(text)
    for pat in (
        r"\n\s*\n",                    # paragraph break
        r"\n\|\-",                     # next wikitable row
        r"\n\|(?!\})",                 # next wikitable cell
        r"</td>", r"</tr>", r"</table>",
        # Next caption prefix on a fresh start
        r"(?:^|\n|\s)(?:Fig|Plate)\.?\s*\d+\.\s*[—–\-]",
        r"(?:^|\n)\s*\d+\.\s*[—–\-]",
    ):
        m = re.search(pat, text[start + 1:], re.IGNORECASE)
        if m:
            best = min(best, start + 1 + m.start())
    return best


def _find_bare_descriptive_captions(
    normalized: str,
    image_spans: list[tuple[int, int]],
    claimed_offsets: set[int],
) -> list[CaptionFrag]:
    """Detect captions that lack a figure-number prefix — bare ALL-CAPS
    descriptive phrases like ``GREAT DANE.``, ``SHORTHORN BULL.``,
    ``HERMES, PRAXITELES.``.

    Three contextual shapes covered:

    * **Wiki/HTML table cell content** — DOG-style plates with image
      cells alternating with caption cells.
    * **Image-adjacent inline phrase** — CATTLE-style ``[[Image:X]]<br/>
      SHORTHORN BULL.`` within a ``{{center|…}}`` block.
    * **Standalone line** — phrase on its own line surrounded by
      blank lines or ``<br/>``.

    Predicate: at least 4 chars, no more than 200, predominantly
    uppercase letters (≥60%), no caption-prefix shape (those go
    through the numbered-prefix path).
    """
    found: list[CaptionFrag] = []

    def in_image_span(p: int) -> bool:
        return any(s <= p < e for s, e in image_spans)

    def is_bare_descriptive(content: str) -> bool:
        if not content or len(content) < 4 or len(content) > 200:
            return False
        cleaned = _strip_caption_markup(content)
        if not cleaned or len(cleaned) < 4:
            return False
        letters = re.findall(r"[A-Za-z]", cleaned)
        if not letters:
            return False
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_ratio < 0.60:
            return False
        if re.match(r"^(?:Fig|Plate)?\.?\s*\d+\.", cleaned, re.IGNORECASE):
            return False
        return True

    def emit_if_caption(content: str, start: int, end: int,
                        require_uppercase: bool = True,
                        is_shared: bool = False) -> None:
        if in_image_span(start):
            return
        if start in claimed_offsets:
            return
        if any(f.pos <= start < f.end_pos for f in found):
            return
        if "[[Image:" in content or "[[File:" in content:
            return
        if re.search(r"\{\{\s*(?:img\s+float|FI|raw\s+image)", content,
                     re.IGNORECASE):
            return
        if require_uppercase:
            if not is_bare_descriptive(content):
                return
        else:
            # Lenient predicate for cell content next to an image cell.
            # The structural position (caption-shaped cell adjacent to
            # an image-shaped cell) is what makes it a caption — case
            # is irrelevant.
            cleaned_check = _strip_caption_markup(content)
            if not cleaned_check or len(cleaned_check) < 4 or len(cleaned_check) > 400:
                return
            if not re.search(r"[A-Za-z]", cleaned_check):
                return
        cleaned = _strip_caption_markup(content)
        found.append(CaptionFrag(
            text=cleaned,
            pos=start,
            end_pos=end,
            number=None,
            is_credit=_is_credit(cleaned),
            is_shared=is_shared,
            raw=normalized[start:end],
        ))

    # 1+2. Wiki and HTML cells, collected together so we can do
    # cell-adjacency detection.  A text cell whose immediate neighbours
    # in source order include an image cell is a caption regardless of
    # case (SCULPTURE-style "JACOPO DELLA QUERCIA—Tomb, …" or
    # CERAMICS-style "Rhodian or Turkish: 16th century.").
    wiki_cell_re = re.compile(
        r"(?:^|\n)\|\s*(?!\}|\-)"
        r"(?:[a-zA-Z]+\s*=\s*\"[^\"]*\"\s*)*"
        r"\|?\s*"
        r"([^\n]+?)"
        r"(?=\n\||\n\|-|\n\|\}|$)",
    )
    html_cell_re = re.compile(
        r"<td\b[^>]*>([\s\S]*?)</td>",
        re.IGNORECASE,
    )
    # ``colspan="N"`` (N > 1) on a wiki cell signals a row-spanning
    # title or shared legend, not a per-image caption.  DOG PLATE IV
    # ends with ``| style="…" colspan="4" |TYPICAL TOY DOGS.`` — a
    # plate-wide title.  Without this signal, the title gets pulled
    # into the per-image caption pool and pairs with whichever image
    # has no other non-credit candidate, cascade-shifting captions.
    _colspan_re = re.compile(r'colspan\s*=\s*"?(\d+)"?', re.IGNORECASE)

    cells: list[tuple[int, int, str, bool]] = []  # +is_shared
    for m in wiki_cell_re.finditer(normalized):
        raw = m.group(1)
        raw_start = m.start(1)
        # Cell prefix between ``\n|`` and the captured content holds
        # any cell attributes (``style="…"``, ``colspan=N``, …).
        prefix = normalized[m.start():m.start(1)]
        cs_match = _colspan_re.search(prefix)
        is_shared_cell = bool(cs_match and int(cs_match.group(1)) > 1)
        # Wiki-table inline cell separator ``||`` splits a single line
        # into multiple cells.  Without this split, ``|img1 ||img2``
        # captures both as one cell, and a row of inline-separated
        # captions like SUN's ``|(1) … ||(2) …`` lands as one
        # concatenated caption.
        if "||" in raw:
            offset = 0
            for sub in raw.split("||"):
                cells.append((raw_start + offset,
                              raw_start + offset + len(sub),
                              sub.strip(),
                              is_shared_cell))
                offset += len(sub) + 2  # +2 accounts for the ``||``
        else:
            cells.append((raw_start, m.end(1), raw.strip(), is_shared_cell))
    for m in html_cell_re.finditer(normalized):
        # HTML ``<td colspan="N">`` works the same way.
        td_open = normalized[m.start():m.start(1)]
        cs_match = _colspan_re.search(td_open)
        is_shared_cell = bool(cs_match and int(cs_match.group(1)) > 1)
        cells.append((m.start(1), m.end(1), m.group(1).strip(), is_shared_cell))
    cells.sort(key=lambda c: c[0])

    def cell_has_image(start: int, end: int) -> bool:
        # Allow the image span to extend slightly past the captured
        # cell text (closing ``]]`` / template markers eat trailing
        # bytes that the cell regex doesn't include).
        for s, e in image_spans:
            if start <= s < end + 4:
                return True
        return False

    cell_is_image = [cell_has_image(s, e) for (s, e, _, _) in cells]

    for i, (start, end, content, is_shared) in enumerate(cells):
        if cell_is_image[i]:
            continue
        # Same-row neighbour (immediate prev/next cell) being image is
        # the strongest signal — captures ``| img1 | img2 ... |- |
        # cap1 | cap2`` interleaving.  Window width is ±5 so a wide
        # caption row (DOG plate has 4-image rows; the last caption
        # is offset 4 from the last image) still finds its image
        # neighbour.  Plates rarely exceed 5 columns; a tighter
        # window misses real adjacencies, a wider window risks
        # pulling in unrelated body cells.
        adjacent_image = any(
            j != i and 0 <= j < len(cells) and cell_is_image[j]
            for j in range(i - 5, i + 6)
        )
        if adjacent_image:
            emit_if_caption(content, start, end,
                            require_uppercase=False, is_shared=is_shared)
        else:
            emit_if_caption(content, start, end,
                            require_uppercase=True, is_shared=is_shared)

    # 3. Image-adjacent and standalone phrases.  After each image
    # span, scan forward through ``<br/>``, whitespace, and template
    # remnants to find the next text run.
    #
    # Two acceptance modes:
    #
    # * **Image-adjacent** — bytes between the nearest preceding image
    #   span's end and the candidate text are all whitespace (or
    #   equivalent template-residue spaces).  The structural position
    #   alone qualifies the text as a caption; the case predicate is
    #   irrelevant.  Catches Archaeology PLATE VI's mixed-case
    #   ``Bronze mounted wooden bucket …`` and similar inline captions
    #   that follow ``[[File:…]]`` directly in the same cell.
    # * **Standalone** — text not adjacent to an image; falls back to
    #   the all-caps predicate to avoid pulling body prose in plates
    #   that have free text floating around the matter.
    line_re = re.compile(
        r"(?:(?<=<br>)|(?<=<br/>)|(?<=<br />)|(?:^|\n)\s*)"
        r"([A-Z][^<\n|{}]{3,})"
        # Acceptable terminators: HTML break, newline, ``{{nop}}``,
        # end-of-string, OR ``}}`` (close of an unstripped wrapper —
        # Theatre PLATE II's ``{{block center|…CAPTION.}}`` couldn't
        # be unwrapped because it spanned an image link, so the
        # caption ends at the wrapper's own ``}}``).
        r"(?=\s*(?:<br|\n|\{\{nop|\}\}|$))",
    )

    def is_image_adjacent(start: int) -> bool:
        nearest_end = max(
            (e for s, e in image_spans if e <= start),
            default=-1,
        )
        if nearest_end < 0 or start - nearest_end > 400:
            return False
        return bool(re.fullmatch(r"\s*", normalized[nearest_end:start]))

    for m in line_re.finditer(normalized):
        cap_start = m.start(1)
        require_uc = not is_image_adjacent(cap_start)
        emit_if_caption(m.group(1).strip(), cap_start, m.end(1),
                        require_uppercase=require_uc)

    return found


def collect_captions(text: str, images: list[ImageRef]) -> list[CaptionFrag]:
    """Find every caption-shaped fragment outside the spans claimed by
    image markers in ``images``.

    Two positive predicates:

    * **Numbered prefix** (``N.``, ``Fig. N.``, ``Plate N.``) anywhere
      in the text — the dominant caption shape.
    * **Cell-only content** — a wiki or HTML table cell whose entire
      content is a short ALL-CAPS or descriptive phrase with no image
      reference.  Picks up DOG-style ``GREAT DANE.`` captions and
      SCULPTURE-style bare titles that lack a figure number.

    Searches a NORMALIZED copy of the text in which formatting and
    layout templates (``{{sc|X}}``, ``{{em|X}}``, ``{{rh|A|B|C}}``,
    etc.) are unwrapped to their inner content, padded with spaces so
    byte offsets stay aligned with the source.
    """
    image_spans = [(r.pos, r.end_pos) for r in images]
    normalized = _normalize_for_capture(text, image_spans)

    def in_image_span(p: int) -> bool:
        return any(s <= p < e for s, e in image_spans)

    found: list[CaptionFrag] = []
    claimed_offsets: set[int] = set()

    for m in _CAPTION_PREFIX_RE.finditer(normalized):
        cap_start = m.start()
        if in_image_span(cap_start):
            continue
        if cap_start in claimed_offsets:
            continue
        # Skip prefix matches that fall inside an already-captured
        # caption's range.  ``_CAPTION_PREFIX_RE`` matches any ``N.``
        # followed by uppercase, including phrases inside a longer
        # caption — SHIPBUILDING PLATE III's
        # ``Fig. 40.—Curves of E.H.P. … Type 1. Block Coefficient
        # ·495.`` matches ``40.—`` AND ``1.`` (in ``Type 1.``); the
        # second was emitting a phantom ``Block Coefficient ·495``
        # caption inside the first one's range.
        if any(f.pos <= cap_start < f.end_pos for f in found):
            continue
        claimed_offsets.add(cap_start)

        end = _caption_end(normalized, m.end())
        for s, e in image_spans:
            if cap_start < s < end:
                end = min(end, s)
        body_raw = normalized[m.end():end]
        cleaned = _strip_caption_markup(body_raw)
        if not cleaned or len(cleaned) < 3:
            continue
        num_str = m.group(2)
        if num_str.isdigit():
            number = int(num_str)
        else:
            number = _roman_to_int(num_str)
        # Rebuild the rendered figure prefix ("Fig. 54.—") so the
        # caption keeps its number label.  Source variants are
        # case-normalized; default to "Fig." when the prefix word was
        # absent in source (typesetters' standard for in-plate figures).
        prefix_word = (m.group(1) or "").strip().rstrip(".").strip()
        if not prefix_word:
            prefix_word = "Fig"
        elif prefix_word.lower().startswith("plate"):
            prefix_word = "Plate"
        else:
            prefix_word = "Fig"
        text_with_prefix = f"{prefix_word}. {num_str}.—{cleaned}"
        found.append(CaptionFrag(
            text=text_with_prefix,
            pos=cap_start,
            end_pos=end,
            number=number,
            is_credit=_is_credit(cleaned),
            raw=text[cap_start:end],
        ))

    # Augment with bare-descriptive captions (DOG, CATTLE, SCULPTURE,
    # etc.).  Skip when the new caption's range overlaps an existing
    # prefix-detected one — bidirectional check, since the bare-
    # descriptive path may capture starting BEFORE a numbered prefix
    # (e.g. SHIPBUILDING PLATE I's ``{{sc|Fig}}. 35.—If length…``
    # padded ``Fig`` at pos 57 while the numbered prefix matches at
    # pos 69).  The simple ``c.pos inside f range`` check misses this
    # because c.pos < f.pos.
    for c in _find_bare_descriptive_captions(
        normalized, image_spans, claimed_offsets
    ):
        if any(c.pos < f.end_pos and f.pos < c.end_pos for f in found):
            continue
        found.append(c)

    found.sort(key=lambda c: c.pos)
    return found


# ---------------------------------------------------------------------------
# Stage 3: header / footer
# ---------------------------------------------------------------------------

def _strip_bookend_markup(text: str) -> str:
    """Aggressive cleanup for header/footer text — strips everything a
    caption cleanup strips, plus wiki-table row separators (``|-``),
    bare cell-attribute fragments (``|ac``, ``|valign="bottom"``),
    standalone pipe lines, AND unmatched template openings/closers
    (``{{center|`` with no nearby ``}}``, stray ``}}``).

    Bookend text often slices through the middle of a template span —
    BREWING's ``{{center|[[image:X]]…}}`` puts ``{{center|`` before the
    first matter and ``}}`` after the last.  Without unmatched-fragment
    stripping, the header would render as the literal word
    ``center`` (template name) and the footer as a stray ``}}``.
    """
    text = _strip_caption_markup(text)
    # Wiki-table cell-attribute syntax: ``align="x"``, ``colspan=2``,
    # ``width="100%"``, ``style="…"`` — these are wikitable grammar,
    # not text content.  Bookend text only ever sees them as residue
    # from cell prefixes the cell-walker didn't consume.
    text = re.sub(
        r'\b(?:align|valign|width|height|colspan|rowspan|style|class|'
        r'id|scope|bgcolor|cellpadding|cellspacing)'
        r'\s*=\s*'
        r'(?:"[^"]*"|\'[^\']*\'|[\w%#-]+)',
        "",
        text,
        flags=re.IGNORECASE,
    )
    # CSS ``property: value`` fragments left after ``style="…"`` is
    # gone or after a ``{{ts|…}}`` stripped to its last arg.  Only
    # property names that actually appear in EB1911 plate templates.
    text = re.sub(
        r'\b(?:width|height|padding|margin|border|background|color|'
        r'text-align|vertical-align|font-size|line-height|float)'
        r'(?:-(?:top|bottom|left|right|color|size|style|width|spacing|family))?'
        r'\s*:\s*'
        r'[^\s;|]+;?',
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"^\s*\|\-+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\|\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\|[a-zA-Z]{1,4}(?=\s|$|\|)", "", text)
    # Strip unmatched template-opener fragments: ``{{name|`` or ``{{name``
    # with no matching ``}}`` in the string.
    text = re.sub(r"\{\{[^{}|]+\|", "", text)
    text = re.sub(r"\{\{[^{}]*", "", text)
    text = re.sub(r"\}\}+", "", text)
    # Stray dashes left from ``|-`` row separators that the
    # multi-line regex above didn't catch (single-line bookend, or
    # collapsed whitespace already merged the line).
    text = re.sub(r"(?:^|\s)-(?=\s|$)", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def derive_bookends(text: str, images: list[ImageRef],
                    captions: list[CaptionFrag]) -> tuple[str, str]:
    """Return ``(header, footer)`` derived from non-matter text at
    either end of the source."""
    matter_starts = (
        [r.pos for r in images]
        + [c.pos for c in captions]
    )
    matter_ends = (
        [r.end_pos for r in images]
        + [c.end_pos for c in captions]
    )
    if not matter_starts:
        cleaned = _strip_bookend_markup(text)
        return cleaned, ""
    first_pos = min(matter_starts)
    last_end = max(matter_ends)
    header = _strip_bookend_markup(text[:first_pos])
    footer = _strip_bookend_markup(text[last_end:])
    return header, footer


# ---------------------------------------------------------------------------
# Stage 4: pair images with captions
# ---------------------------------------------------------------------------

def pair_images_with_captions(
    images: list[ImageRef],
    captions: list[CaptionFrag],
) -> tuple[list[tuple[str, str]], list[str]]:
    """Return ``(pairs, shared_legends)``.

    Algorithm:
      1. Inline captions (from ``{{img float|cap=…}}``) attach immediately.
      2. Explicit-number override: when both filename and caption carry
         the same trailing number, pair them regardless of position.
      3. Remaining images take the nearest unclaimed caption by source
         position (preferring the one immediately following the image).
      4. Captions left over after every image is paired become shared
         legends if they're long enough to read as collective; short
         leftovers are ignored.
    """
    pairs: list[tuple[str, str]] = []
    used_caption_ids: set[int] = set()

    # 1. Inline captions take precedence.
    for img in images:
        if img.inline_caption:
            cleaned = _strip_caption_markup(img.inline_caption)
            pairs.append((img.filename, cleaned))
            img.inline_caption = "__USED__"  # mark consumed

    # 2. Explicit-number override.
    cap_by_number: dict[int, list[CaptionFrag]] = {}
    for c in captions:
        if c.number is not None:
            cap_by_number.setdefault(c.number, []).append(c)
    for img in images:
        if img.inline_caption == "__USED__":
            continue
        if img.number is None:
            continue
        candidates = cap_by_number.get(img.number, [])
        candidates = [c for c in candidates if id(c) not in used_caption_ids]
        if candidates:
            # Prefer the closest by position.
            best = min(candidates, key=lambda c: abs(c.pos - img.pos))
            pairs.append((img.filename, best.text))
            used_caption_ids.add(id(best))
            img.inline_caption = "__USED__"

    # 3. Position-based pairing for the rest.  Two passes:
    #    - First pass uses NON-CREDIT captions only — descriptive
    #      captions ("JACOPO DELLA QUERCIA—Tomb…") claim the primary
    #      slot.
    #    - Images that didn't find a non-credit fall back to credits
    #      in a second pass.
    # SCULPTURE PLATE I has photo-credit rows BETWEEN image rows and
    # descriptive-caption rows; without this two-pass logic the
    # nearest-by-position rule pairs every image with its photo
    # credit ("(Photo, Brogi.)") and the descriptive captions dangle
    # as legends at the bottom.
    remaining_imgs = [r for r in images if r.inline_caption != "__USED__"]
    remaining_caps = [c for c in captions if id(c) not in used_caption_ids]

    def _pick_best(img: ImageRef, pool: list[CaptionFrag]) -> CaptionFrag | None:
        after = [c for c in pool if c.pos > img.pos]
        if after:
            return min(after, key=lambda c: c.pos - img.pos)
        before = [c for c in pool if c.pos < img.pos]
        if before:
            return max(before, key=lambda c: c.pos)
        return None

    img_to_cap: dict[str, str] = {}
    for img in remaining_imgs:
        # ``is_shared`` cells (colspan>1) are plate-wide titles, not
        # per-image captions — exclude from primary pool so they
        # become LEGENDs at step 5.  Without this, DOG PLATE IV's
        # ``TYPICAL TOY DOGS`` (colspan=4 footer) gets pulled into the
        # primary slot and cascades the per-image pairing off by one.
        non_credits = [c for c in remaining_caps
                       if not c.is_credit and not c.is_shared
                       and id(c) not in used_caption_ids]
        best = _pick_best(img, non_credits)
        if best is not None:
            img_to_cap[img.filename] = best.text
            used_caption_ids.add(id(best))
        else:
            img_to_cap[img.filename] = ""
    # Second pass: images without a non-credit caption fall back to
    # credits.
    for img in remaining_imgs:
        if img_to_cap.get(img.filename):
            continue
        credits = [c for c in remaining_caps
                   if c.is_credit and id(c) not in used_caption_ids]
        best = _pick_best(img, credits)
        if best is not None:
            img_to_cap[img.filename] = best.text
            used_caption_ids.add(id(best))

    # Build pair list in source-image order.
    pairs_by_pos: list[tuple[str, str]] = []
    seen: set[str] = set()
    for img in images:
        if img.filename in seen:
            continue
        seen.add(img.filename)
        # Inline / explicit-number / position pass — find this image's
        # caption from any of the three lists.
        cap_text = ""
        for fn, cap in pairs:
            if fn == img.filename:
                cap_text = cap
                break
        else:
            cap_text = img_to_cap.get(img.filename, "")
        pairs_by_pos.append((img.filename, cap_text))

    # 4. Append credits to their column-aligned image caption.  When
    # a plate has a credit row of the same width as the image row,
    # the credit at column k belongs to the image at column k — both
    # are at the same x-coordinate in the rendered table.  Approximate
    # this with source-order pairing: if the count of unclaimed
    # credits exactly equals the image count, credit[i] attaches to
    # image[i] in source order.  When counts mismatch the structural
    # rule doesn't apply (credit row only covers some images, or
    # there's a per-figure credit interleaving); skip the attach
    # rather than risk duplicate pile-ups.
    unpaired_credits = sorted(
        (c for c in remaining_caps
         if c.is_credit and id(c) not in used_caption_ids),
        key=lambda c: c.pos,
    )
    images_in_order = sorted(images, key=lambda i: i.pos)
    if unpaired_credits and len(unpaired_credits) == len(images_in_order):
        for img, credit in zip(images_in_order, unpaired_credits):
            for j, (fn, cap) in enumerate(pairs_by_pos):
                if fn == img.filename:
                    credit_clean = credit.text.strip("() ")
                    if cap:
                        pairs_by_pos[j] = (fn, f"{cap} ({credit_clean})")
                    else:
                        pairs_by_pos[j] = (fn, f"({credit_clean})")
                    used_caption_ids.add(id(credit))
                    break

    # 5. Leftover non-credit, non-shared captions become shared
    # legends if long enough.  ``is_shared`` captions are handled
    # separately by ``parse_plate`` — they get routed to header or
    # footer based on source position so the viewer can render them
    # with title styling rather than caption styling.
    shared = []
    for c in remaining_caps:
        if id(c) in used_caption_ids:
            continue
        if c.is_credit or c.is_shared:
            continue
        if len(c.text) > 20:
            shared.append(c.text)
    return pairs_by_pos, shared


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _try_render_as_outline_plate(
    text: str, images: list[ImageRef],
) -> str | None:
    """Detect a single-composite-image plate whose post-image content
    is a hierarchical numbered caption block (GEMS PLATE I), and
    render it as ``{{IMG:fn}}`` followed by the OUTLINE marker.

    Returns ``None`` if the plate doesn't match this shape — the
    normal image+caption pairing path then runs.
    """
    if len(images) != 1:
        return None
    img = images[0]
    after = text[img.end_pos:]
    # Strip wrappers that interrupt the list-shape detection but
    # carry no list content of their own.
    after = re.sub(r"\{\{EB1911 fine print/[se]\}\}", "", after)
    after = re.sub(r"<div\b[^>]*>|</div>", "", after)
    # Flatten layout-only HTML tables (GEMS PLATE II uses a 2-column
    # `<table>` to split the numbered caption block into columns).
    # Strip the table / row / cell tags but keep their content; cells
    # are already in reading order (left-to-right then top-to-bottom).
    after = re.sub(
        r"</?(?:table|tbody|thead|tfoot|tr|td|th)\b[^>]*>",
        "", after, flags=re.IGNORECASE,
    )
    # `<br />` lines that survived as bare line-starts (GEM II's column
    # cells start with `\n<br />27–34.—…`); the line-start `<br />` is
    # a column-top spacer, not part of the list line — drop it so the
    # range header reads cleanly.
    after = re.sub(r"^\s*<br\s*/?>\s*", "", after, flags=re.MULTILINE | re.IGNORECASE)

    # Defer imports — these modules import this one.
    from britannica.pipeline.stages.elements import (
        ElementRegistry,
        _extract_outlines,
        _process_outline,
    )
    from britannica.pipeline.stages.transform_articles import (
        _transform_body_text,
    )

    registry = ElementRegistry()
    residual = _extract_outlines(after, registry, require_emphasis=False)
    outlines = [
        (k, raw) for k, (etype, raw) in registry.elements.items()
        if etype == "OUTLINE"
    ]
    if not outlines:
        return None

    parts = [f"{{{{IMG:{img.filename}}}}}"]
    for _, raw_block in outlines:
        rendered = _process_outline(raw_block, _transform_body_text)
        if rendered.strip():
            # Plate-caption outlines render in figure-caption styling
            # (smaller, italic, compressed) — re-tag the marker so
            # the viewer can route to a dedicated CSS class without
            # restyling every taxonomic OUTLINE corpus-wide.
            rendered = rendered.replace(
                "«OUTLINE:", "«PLATE_OUTLINE:", 1,
            ).replace(
                "«/OUTLINE»", "«/PLATE_OUTLINE»", 1,
            )
            parts.append(rendered.strip())

    # Preserve post-outline footer prose (credit line under the plate,
    # e.g. GEMS PLATE I's "All the above are in the British Museum.").
    # Strip OUTLINE placeholders from residual; what remains is plate
    # bookend matter.
    placeholder_keys = [k for k, _ in outlines]
    footer = residual
    for k in placeholder_keys:
        footer = footer.replace(k, "")
    footer = _transform_body_text(footer).strip()
    if footer:
        parts.append(f"«I»{footer}«/I»")

    return "\n\n".join(parts)


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
    return "\n\n".join(parts)

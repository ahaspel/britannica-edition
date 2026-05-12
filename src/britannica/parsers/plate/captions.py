"""Stage 2: detect caption-shaped text fragments.

A caption is positively recognised by its prefix shape (``Fig.``, ``Plate``,
roman / arabic numeral followed by ``.``, ``—``, etc.) and by its trailing
punctuation.  ``_normalize_for_capture`` unwraps formatting templates while
preserving byte offsets so detection sees real text but caption positions
still map back into the raw source.

Bare descriptive captions (no numeric prefix) are detected by
``_find_bare_descriptive_captions`` based on positional and styling
heuristics.
"""

from __future__ import annotations

import re

from britannica.parsers.plate.models import CaptionFrag, ImageRef

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

_UC_TEMPLATE_RE = re.compile(
    r"\{\{\s*uc\s*\|([^{}]*)\}\}", re.IGNORECASE,
)
_LC_TEMPLATE_RE = re.compile(
    r"\{\{\s*lc\s*\|([^{}]*)\}\}", re.IGNORECASE,
)

_MULTI_ARG_LAYOUT_RE = re.compile(
    r"\{\{\s*(?:rh|RunningHeader)\s*\|([^{}]*)\}\}",
    re.IGNORECASE,
)

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
    # …and cell-attribute strings that leaked *mid-text* — when a
    # walker glues a ``|attrs|content`` cell onto a preceding caption
    # without splitting on the ``|`` (GLASS PLATE II: ``…Jackson in
    # 1870. align="center" valign="top" Fig. 12.…``; ROPE PLATE legends
    # ``- style="font-size: 90%"``; PROCESS spacer cells
    # ``style="height: 0px; width: 40px"``).  The ``=`` is required so
    # prose words ("align the figures", "Art Nouveau style", "the width
    # of the river") aren't touched — same lesson as clean_body's
    # leaked_html_table_attrs.
    text = re.sub(
        r'\b(?:align|valign|width|height|colspan|rowspan|style|class|'
        r'id|scope|bgcolor|cellpadding|cellspacing|border)'
        r'\s*=\s*'
        r'(?:"[^"]*"|\'[^\']*\'|[^\s|]+)',
        "", text, flags=re.IGNORECASE,
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



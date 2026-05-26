"""Legend / attribution utility helpers (paragraph classification,
legend-line matching, attribution detection).

Historical note: this module also held ``_assemble_figures``, a
post-pass-style orchestrator that walked ``{{IMG:…}}`` markers in body
text and absorbed following paragraphs as attribution / legend.  It was
used first as a whole-body ``_process_figures`` post-pass (deleted when
the structural figure break landed) and then as a fallback inside the
``FIGURE`` element producer (deleted once ``_process_prose_figure``
became total over single + multi-image cases).  Whatever it did is now
done inside the figure producers themselves, which receive structural
spans from the walker and own their final output bytes.

The helpers below remain as Layer-A utilities; producers / classifiers
may call them as private diagnostics or transform aids, but nothing
threads their outputs across stages.
"""

from __future__ import annotations

import re

from britannica.captions import clean_caption
from britannica.markers import IMG_PARTS_RE


def _table_row_cells(row: str) -> list[str]:
    """Split a ``{{TABLE:}`` row into stripped cells.

    ``_process_table`` joins cells with ``" | "`` and renders an empty
    cell as ``" "`` — so an empty cell shows up as ``|   |`` (three
    spaces).  If a later pass collapses that to ``| |`` (one space),
    ``split(" | ")`` would read the second ``|`` as cell content rather
    than a separator; re-expanding any collapsed empty-cell gap first
    keeps the split robust.  No-op on ``_process_table``'s raw output
    (it never emits ``| |``); marker-internal pipes (``«LN:a|b«/LN»``
    etc.) have no space around them so they're untouched.
    """
    row = re.sub(r"\| (?=\|)", "|  ", row)
    # Strip the producer's ⟦…⟧ layout prefix (align / colspan / ⟦+⟧ caption) —
    # legend detection wants the cell's text, not its layout metadata.
    return [re.sub(r"^⟦[^⟧]*⟧", "", c.strip()).strip()
            for c in row.split(" | ")]


def _clean_loose_caption(text: str) -> str:
    """Produce clean caption text from a loose caption block extracted
    from ``{{c|…}}`` or a wikitable row.

    Markup-stripping is the shared ``clean_caption`` (templates,
    entities, cell-attrs, stray pipes/braces, unclosed openers); on top
    of that, this drops a leading source-attribution clause when a
    ``Fig. N.`` follows it ("From the Notice issued by the Board.
    Fig. 13.—…" → "Fig. 13.—…")."""
    text = clean_caption(text)
    m = re.search(r"((?:Fig|Plate)\.?\s*\d+)", text, re.IGNORECASE)
    if m and m.start() > 0:
        prefix = text[:m.start()].rstrip()
        if prefix.endswith((".", ":")):
            text = text[m.start():]
    return text.strip(" .|")


def _bundle_raw_image_with_caption(text: str) -> str:
    """Bundle a bare image reference and its following caption block
    into a single `[[File:X|caption]]` so the caption renders inside
    the figure rather than as a separate paragraph beneath it.

    Handles three image source forms:
      • `{{raw image|X}}` — EB1911 alternate syntax
      • `[[File:X|size|align]]` — caption-less wikilink with only
        size/position params
      • `[[Image:X|size|align]]` — same, alternate prefix

    Followed by a caption block in either form:
      • `{{c|…}}` (potentially nested) — single-line caption
      • `{| … |}` wikitable — multi-row attribution + caption
    """
    out: list[str] = []
    pos = 0
    img_pat = re.compile(
        # raw image: {{raw image|filename}}
        r"\{\{\s*raw\s+image\s*\|([^{}|]+)\}\}"
        # OR caption-less wikilink: [[File:filename|size|align]]
        r"|\[\[(?:File|Image):([^\]|]+)((?:\|[^\]|]+)*)\]\]",
        re.IGNORECASE,
    )

    _IMG_KEYWORDS = {"center", "left", "right", "thumb", "thumbnail",
                     "frameless", "frame", "border", "upright", "none"}

    def _has_caption(params: str) -> bool:
        """Return True if any | param is a real caption (not size/align)."""
        for p in params.split("|"):
            p = p.strip()
            if not p:
                continue
            lp = p.lower()
            if lp in _IMG_KEYWORDS:
                continue
            if re.match(r"^\d+px$|^x\d+px$|^\d+x\d+px$", lp):
                continue
            if "=" in p:
                continue
            return True
        return False

    for m in img_pat.finditer(text):
        out.append(text[pos:m.start()])

        if m.group(1) is not None:
            # {{raw image|X}} form — never has inline caption
            filename = m.group(1).strip()
            already_captioned = False
        else:
            # [[File:X|...]] form — skip if it already has a real caption
            filename = (m.group(2) or "").strip()
            params = m.group(3) or ""
            already_captioned = _has_caption(params)

        if already_captioned:
            # Don't touch — let normal extraction handle it
            out.append(m.group(0))
            pos = m.end()
            continue

        # Skip whitespace/newlines after the image
        cur = m.end()
        ws = re.match(r"\s*", text[cur:])
        cur += ws.end() if ws else 0
        caption = ""
        consumed_to = m.end()

        # Try {{c|…}} (or {{C|…}}) — count braces to find the close
        if text[cur:cur + 4].lower().startswith("{{c|"):
            end = _find_matching_double_braces(text, cur)
            if end > 0:
                inner = text[cur + 2:end - 2]
                inner = inner.split("|", 1)[1] if "|" in inner else inner
                caption = _clean_loose_caption(inner)
                consumed_to = end
        # Try wikitable {| … |}
        elif text[cur:cur + 2] == "{|":
            end = text.find("|}", cur)
            if end > 0:
                table = text[cur + 2:end]
                rows = re.split(r"\n\s*\|-[^\n]*\n", table)
                last_row = rows[-1].strip() if rows else ""
                if last_row.startswith("|"):
                    last_row = last_row[1:].strip()
                last_row = re.sub(
                    r'^(?:(?:align|style|width|valign|class|colspan|rowspan)'
                    r'\s*=\s*"[^"]*"\s*)+\|\s*', "", last_row,
                )
                caption = _clean_loose_caption(last_row)
                consumed_to = end + 2

        if caption:
            out.append(f"[[File:{filename}|{caption}]]")
        else:
            out.append(m.group(0))  # leave as-is
        pos = consumed_to
    out.append(text[pos:])
    return "".join(out)


def _find_matching_double_braces(text: str, start: int) -> int:
    """Given text[start:start+2] == '{{', return index just past the
    matching '}}'. Returns -1 if not balanced within 5000 chars."""
    if text[start:start + 2] != "{{":
        return -1
    depth = 0
    i = start
    end_search = min(len(text), start + 5000)
    while i < end_search - 1:
        ch2 = text[i:i + 2]
        if ch2 == "{{":
            depth += 1
            i += 2
        elif ch2 == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return i
        else:
            i += 1
    return -1


_LEGEND_CELL_RE = re.compile(
    r"^\s*([A-Za-z0-9](?:[A-Za-z0-9.,\- ]{0,20}?))"
    r"[,.]\s+(.+\S)\s*$")

_PARA_LEGEND_LABEL_ONE = r"[A-Za-z0-9][A-Za-z0-9.\-]{0,3}"

# A *typographically distinguished* label, used in the boundary lookahead
# inside `_split_multi_entry_line`.  EB1911 typesets figure-legend labels
# distinctly from body text: italicised (`''a''` → «I»a«/I» here), small
# caps, bold, OR bare uppercase letters / digits.  A bare lowercase token
# (`but`, `and`, `or`, `long`) appearing after `; ` or `. ` is body prose,
# not a label — BATRACHIA / HITTITES / OIL ENGINE / PIANOFORTE all fooled
# the old permissive `_label_ahead` because their connectives match the
# 1-4 char alnum label shape.  Restricting bare labels to uppercase/digit
# keeps every legitimate recovery (SHIP A-H, VISION A/SC/S, AMANITA A/B,
# BROOM 1/2, PEPPERMINT/TUMOUR/KINORHYNCHA/REPTILES all-italic) and
# rejects all observed regressions.
_TYPED_LEGEND_LABEL = (
    r"(?:"
    r"«(?:I|SC|B)»[A-Za-z0-9][A-Za-z0-9.\-]{0,3}«/(?:I|SC|B)»"
    r"|"
    r"[A-Z0-9][A-Z0-9.\-]{0,3}"
    r")"
)

def _build_legend_line_re(strict: bool) -> re.Pattern:
    # Single-label separator: `[,.]` required in strict, `[,.]?` in
    # permissive mode.
    single_sep = r"[,.]" if strict else r"[,.]?"
    # Text group uses `[\s\S]+?` so legend entries with internal
    # newlines (source `<br>` → space/newline) still match.
    return re.compile(
        r"^\s*(?:"
        r"(" + _PARA_LEGEND_LABEL_ONE +
        r"(?:\s*,\s*" + _PARA_LEGEND_LABEL_ONE + r")+)\."
        r"|"
        r"(" + _PARA_LEGEND_LABEL_ONE + r")" + single_sep +
        r")\s+([\s\S]+?)\s*$",
        re.DOTALL,
    )


_PARA_LEGEND_PLAIN_RE = _build_legend_line_re(strict=False)
_PARA_LEGEND_STRICT_RE = _build_legend_line_re(strict=True)

def _strip_inline_italic(text: str) -> str:
    """Remove `«I»…«/I»`, `«B»…«/B»`, `«SC»…«/SC»` open/close markers
    so a line can be matched against a plain-ASCII legend-label regex.

    Enumerate the exact formatting markers rather than using a
    permissive ``«/?[A-Z]+»`` pattern: ``«/FN»`` / ``«/SEC»`` / etc.
    would match that pattern too, but their OPENERS use a trailing
    colon (``«FN:``, ``«SEC:``) that the regex misses — stripping
    just the closer turned every footnote into an unclosed marker.
    Observed corpus-wide: 9 articles had unbalanced FN markers
    traceable to this (CONVEYORS, GAS, RING, PROBABILITY, …).
    """
    return re.sub(r"\u00ab/?(?:I|B|SC)\u00bb", "", text)


_INLINE_SECTION_HEADING_RE = re.compile(
    r"^\s*[A-Za-z0-9IVXLCDM]+\.?\s+"
    r"\u00abI\u00bb[^\u00ab]+\u00ab/I\u00bb"
    r"\s*[.\u2014\u2013\-]"
)

def _match_legend_line(line: str, *, strict: bool = False) -> tuple[str, str] | None:
    """Try to parse `line` as a legend entry.  Returns (label, text)
    or None.  Handles all the variants we've seen:

    * `A, text.`                       (comma separator)
    * `A. text.`                       (period separator)
    * `A text`                         (no separator — TOOL Fig. 65;
                                        only accepted in permissive mode)
    * `«I»A«/I», text.`                (italic label, outside punct)
    * `«I»A,«/I» text.`                (italic label, inside punct;
                                        TOOL Fig. 58 `A,` inside)
    * `A, B, text.`                    (multiple labels)
    * `«I»A«/I», «I»B«/I», text.`      (multiple italic labels)

    `strict=True` rejects single-label entries without a `,` or `.`
    separator, used for body-paragraph context where `a drilling…`
    (English article "a") should NOT be mistaken for a label.
    """
    # EB1911 inline section-heading pattern: ``LABEL. ''italic
    # title.''—prose``.  Check this BEFORE stripping italic markers,
    # since ``_strip_inline_italic`` would erase the signature.
    if _INLINE_SECTION_HEADING_RE.match(line):
        return None
    plain = _strip_inline_italic(line).strip()
    pat = _PARA_LEGEND_STRICT_RE if strict else _PARA_LEGEND_PLAIN_RE
    m = pat.match(plain)
    if not m:
        return None
    label = (m.group(1) or m.group(2) or "").strip().rstrip(".,")
    text = m.group(3).strip().rstrip(".")
    if not label or not text:
        return None
    # Reject lowercase ``fig`` as a legend label.  Real figure-legend
    # labels are short symbols (A, B, i, ii, α) — never the word ``fig``.
    # Lowercase ``fig.`` only appears in body prose as in-text references
    # (``see fig. 78``).  When such a sentence sits next to a figure,
    # ``_legend_entries_from_paragraph`` would otherwise parse it as a
    # legend entry and the surrounding prose paragraph gets wrapped as a
    # gigantic ``{{LEGEND:…}LEGEND}`` block (ORDNANCE p257 Fig 78).
    if label.lower() == "fig":
        return None
    return label, text


def _promote_paragraph_legends(text: str) -> str:
    """Convert `{{IMG:…}}` followed by legend-shaped prose into
    `{{IMG:…}}\\n\\n{{LEGEND:…}LEGEND}`.

    The legend content can appear in several layouts:
      * Multiple paragraphs, each one entry (TOOL Figs 2-3)
      * A single paragraph with multiple entries glued together
        separated by sentence boundaries (TOOL Figs 9-10)
      * Multiple lines in one paragraph, each one entry (TOOL Fig. 13)

    Everything from the IMG's closing `}}` up to the next blank-line
    paragraph break (or page-break marker) is handed to
    `_parse_legend_lines`, which already knows how to handle all
    three layouts.  Separator between IMG and the first legend line
    may be a single newline OR a blank line.
    """
    img_re = re.compile(r"\{\{IMG:[^}]+\}\}")
    block_end_re = re.compile(r"\n\n+|\x01PAGE:\d+\x01")
    out_parts: list[str] = []
    pos = 0
    for m in img_re.finditer(text):
        out_parts.append(text[pos:m.end()])
        pos = m.end()
        tail = text[pos:]
        # Skip past any whitespace (single `\n`, `\n\n`, spaces).
        ws_m = re.match(r"[ \t]*\n+", tail)
        if not ws_m:
            continue
        after_ws = pos + ws_m.end()
        # Find the end of the legend block: next blank-line break
        # or page marker.  Everything up to there is candidate
        # legend content.
        end_m = block_end_re.search(text, after_ws)
        block_end = end_m.start() if end_m else len(text)
        candidate = text[after_ws:block_end]
        # Don't try to absorb overly long chunks as a single legend —
        # real legends per figure are bounded (≤ 2000 chars is a
        # generous cap).
        if not candidate.strip() or len(candidate) > 2000:
            continue
        # Handle the "multi-entry on one line" shape by pre-splitting
        # the candidate on sentence-boundary-before-label.
        lines_to_parse: list[str] = []
        for line in candidate.split("\n"):
            line = line.strip()
            if not line:
                continue
            chunks = _split_multi_entry_line(line)
            if len(chunks) >= 2:
                lines_to_parse.extend(chunks)
            else:
                lines_to_parse.append(line)
        entries = _parse_legend_lines(lines_to_parse)
        if entries is None:
            continue
        # If the IMG already carries a caption AND the candidate
        # parses as a single entry whose "Label. text" matches that
        # caption, skip promotion AND drop the redundant candidate.
        # Vol 4 BOILER Fig. 16: source has
        # `[[File:…|491px]]<br />{{EB1911 Fine Print|Fig. 16.—Yarrow…}}`
        # — the image-extract regex already lifts the Fine-Print line
        # into the IMG caption; promoting it again as LEGEND made the
        # caption render twice.
        if len(entries) == 1:
            img_cap_match = IMG_PARTS_RE.match(m.group(0))
            if img_cap_match and img_cap_match.group(3):
                img_cap = img_cap_match.group(3).strip().rstrip(".,")
                legend_text = (
                    f"{entries[0][0]}. {entries[0][1]}"
                ).strip().rstrip(".,")
                if img_cap == legend_text:
                    pos = block_end
                    continue
        legend = "\n".join(f"{lbl}. {t}." for lbl, t in entries)
        out_parts.append(f"\n\n{{{{LEGEND:{legend}}}LEGEND}}\n\n")
        pos = block_end
    out_parts.append(text[pos:])
    return "".join(out_parts)


def _split_multi_entry_line(line: str) -> list[str]:
    """Split a line like `A, first text. B, second text. C, third.`
    into per-entry chunks using the sentence boundary immediately
    preceding the next label shape.  Labels may be wrapped in
    italic markers (`«I»A«/I», text`) — TOOL Figs 9-10.  Single-entry
    lines return the line unchanged.

    Also splits a literal ``||`` cell grid left over from a loose-laid-out
    wikitable that was unwrapped (not rendered as a table) before reaching
    the figure walker (AMANITA ``A, ||the young plant. ||g,||the gills.``,
    BEE Fig. 6 ``A. Abdomen ... || i. Intestine.``), and on ``; LABEL,``
    semicolon boundaries (SHIP Fig. 126 ``C. dynamo and motor; D,
    water-tight compartments;``).  When ``||`` cells alternate
    bare-label / text \u2014 an inline two-column legend grid \u2014 each label
    cell is merged with the text cell that follows it; otherwise each
    cell is one entry, re-split recursively in case it packs several."""
    if "||" in line:
        cells = [c.strip() for c in re.split(r"\s*\|\|\s*", line) if c.strip()]
        if len(cells) >= 2:
            # Alternating label-cell / text-cell grid?  Then every even
            # cell is a bare short label (`A,` / `g,` / `1.` / `\u00abI\u00bbp\u00ab/I\u00bb,`).
            if len(cells) % 2 == 0 and all(
                _LEGEND_LABEL_ALONE_RE.match(_strip_inline_italic(c))
                for c in cells[0::2]
            ):
                cells = [f"{cells[i]} {cells[i + 1]}"
                         for i in range(0, len(cells), 2)]
            out: list[str] = []
            for cell in cells:
                out.extend(_split_multi_entry_line(cell))
            return out

    _label_ahead = r"(?=" + _TYPED_LEGEND_LABEL + r"[,.]\s+)"
    # Don't split when the period that terminates the prior sentence
    # belongs to ``fig.`` / ``Fig.`` / ``figs.`` etc. — the number that
    # follows is a figure reference (``…in fig. 3.``), not the label of
    # a new legend entry.  Without this, body paragraphs that name
    # a figure get carved into pseudo-entries (DIFFERENCES § 3 /
    # ELASTICITY § 14 / IRON AND STEEL § 85 …).
    _not_fig_ref = (
        r"(?<!\bfig\.)(?<!\bFig\.)(?<!\bFIG\.)"
        r"(?<!\bfigs\.)(?<!\bFigs\.)(?<!\bFIGS\.)")
    split_re = re.compile(
        _not_fig_ref + r"(?<=\.)\s+" + _label_ahead  # `. ` sentence boundary (kept)
        + r"|\s*;\s+" + _label_ahead)                # `; ` semicolon boundary (dropped)
    parts = split_re.split(line)
    return [p.strip() for p in parts if p.strip()]


def _parse_legend_lines(
    lines: list[str], *, strict: bool = False,
) -> list[tuple[str, str]] | None:
    """Parse a list of lines as legend entries.  A line may contain
    multiple legend entries separated by sentence boundaries (TOOL
    Figs 4-5, HEXAPODA Fig. 3 Saw-Fly); those are split on `. LABEL,`
    boundaries and each chunk parsed independently.  A line that
    doesn't match gets appended as continuation to the PREVIOUS
    entry (multi-line anatomy descriptions in TOOL Figs 35/43/44).
    Returns None if no entry parses at all.

    `strict=True` enforces strict label matching (`,` or `.`
    separator required) — used when parsing body paragraphs where
    `a drilling…` shouldn't be mistaken for a label.
    """
    entries: list[tuple[str, str]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parsed = _match_legend_line(line, strict=strict)
        if parsed:
            entries.append(parsed)
            continue
        chunks = _split_multi_entry_line(line)
        if len(chunks) >= 2:
            chunk_parsed = [_match_legend_line(c, strict=strict)
                            for c in chunks]
            if all(chunk_parsed):
                entries.extend(cp for cp in chunk_parsed if cp)
                continue
        if entries:
            label, text = entries[-1]
            entries[-1] = (label, f"{text} {line.rstrip('.')}".strip())
            continue
        return None
    return entries if len(entries) >= 2 else None


def _promote_legend_verses(text: str) -> str:
    """Convert `{{IMG:…}} {{VERSE:…}VERSE}` sequences into
    `{{IMG:…}} {{LEGEND:…}LEGEND}` when the VERSE content parses as
    legend entries.  Biological-taxonomy articles (HYDROMEDUSAE,
    HEXAPODA) and engineering articles (TOOL) both use `<poem>`
    blocks for figure legends, which earlier stages convert to
    VERSE; this retroactively relabels them so the viewer renders
    them in figure-legend style."""
    def _try_convert(m: re.Match) -> str:
        img_block = m.group(1)
        verse_content = m.group(2)
        entries = _parse_legend_lines(verse_content.split("\n"))
        if not entries:
            return m.group(0)
        legend = "\n".join(f"{lbl}. {t}." for lbl, t in entries)
        return f"{img_block}\n\n{{{{LEGEND:{legend}}}LEGEND}}"

    return re.sub(
        r"(\{\{IMG:[^}]+\}\})\s*\{\{VERSE:([\s\S]*?)\}VERSE\}",
        _try_convert_verse_simple, text)


def _try_convert_verse_simple(m: re.Match) -> str:
    img_block = m.group(1)
    verse_content = m.group(2)
    entries = _parse_legend_lines(verse_content.split("\n"))
    if not entries:
        return m.group(0)
    legend = "\n".join(f"{lbl}. {t}." for lbl, t in entries)
    return f"{img_block}\n\n{{{{LEGEND:{legend}}}LEGEND}}"


def _fold_image_attribution(text: str) -> str:
    """Fold an attribution line immediately following an `{{IMG:…}}`
    marker into the IMG's caption in parens.  An attribution is a
    short line that starts with `(`, `From `, `After `, `Modified `,
    `Photo`, or `Copyright` — so regular body prose doesn't get
    eaten.  Covers the TOOL Fig. 58 `{{IMG:…}}\\n(W. & J. Player,
    Birmingham.)\\n\\n{{VERSE:…` layout."""
    attr_re = re.compile(
        r"(\{\{IMG:[^}]+\}\})\n"
        r"(\([^\n{}]{3,200}\)"
        r"|(?:From|After|Modified|Photo|Copyright)[^\n{}]{1,200})"
        r"[ \t]*"           # tolerate trailing whitespace on attr line
        r"(?=\n)",
        re.IGNORECASE,
    )
    def _apply(m: re.Match) -> str:
        img_block = m.group(1)
        attribution = m.group(2).strip()
        return _append_attr_to_img(img_block, attribution)
    return attr_re.sub(_apply, text)


_ATTRIBUTION_START_RE = re.compile(
    # Parenthetical attribution OR attribution-word immediately
    # followed by a capital-letter proper noun (or an initial).
    # Real source credits always have a name (After Haeckel, From
    # A. M. Paterson, Modified after Linko).  "After body." or
    # "After the war" would fail this check and stay as body prose.
    r"^(?:\("
    r"|(?:From|After|Modified|Photo|Copyright)"
    r"(?:\s+after)?\s+[A-Z])",
)
_FIGURE_BOUNDARY_MARKERS = (
    "{{IMG:", "\u00abSEC:", "\u00abSH", "\u00abHTMLTABLE:",
    "\x01PAGE:",
)

_BLOCK_MARKER_RE = re.compile(
    # A block-level marker that begins a fresh paragraph even when
    # preceded by just a single newline.  VERSE / TABLE / HTMLTABLE
    # are complete self-terminating units; \x01PAGE:N\x01 is a
    # page-break sentinel.  `«SEC:` / `«SH»` are heading markers.
    r"\{\{(?:VERSE|TABLE[A-Z]?|IMG|LEGEND):"
    r"|\u00abHTMLTABLE:"
    r"|\u00abSEC:"
    r"|\u00abSH\u00bb"
    r"|\x01PAGE:\d+\x01"
)

_BLOCK_END_RE = re.compile(
    r"\}VERSE\}"
    r"|\}TABLE\}"
    r"|\}LEGEND\}"
    r"|\u00ab/HTMLTABLE\u00bb"
)

def _paragraphs_starting_at(text: str, start: int):
    """Yield `(para_start, para_end, para_text)` for each paragraph
    from `start` onward.  Paragraphs are separated by blank lines OR
    by block-level markers (VERSE, TABLE, IMG, LEGEND, HTMLTABLE,
    PAGE sentinel, section headings), so a `{{VERSE:…}VERSE}\\n<body
    prose>` sequence yields the VERSE and the body prose as two
    paragraphs instead of one glued chunk.  `para_text` is the
    paragraph content with leading/trailing whitespace stripped."""
    pos = start
    ws = re.match(r"\s+", text[pos:])
    if ws:
        pos += ws.end()
    while pos < len(text):
        # Does the current position start with a self-terminating
        # block marker? If so, the paragraph is just that block.
        if text[pos:].startswith(("{{VERSE:", "{{TABLE:", "{{TABLEH:",
                                   "{{LEGEND:")):
            # Find the matching close.
            end_m = _BLOCK_END_RE.search(text, pos)
            if end_m:
                end = end_m.end()
            else:
                end = len(text)
        elif text[pos:].startswith("\u00abHTMLTABLE:"):
            end_i = text.find("\u00ab/HTMLTABLE\u00bb", pos)
            end = end_i + len("\u00ab/HTMLTABLE\u00bb") if end_i > 0 else len(text)
        elif text[pos:].startswith("{{IMG:"):
            close = text.find("}}", pos)
            end = close + 2 if close > 0 else len(text)
        elif text[pos:].startswith("\x01PAGE:"):
            close = text.find("\x01", pos + 1)
            end = close + 1 if close > 0 else len(text)
        elif text[pos:].startswith("\u00abSEC:"):
            close = text.find("\u00bb", pos)
            end = close + 1 if close > 0 else len(text)
        else:
            # Plain-text paragraph — up to next blank line OR the
            # next block-marker opening.
            blank = text.find("\n\n", pos)
            if blank < 0:
                blank = len(text)
            block = _BLOCK_MARKER_RE.search(text, pos)
            block_pos = block.start() if block and block.start() > pos else blank
            end = min(blank, block_pos)
        para = text[pos:end].strip()
        if para:
            yield pos, end, para
        pos = end
        ws = re.match(r"\s+", text[pos:])
        if ws:
            pos += ws.end()


def _is_attribution_paragraph(para: str) -> bool:
    """An attribution is a short paragraph that opens with a known
    attribution marker — `(…)`, `From …`, `After …`, `Modified …`,
    `Photo…`, `Copyright…`."""
    if len(para) > 200:
        return False
    return bool(_ATTRIBUTION_START_RE.match(para))


# A loose-laid-out figure legend in EB1911 wikitext (one not contained
# in a ``{| |}`` table or a ``<poem>`` block, which are delimited
# structurally) marks each entry's *label* in italics —
# ``''A'', Tool which would burnish only.`` (TOOL Fig. 2), surviving
# transform as a leading ``«I»A«/I»,`` (or ``«SC»``/``«B»`` for sc/bold
# labels).  A numbered *body section* — ``14. It is important to
# distinguish between two types of strain…`` (ELASTICITY) — has a
# *bare* label.  That italic-vs-bare distinction is the raw-structural
# signal that tells a legend from a body paragraph, so this path
# requires it; without it, the figure walker stops (the paragraph is
# body prose).  Entries inside a ``<poem>``/``{| |}`` are handled by
# ``_parse_verse_as_legend`` / ``_parse_table_as_legend`` and don't
# need this — the container is the delimiter there.
_LOOSE_LEGEND_LABEL_RE = re.compile(
    r"«(?:I|SC|B)»\s*"
    r"[A-Za-z0-9][A-Za-z0-9.\-]{0,3}\s*"
    r"[,.]?\s*«/(?:I|SC|B)»"
    r"[,.]?\s+\S"
)


# Bare numeric legend labels go 1–~50 (floor plans, multi-part figures);
# a larger number is a section number, not a figure-part label.
_BARE_NUM_LABEL_MAX = 99


# Heal ``fig.\nN`` line splits before splitting paragraphs into legend
# lines.  Body paragraphs in numbered articles (ELASTICITY § 14, DENSITY
# § 1, DIFFERENCES § 3, IRON AND STEEL § 85, …) frequently contain
# ``…shown in fig.\n3.…`` where wikisource pagination inserted the
# newline right between ``fig.`` and the figure number.  Without this
# heal, ``_split_para_into_legend_lines`` produces two lines that *look*
# like a numbered list (``3. …`` and ``N. …``), and the no-italic
# fallback in ``_legend_entries_from_paragraph`` accepts the body
# paragraph as a 2-entry legend.  The healed paragraph reads exactly the
# same way (``…shown in fig. 3.…``) and no longer trips the fallback.
_FIG_NEWLINE_SPLIT_RE = re.compile(
    r"\b((?:Figs?|FIGS?|figs?)\.)\s*\n\s*(?=\d)")


def _split_para_into_legend_lines(para: str) -> list[str]:
    para = _FIG_NEWLINE_SPLIT_RE.sub(r"\1 ", para)
    out: list[str] = []
    for line in para.split("\n"):
        line = line.strip()
        if not line:
            continue
        chunks = _split_multi_entry_line(line)
        if len(chunks) >= 2:
            out.extend(chunks)
        else:
            out.append(line)
    return out


def _legend_entries_from_paragraph(
    para: str,
) -> list[tuple[str, str]] | None:
    """Parse a loosely-laid-out figure legend — ``«I»LABEL«/I», text``
    entries written as plain paragraphs after an image (TOOL Figs 2-3),
    one per paragraph/line or several packed on a line.  Returns None if
    the paragraph isn't a legend.

    Two tiers, mirroring the plate-classification approach:

    * **Italic label = the reliable raw signal.**  EB1911 sets each
      loose-text legend entry's *label* in italics — ``''A'', text`` —
      surviving transform as a leading ``«I»A«/I»,`` (or ``«SC»``/``«B»``
      for sc / bold labels).  A numbered *body section* — ``14. It is
      important to distinguish between two types of strain…`` — has a
      *bare* label.  When the italic mark is present we trust it: a
      single short entry or a multi-entry list, no further questions.
    * **No italic label → last-resort heuristic.**  A *single* bare
      "entry" here is a body section / a body sentence whose first word
      ("Thus.", "viz.", "AB.", a citation initial "J.", a genus
      abbreviation "S.") got mis-read as a label — reject it.  Only a
      *list* — ≥2 entries with valid short labels (single ASCII letter,
      roman numeral, number ≤ 99, or 1–3-char code — never a 4-digit
      year) — is accepted (ROLLING-MILL ``A. Box Pass. B, Gothic
      Pass. …``, SKULL ``Fr. Frontal bone. Mx, Superior maxilla. …``).

    Note: the no-italic fallback previously also rejected legends with
    *repeated* labels as a defense against apparent-composite legends
    that the column-major layout-unwrap bug used to create (LARVAL
    FORMS Fig 5/6, FUNGI Fig 12/13, etc.).  With the disentangle fix
    in ``_try_image_layout_subclass`` the producer no longer emits
    those, so the defense is gone — letting the rare genuine repeated-
    label legends (LARVAL FORMS Fig 13's ``1. 2. 3. …`` composite,
    WILLOW's size-spec lines) come through."""
    italic = bool(_LOOSE_LEGEND_LABEL_RE.match(para))

    multi = _parse_legend_lines(_split_para_into_legend_lines(para),
                                strict=True)
    if multi is not None:                              # ≥2 parsed entries
        if not italic:
            for lbl, _ in multi:
                if lbl.isdigit() and (
                        len(lbl) >= 4 or int(lbl) > _BARE_NUM_LABEL_MAX):
                    return None                        # year / section number
        return multi

    # Fewer than two parsed entries — only credible as a legend when
    # the (single) label is italicised.
    if italic and len(para) <= 400:
        single = _match_legend_line(para, strict=True)
        if single:
            return [single]
    return None


_LEGEND_LABEL_ALONE_RE = re.compile(
    r"^\s*(\w[\w.\- ]{0,12}?)\s*[,.]\s*$")

def _parse_table_as_legend(
    table_content: str,
) -> list[tuple[str, str]] | None:
    """Try to parse a `{{TABLE:…}TABLE}` body as a 2+-column legend
    grid.  Returns entries or None.

    Two layouts are recognised:
      1. `label, text | label, text` — each cell holds one entry.
      2. `label, | text | spacer? | label, | text` — labels and
         text live in alternating cells, separated by empty or
         whitespace-only spacer cells (TUNICATA Fig. 24)."""
    rows = [r for r in table_content.strip().split("\n") if r.strip()]
    if not rows:
        return None

    def _strip_italic(s: str) -> str:
        return re.sub(r"\u00ab/?[A-Z]+\u00bb", "", s).strip()

    # Layout 1: each cell is `label, text`.  Entries may span multiple
    # rows in the same column — a cell that doesn't start with a label
    # is a continuation of the previous entry in its column.  Entries
    # are collected per-column then concatenated column-major so the
    # final reading order matches the print layout (top-to-bottom of
    # column 1, then column 2, …) — ARACHNIDA Fig 14 is the canonical
    # case.  Pure single-row legends (WEAVING Fig 26) are a degenerate
    # case where no continuations exist.
    n_cols = len(_table_row_cells(rows[0])) if rows else 0
    if n_cols >= 2:
        columns: list[list[tuple[str, str]]] = [[] for _ in range(n_cols)]
        layout1_ok = True
        for row in rows:
            cells = _table_row_cells(row)
            # Allow a short trailing row (final blank cell stripped by
            # the table closer): pad to n_cols with empty cells.
            if len(cells) < n_cols:
                cells = cells + [""] * (n_cols - len(cells))
            elif len(cells) > n_cols:
                layout1_ok = False
                break
            for c_idx, cell in enumerate(cells):
                stripped = cell.strip()
                if not stripped:
                    continue
                clean = _strip_italic(cell)
                # A trailing `|` is the closer of a row that ended `| `
                # in source — the trailing space gets stripped earlier
                # so `_table_row_cells` doesn't split the empty cell
                # off, and the pipe rides into col-0 cell text.  Drop
                # it before parsing.
                clean = re.sub(r"\s*\|\s*$", "", clean).strip()
                cm = _LEGEND_CELL_RE.match(clean)
                if cm:
                    label = cm.group(1).strip().rstrip(".,")
                    txt = cm.group(2).strip().rstrip(".")
                    if label and txt:
                        columns[c_idx].append((label, txt))
                else:
                    # Continuation row — append to the previous entry
                    # in the same column.  No prior entry means this
                    # column starts with a non-label cell, which isn't
                    # the legend shape we're looking for.
                    if not columns[c_idx]:
                        layout1_ok = False
                        break
                    prev_lbl, prev_txt = columns[c_idx][-1]
                    cont = clean.rstrip(".").strip()
                    columns[c_idx][-1] = (
                        prev_lbl,
                        f"{prev_txt} {cont}".strip(),
                    )
            if not layout1_ok:
                break
        if layout1_ok:
            entries = [e for col in columns for e in col]
            if len(entries) >= 2:
                return entries

    # Layout 2: alternating label-cell + text-cell, possibly
    # separated by empty/whitespace-only spacer cells (em-/en-spaces).
    entries: list[tuple[str, str]] = []
    for row in rows:
        cells = _table_row_cells(row)
        meaningful = []
        for c in cells:
            stripped = _strip_italic(c)
            # Treat em-space (\u2003), en-space (\u2002), nbsp
            # (\u00a0) and regular whitespace as spacer-only.
            collapsed = re.sub(
                r"[\s\u2002\u2003\u00a0]+", "", stripped)
            if collapsed:
                meaningful.append(c)
        if len(meaningful) < 2 or len(meaningful) % 2 != 0:
            return None
        for i in range(0, len(meaningful), 2):
            label_clean = _strip_italic(meaningful[i])
            text_clean = _strip_italic(meaningful[i + 1])
            lm = _LEGEND_LABEL_ALONE_RE.match(label_clean)
            if not lm:
                return None
            label = lm.group(1).strip().rstrip(".,")
            txt = text_clean.strip().rstrip(".")
            if not label or not txt:
                return None
            entries.append((label, txt))
    return entries if len(entries) >= 2 else None


def _parse_verse_as_legend(
    verse_content: str,
) -> list[tuple[str, str]] | None:
    """Try to parse a `{{VERSE:…}VERSE}` body as legend lines."""
    return _parse_legend_lines(verse_content.split("\n"))


def _classify_figure_paragraph(
    para: str,
) -> tuple[str, object]:
    """Classify one paragraph of post-IMG content.  Returns a tuple:

        ("boundary",   None)             — stop here, don't consume
        ("attribution", attribution_text) — append to caption
        ("legend",     [(label, text)…])  — emit as LEGEND entries
        ("skip",       None)             — empty / continuation

    Also returns `"boundary"` for block markers that don't belong to
    the figure (next IMG, section heading, HTMLTABLE, …).
    """
    if not para:
        return "skip", None

    # Boundary markers
    for marker in _FIGURE_BOUNDARY_MARKERS:
        if para.startswith(marker):
            return "boundary", None

    # Pre-existing LEGEND block — the layout-unwrap subclass already
    # promoted the legend for this figure (MULTICOL_LEGEND case in
    # `elements/_layout.py`).  Emit "preserve" so the walker keeps
    # scanning forward (to fold a trailing attribution into the IMG
    # caption — e.g. ARACHNIDA Fig 65's "(Original drawing by …)")
    # AND keeps the existing LEGEND verbatim in the output.  Without
    # this the walker either stops at the LEGEND (no attribution
    # fold) or eats it as a "skip" (LEGEND lost from output).
    if re.match(r"\{\{LEGEND:[\s\S]*\}LEGEND\}\s*$", para):
        return "preserve", para

    # VERSE block: legend-shaped?
    verse_m = re.match(r"\{\{VERSE:([\s\S]*)\}VERSE\}\s*$", para)
    if verse_m:
        entries = _parse_verse_as_legend(verse_m.group(1))
        if entries:
            return "legend", entries
        return "boundary", None  # unrelated verse → stop

    # TABLE block: legend-shaped?
    table_m = re.match(r"\{\{TABLE[A-Z]?:([\s\S]*)\}TABLE\}\s*$", para)
    if table_m:
        entries = _parse_table_as_legend(table_m.group(1))
        if entries:
            return "legend", entries
        return "boundary", None

    # Attribution line
    if _is_attribution_paragraph(para):
        return "attribution", para.strip(" .")

    # Legend-shape paragraph
    entries = _legend_entries_from_paragraph(para)
    if entries:
        # Reject caption-repeat paragraphs. A lone ``Fig. 21.`` after
        # an IMG parses as legend entry ("Fig", "21") — but real legend
        # labels are short symbols (A, B, i, ii, α), never the word
        # "Fig". This pattern appears in source wikitext that writes
        # the caption both in the File link and as a separate
        # ``{{csc|Fig. N.}}`` line (SHIPBUILDING Figs 21–22).
        if len(entries) == 1:
            lbl, txt = entries[0]
            if lbl.lower() == "fig" and re.fullmatch(r"\d+", txt.strip()):
                return "skip", None
        return "legend", entries

    # Anything else is body prose — figure boundary.
    return "boundary", None


def _try_convert_with_attr(m: re.Match) -> str:
    """Convert IMG + optional attribution line + VERSE into IMG +
    LEGEND, folding the attribution into the IMG caption.  Shared
    helper so the same logic applies to TABLE and paragraph
    promoters."""
    img_block = m.group(1)
    attribution = (m.group(2) or "").strip(" .")
    verse_content = m.group(3)
    entries = _parse_legend_lines(verse_content.split("\n"))
    if not entries:
        return m.group(0)
    # Append attribution to caption if present.
    if attribution:
        img_block = _append_attr_to_img(img_block, attribution)
    legend = "\n".join(f"{lbl}. {t}." for lbl, t in entries)
    return f"{img_block}\n\n{{{{LEGEND:{legend}}}LEGEND}}"


def _append_attr_to_img(img_block: str, attribution: str) -> str:
    """Append attribution text to an IMG marker's caption in parens."""
    m = IMG_PARTS_RE.match(img_block)
    if not m:
        return img_block
    filename = m.group(1)
    meta_block = m.group(2)  # "|align=…|width=…" or "" — carried through
    caption = m.group(3) or ""
    # `attribution` is captured straight off body text that may not have
    # been through the body-text transform — clean it the same way every
    # caption is (templates, entities, cell-attrs, stray pipes/braces).
    attribution = clean_caption(attribution)
    if not attribution or attribution in caption:
        return img_block
    if attribution.startswith("(") and attribution.endswith(")"):
        new_caption = (f"{caption.rstrip()} {attribution}"
                       if caption else attribution)
    else:
        new_caption = (f"{caption.rstrip()} ({attribution}.)"
                       if caption else f"({attribution}.)")
    return f"{{{{IMG:{filename}{meta_block}|{new_caption}}}}}"


def _promote_legend_tables(text: str) -> str:
    """Convert `{{IMG:…}} {{TABLE:…}TABLE}` sequences into
    `{{IMG:…}} {{LEGEND:…}LEGEND}` when the table is a 2+-column
    grid of `label, text` pairs (WEAVING Fig. 26)."""
    def _try_convert(m: re.Match) -> str:
        img_block = m.group(1)
        table_content = m.group(2)
        rows_text = [r for r in table_content.strip().split("\n")
                     if r.strip()]
        if not rows_text:
            return m.group(0)
        entries: list[tuple[str, str]] = []
        for row in rows_text:
            cells = _table_row_cells(row)
            if len(cells) < 2:
                return m.group(0)
            for cell in cells:
                # Strip italic markers before parsing so `«I»a«/I», x`
                # matches the label regex.
                clean = re.sub(
                    r"\u00ab/?[A-Z]+\u00bb", "", cell).strip()
                cm = _LEGEND_CELL_RE.match(clean)
                if not cm:
                    return m.group(0)
                label = cm.group(1).strip().rstrip(".,")
                txt = cm.group(2).strip().rstrip(".")
                if label and txt:
                    entries.append((label, txt))
        if len(entries) < 2:
            return m.group(0)
        legend = "\n".join(f"{lbl}. {t}." for lbl, t in entries)
        return f"{img_block}\n\n{{{{LEGEND:{legend}}}LEGEND}}"

    return re.sub(
        r"(\{\{IMG:[^}]+\}\})\s*\{\{TABLE:([\s\S]*?)\}TABLE\}",
        _try_convert, text)



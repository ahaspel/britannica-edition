"""Extract, process, and reassemble embedded elements in wikitext.

Embedded elements (tables, images, footnotes, poems, math, scores)
are extracted from the raw wikitext into a registry, the remaining
text is transformed (bold, italic, links, etc.), then each element
is processed recursively and reassembled into the final text.

The key rule: extract outermost first, process innermost first.
Each element processor calls the same extract-process-reassemble
on its own content, so nesting (e.g. footnotes inside tables)
is handled naturally by recursion.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


# Placeholder uses \x03 (ETX) which is stripped by clean_pages anyway,
# so any leaked placeholders won't survive to export.
_PH = "\x03"


@dataclass
class ElementRegistry:
    """Stores extracted elements keyed by placeholder strings.

    Uses a module-level counter so keys are unique across every
    registry instance in a processing run.  Per-instance counters
    caused silent collisions: an inner registry's ``ELEM:1``
    matched the outer registry's ``ELEM:1``, so if a stale inner
    placeholder escaped unreplaced (e.g. ``<ref>`` inside ``<poem>``
    inside a table), the outer substitution pass would substitute
    the outer ``ELEM:1``'s processed content into the inner's
    location — duplicating content across the article.
    """
    elements: dict[str, tuple[str, str]] = field(default_factory=dict)

    def add(self, element_type: str, raw: str) -> str:
        """Add an element to the registry, return its placeholder."""
        counter = _next_placeholder_id()
        key = f"{_PH}ELEM:{counter}{_PH}"
        self.elements[key] = (element_type, raw)
        return key


_placeholder_counter = 0


def _next_placeholder_id() -> int:
    global _placeholder_counter
    _placeholder_counter += 1
    return _placeholder_counter


# ── Extraction ─────────────────────────────────────��──────────────────

# Extraction order: outermost first.
# Tables can contain all other elements.
# Poems can contain footnotes.
# Images can (rarely) contain footnotes in captions.
# Footnotes, math, and scores are leaf-level or near-leaf.

_EXTRACTORS = [
    # Extraction order: outermost first.
    # HTML elements first (they can contain wiki markup elements).
    # Wiki tables handled separately with balanced matching.
    ("REF_SELF", re.compile(r"<ref\s[^>]*/\s*>", re.IGNORECASE), 0),
    ("REF", re.compile(r"<ref(?:\s[^>]*)?>.*?</ref>", re.DOTALL | re.IGNORECASE), 0),
    ("HTML_TABLE", re.compile(r"<table\b[^>]*>.*?</table>", re.DOTALL | re.IGNORECASE), 0),
    ("POEM", re.compile(r"<poem>.*?</poem>", re.DOTALL | re.IGNORECASE), 0),
    ("MATH", re.compile(r"<math[^>]*>.*?</math>", re.DOTALL | re.IGNORECASE), 0),
    ("SCORE", re.compile(r"<score[^>]*>.*?</score>", re.DOTALL), 0),
    # Wiki markup elements
    # 4 levels of brace nesting — CASTLE Fig. 9 `cap={{Fs85|…}}
    # {{center|{{EB1911 Fine Print|{{sc|Fig.}} 9.…}}}}` is 4 deep.
    ("IMAGE_FLOAT", re.compile(
        r"\{\{(?:img float|figure|FI)\s*\|"
        r"(?:[^{}]|\{\{(?:[^{}]|\{\{(?:[^{}]|\{\{[^{}]*\}\})*\}\})*\}\})*"
        r"\}\}",
        re.DOTALL | re.IGNORECASE), 0),
    ("IMAGE", re.compile(
        r"\[\[(?:File|Image):([^\]]+)\]\]"
        # Optional caption block on the following line(s).  Allow up
        # to 2 lines so attribution-line + Fig.-caption-line blocks
        # stay together (WEAVING Fig. 29 `<small>From Roth's…</small>
        # <br/>\n{{center|{{sc|Fig}} 29—Loom from Sarawak.}}`).  Each
        # line must start with a recognized caption-or-attribution
        # marker, optionally preceded by an HTML tag (`<small>`) or
        # wrapper template (`{{sm|…}}`).
        r"(?:\s*\n\n?("
        r"(?:<[a-z]+[^>\n]*>\s*)?"
        r"(?:\{\{sm\||\{\{center\||\{\{(?:sc|Fine)\|Fig[.}]"
        r"|Fig[. ]\d|Plate\s"
        r"|(?:From|After|Photo|Copyright|Modified)\s"
        r"|\d+\.\s*[A-Z])"
        r"[^\n]*"
        r"(?:\n(?:<[a-z]+[^>\n]*>\s*)?"
        r"(?:\{\{center\||\{\{(?:sc|Fine)\|Fig[.}]|Fig[. ]\d)"
        r"[^\n]*)?"
        r"))?",
        re.IGNORECASE), 0),
    ("HIEROGLYPH", re.compile(
        r"\{\{hieroglyph\|([^{}]*)\}\}", re.IGNORECASE), 0),
    ("HIEROGLYPH", re.compile(
        r"<hiero>([^<]*)</hiero>", re.IGNORECASE), 0),
]


def _is_compound_table(table_text: str) -> bool:
    """Detect data tables with nested sub-tables in cells.

    These are outermost tables with data signals (border/rules/class) that
    contain nested {|...|} blocks.  They need dedicated processing to zip
    parallel sub-table rows together.
    """
    header = table_text.split("\n", 1)[0]
    has_data = bool(
        re.search(r'border\s*=\s*"?[1-9]', header, re.IGNORECASE) or
        re.search(r'rules\s*=', header, re.IGNORECASE) or
        re.search(r'class\s*=\s*"[^"]*(?:wikitable|tablecolhd|border)',
                   header, re.IGNORECASE))
    if not has_data:
        return False
    # Check for nested table (depth > 1)
    depth = 0
    for m in re.finditer(r"\{\||\|\}", table_text):
        if m.group() == "{|":
            depth += 1
            if depth > 1:
                return True
        else:
            depth -= 1
    return False


def _extract_balanced_tables(text: str, registry: ElementRegistry) -> str:
    """Extract wiki tables using balanced {| |} matching.

    Handles nested tables correctly by finding outermost {| first.
    Tables containing {{Css image crop}} are registered as DJVU_CROP
    so they get image processing instead of table processing.
    """
    while True:
        # Find the first {| that isn't already inside a placeholder
        idx = text.find("{|")
        if idx < 0:
            break

        # Find the balanced |} by tracking depth. Skip over
        # ``{{…}}`` template blocks entirely — e.g. ``{{Ts|vmi|}}``
        # contains ``|}}`` which would otherwise be read as a table
        # closer, truncating the table mid-row (ATMOSPHERIC
        # ELECTRICITY Table IV).
        #
        # Also accept ``</table>`` as an alternative closer.  A handful
        # of Wikisource pages mix syntaxes — open with ``{|`` but close
        # with ``</table>`` (POST, vol22 ws 208).  MediaWiki tolerates
        # this; we have to too, otherwise the table leaks as raw
        # wikitable markup.
        depth = 0
        i = idx
        found = False
        while i < len(text) - 1:
            if text[i:i+2] == "{{":
                # Skip to matching }} (nested-brace aware)
                tdepth = 1
                j = i + 2
                while j < len(text) - 1 and tdepth > 0:
                    if text[j:j+2] == "{{":
                        tdepth += 1
                        j += 2
                    elif text[j:j+2] == "}}":
                        tdepth -= 1
                        j += 2
                    else:
                        j += 1
                i = j
                continue
            if text[i:i+2] == "{|":
                depth += 1
                i += 2
            elif text[i:i+2] == "|}" or (
                text[i:i+8].lower() == "</table>" and depth > 0
            ):
                depth -= 1
                # Compute length of the closer we matched.
                closer_len = 2 if text[i:i+2] == "|}" else 8
                if depth == 0:
                    # Found the balanced close
                    table_text = text[idx:i + closer_len]
                    # Classify at extraction time
                    if re.search(r"\{\{Css image crop", table_text, re.IGNORECASE):
                        etype = "DJVU_CROP"
                    elif _is_compound_table(table_text):
                        etype = "COMPOUND_TABLE"
                    else:
                        etype = "TABLE"
                    placeholder = registry.add(etype, table_text)
                    text = text[:idx] + placeholder + text[i + closer_len:]
                    found = True
                    break
                i += closer_len
            else:
                i += 1

        if not found:
            break  # Unbalanced — stop

    return text


_CHART2_RE = re.compile(
    r"(?:\{\{missing table\}\}\s*(?:\x01PAGE:\d+\x01)?\s*)?"  # consume missing-table + page marker
    r"(?:\{\{center\|[^}]*\}\}\s*)?"  # consume preceding centered title
    r"(?:\{\{EB1911 fine print/s\}\}\s*)?"  # consume fine-print wrapper start
    r"\{\{chart2/start[^}]*\}\}.*?\{\{chart2/end\}\}"
    r"(?:\s*<poem>.*?</poem>)?"  # consume garbled OCR text after chart
    r"(?:\s*\{\{EB1911 fine print/e\}\})?",  # consume fine-print wrapper end
    re.DOTALL | re.IGNORECASE,
)


def extract(text: str) -> tuple[str, ElementRegistry]:
    """Extract all embedded elements from text, outermost first.

    Returns the text with placeholders and a registry of extracted elements.
    """
    registry = ElementRegistry()

    # Chart2 genealogical trees — extract before tables
    text = _CHART2_RE.sub(
        lambda m: registry.add("CHART2", m.group(0)), text)

    # Wiki tables first (outermost) — balanced matching handles nesting
    text = _extract_balanced_tables(text, registry)

    # Then all other elements (refs, images, poems, math, etc.)
    for element_type, pattern, _flags in _EXTRACTORS:
        text = pattern.sub(
            lambda m, et=element_type: registry.add(et, m.group(0)),
            text,
        )

    return text, registry


# ── Processing ────────────────────────────────────────────────────────

def _strip_delimiters(element_type: str, raw: str) -> str:
    """Strip the outer delimiters of an element, returning inner content."""
    if element_type == "TABLE":
        # {| ... |}
        s = re.sub(r"^\{\|[^\n]*\n?", "", raw)
        s = re.sub(r"\n?\|\}\s*$", "", s)
        return s
    elif element_type == "REF_SELF":
        return ""
    elif element_type == "REF":
        return re.sub(r"<ref(?:\s[^>]*)?>|</ref>", "", raw, flags=re.IGNORECASE).strip()
    elif element_type == "POEM":
        return re.sub(r"</?poem>", "", raw, flags=re.IGNORECASE).strip()
    elif element_type == "MATH":
        return re.sub(r"<math[^>]*>|</math>", "", raw, flags=re.IGNORECASE).strip()
    elif element_type == "SCORE":
        return re.sub(r"<score[^>]*>|</score>", "", raw, flags=re.IGNORECASE).strip()
    elif element_type == "IMAGE":
        m = re.match(r"\[\[(?:File|Image):(.+)\]\](?:\s*\n\n?(.+))?$", raw,
                      re.IGNORECASE | re.DOTALL)
        if m:
            inner = m.group(1)
            ext_caption = m.group(2)
            if ext_caption:
                inner = inner + "|EXTCAP:" + ext_caption
            return inner
        return raw
    elif element_type == "HTML_TABLE":
        s = re.sub(r"^<table\b[^>]*>", "", raw, flags=re.IGNORECASE)
        s = re.sub(r"</table>\s*$", "", s, flags=re.IGNORECASE)
        return s
    elif element_type == "HIEROGLYPH":
        s = re.sub(r"^\{\{hieroglyph\||\}\}$", "", raw, flags=re.IGNORECASE)
        s = re.sub(r"^<hiero>|</hiero>$", "", s, flags=re.IGNORECASE)
        return s
    elif element_type == "IMAGE_FLOAT":
        # Strip outer {{ and }}
        s = re.sub(r"^\{\{", "", raw)
        s = re.sub(r"\}\}$", "", s)
        return s
    return raw


def _process_element(element_type: str, raw: str,
                     text_transform, context: dict) -> str:
    """Process a single element recursively.

    Args:
        element_type: TABLE, IMAGE, REF, POEM, MATH, SCORE, IMAGE_FLOAT
        raw: the raw wikitext of the element
        text_transform: function to transform plain wikitext (bold, italic, etc.)
        context: dict with 'volume' and 'page_number' for score lookups
    """
    # DJVU_CROP, CHART2, SCORE, and COMPOUND_TABLE are self-contained —
    # process from raw, no recursive child extraction.
    if element_type == "DJVU_CROP":
        return _process_djvu_crop(raw, text_transform, context)
    if element_type == "CHART2":
        return _process_chart2(raw, context)
    if element_type == "SCORE":
        return _process_score(raw, context)
    if element_type == "COMPOUND_TABLE":
        return _process_compound_table(raw, text_transform)

    # Strip outer delimiters to get the element's inner content,
    # then recursively extract and process any child elements.
    inner = _strip_delimiters(element_type, raw)
    inner, inner_registry = extract(inner)

    # Process children but DON'T reinsert yet — keep placeholders
    # so the parent processor sees opaque markers, not expanded content.
    processed_children = {}
    for key, (child_type, child_raw) in inner_registry.elements.items():
        processed_children[key] = _process_element(
            child_type, child_raw, text_transform, context)

    # Process this element with placeholders still in place
    if element_type == "MATH":
        result = _process_math(inner)
    elif element_type == "REF_SELF":
        result = ""  # Self-closing ref (back-reference) — strip it
    elif element_type == "REF":
        result = _process_ref(inner, text_transform)
    elif element_type == "IMAGE":
        result = _process_image(inner, text_transform)
    elif element_type == "IMAGE_FLOAT":
        result = _process_image_float(inner, text_transform)
    elif element_type == "POEM":
        result = _process_poem(inner, text_transform)
    elif element_type == "HIEROGLYPH":
        result = f"[hieroglyph: {inner}]"
    elif element_type == "TABLE":
        table_kind = _classify_table(raw, inner, inner_registry)
        if table_kind == "MATH_LAYOUT":
            result = _process_math_layout_table(raw)
        elif table_kind == "EQUATION_LAYOUT":
            result = _process_equation_layout(inner, text_transform)
        elif table_kind == "LAYOUT_WRAPPER":
            result = _unwrap_layout_table(inner, text_transform, inner_registry)
        elif table_kind == "COMPLEX_HTML":
            result = _process_complex_table(inner, text_transform)
        else:
            result = _process_table(inner, text_transform, inner_registry)
    elif element_type == "HTML_TABLE":
        result = _process_html_table(raw, inner, text_transform, inner_registry)
    else:
        result = inner

    # Reinsert processed children.  A single pass isn't enough: a
    # processed child may itself contain placeholders for siblings
    # (e.g. ``<poem>`` with a ``<ref>`` inside — the poem processor
    # carries the REF placeholder through opaque, because its inner
    # ``extract()`` can't see past the ``\x03`` wrapper).  If we only
    # substitute in registry order, such a re-introduced placeholder
    # rides out into the parent's result and leaks.  Iterate until
    # the result stops changing.
    for _pass in range(5):
        changed = False
        for key, processed_child in processed_children.items():
            if key in result:
                result = result.replace(key, processed_child)
                changed = True
        if not changed:
            break

    return result


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
    text = re.sub(r"\u00abLN:[^|]*\|([^\u00ab]*)\u00ab/LN\u00bb", r"\1", text)
    # Strip converted markers (post-fetch-stage)
    text = re.sub(r"\u00abB\u00bb(.*?)\u00ab/B\u00bb", r"\1", text)
    text = re.sub(r"\u00abI\u00bb(.*?)\u00ab/I\u00bb", r"\1", text)
    text = re.sub(r"\u00abSC\u00bb(.*?)\u00ab/SC\u00bb", r"\1", text)
    text = re.sub(r"\u00ab/?[A-Z]+\u00bb", "", text)
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


def _process_score(raw: str, context: dict) -> str:
    """Replace <score> tag with pre-rendered Wikimedia image URL."""
    from britannica.pipeline.stages.clean_pages import _SCORE_IMAGES, _SCORE_TAG

    vol = context.get("volume")
    page = context.get("page_number")
    if vol is not None and page is not None:
        # Try to match by content against the static map
        matches = list(_SCORE_TAG.finditer(raw))
        if matches:
            for (v, p, idx), url in _SCORE_IMAGES.items():
                if v == vol and p == page:
                    return f"{{{{IMG:{url}|Musical notation}}}}"
    return "[Musical notation]"


def _process_math(inner: str) -> str:
    """Convert math content to «MATH:...«/MATH» marker, preserving LaTeX."""
    import html as html_mod
    inner = html_mod.unescape(inner.strip())
    # Collapse blank lines — they break LaTeX math environments
    inner = re.sub(r"\n{2,}", "\n", inner)
    return f"\u00abMATH:{inner}\u00ab/MATH\u00bb"


def _classify_table(raw: str, inner: str, inner_registry: ElementRegistry | None) -> str:
    """Classify a wiki table into its processing type.

    Returns one of:
        EQUATION_LAYOUT — math alignment (mostly MATH placeholders or spacer-heavy)
        LAYOUT_WRAPPER  — image+caption wrapper or nested table wrapper
        COMPLEX_HTML    — tables with rowspan that need HTML passthrough
        DATA_TABLE      — regular data tables (default)
    """
    # Complex HTML: tables with rowspan/colspan need full HTML rendering.
    # Check this BEFORE equation layout — rowspan is a strong signal of a
    # real data table, and {{ts}} stripping can create phantom empty cells
    # that fool the equation layout heuristic.
    has_rowspan = bool(re.search(r"rowspan\s*=", raw, re.IGNORECASE))
    has_colspan = bool(re.search(r"colspan\s*=", raw, re.IGNORECASE))
    # Layout wrappers first — image+caption tables often use colspan for centering
    if _is_layout_wrapper(raw, inner, inner_registry):
        return "LAYOUT_WRAPPER"
    # Complex HTML: tables with rowspan or colspan need full HTML rendering.
    # Check BEFORE equation layout — rowspan is a strong signal of a
    # real data table, and {{ts}} stripping can create phantom empty cells
    # that fool the equation layout heuristic.
    if has_rowspan or has_colspan:
        # Exception: brace tables (poem + translation) handle rowspan
        # themselves. Match `{{brace}}` or `{{brace|...}}` specifically —
        # NOT `{{brace2|...}}` (decorative bracket, not a poem layout).
        if re.search(r"\{\{brace(?:\s*\||\s*\})", raw, re.IGNORECASE):
            return "DATA_TABLE"
        return "COMPLEX_HTML"
    # Tables with data signals (border/rules/class) AND {{Ts}} templates
    # need COMPLEX_HTML processing — the template markup creates extra
    # pipes and empty cells that break _process_table's simple cell parsing.
    # {{Ts}} alone is not enough (it's also used for layout table styling).
    # Class value may be quoted or unquoted: class="wikitable" or class=_foo.
    header = raw.split("\n", 1)[0]
    has_data_signal = (
        re.search(r'border\s*=\s*"?[1-9]', header, re.IGNORECASE) or
        re.search(r'rules\s*=', header, re.IGNORECASE) or
        re.search(r'class\s*=\s*"?[^"\s]*(?:wikitable|tablecolhd|border)',
                   header, re.IGNORECASE))
    if has_data_signal and re.search(r'\{\{[Tt]s\|', raw):
        return "COMPLEX_HTML"
    if _is_math_layout(raw, inner):
        return "MATH_LAYOUT"
    if _is_equation_layout(inner, inner_registry):
        return "EQUATION_LAYOUT"
    return "DATA_TABLE"


_MATH_CELL_RE = re.compile(
    r"^(?:"
    r"''[A-Za-z]''"
    r"|<su[pb]>[^<]{1,8}</su[pb]>"
    r"|\{\{Greek\|[^}]{1,8}\}\}"
    r"|\{\{sfrac\|[^}]{1,20}\}\}"
    r"|\{\{[A-Za-z]+\s*\|[^}]{1,30}\}\}"
    r"|[0-9]+"
    r"|[+\-=\uFF1D\u00D7\u00B7()/., \u2212\u00F7\u2260\u2264\u2265\u2261\u2192]"
    r"|&nbsp;|&minus;|&emsp;|&ensp;|&thinsp;"
    r"|<br\s*/?>"
    r")+$",
    re.IGNORECASE,
)


def _parse_math_layout_cells(inner: str) -> list[str] | None:
    """Return list of cell content strings for a candidate math-layout
    table, or None if the table has a header (``!`` sigil) row."""
    cells: list[str] = []
    for line in inner.split("\n"):
        s = line.strip()
        if not s or s.startswith("|+") or s == "|}" or s.startswith("|-"):
            continue
        if s.startswith("!"):
            return None  # header row disqualifies
        if not s.startswith("|"):
            continue
        body = s[1:]
        body = re.sub(r"\{\{[^}]*\}\}",
                      lambda m: m.group(0).replace("|", "\x04"), body)
        for chunk in body.split("||"):
            if "|" in chunk:
                _, _, content = chunk.rpartition("|")
            else:
                content = chunk
            content = content.replace("\x04", "|").strip()
            content = re.sub(r"<span\s[^>]*>|</span>", "", content)
            if content:
                cells.append(content)
    return cells


def _is_math_layout(raw: str, inner: str) -> bool:
    """Detect tables that hold math content as positional layout
    (equation systems, determinants, matrices) rather than prose data.

    Seen on ALGEBRAIC FORMS (vol 1 p624+): transcribers used
    ``{|{{ts|…}}|}`` wikitables to align successive terms of an
    equation system or the cells of a determinant.  Rendering such
    tables as HTML data-tables gives a wholly wrong visual result —
    they should go through KaTeX as ``\\begin{aligned}`` /
    ``\\begin{vmatrix}`` blocks instead.

    Requires:
      * No ``class=wikitable``/``border=N``/``rules=`` data signal.
      * No ``<ref>`` footnotes (those don't appear in math layouts).
      * No header row (no ``!`` sigil cell).
      * Every cell matches the narrow math-token regex.
      * ≥ 2 cells with a strong math signature (``<su[pb]>`` tag, or
        an arithmetic operator joining operands).
    """
    header = raw.split("\n", 1)[0]
    if re.search(r'class\s*=\s*"?[^"\s]*(?:wikitable|tablecolhd)',
                 header, re.IGNORECASE):
        return False
    if re.search(r'border\s*=\s*"?[1-9]|rules\s*=',
                 header, re.IGNORECASE):
        return False
    if re.search(r"<ref[\s>]", raw, re.IGNORECASE):
        return False
    cells = _parse_math_layout_cells(inner)
    if cells is None or len(cells) < 2:
        return False
    if any(len(c) > 250 for c in cells):
        return False
    if not all(_MATH_CELL_RE.match(c) for c in cells):
        return False
    strong = 0
    for c in cells:
        if re.search(r"<su[pb]>", c):
            strong += 1
        elif re.search(
                r"[+\-\u2212=\uFF1D\u00D7\u00F7]\s*(?:''|[0-9(])", c):
            strong += 1
    return strong >= 2


def _math_cell_to_latex(content: str) -> str:
    """Convert a wikitext math cell to LaTeX token sequence."""
    # Strip {{ts|…}} styling leftovers
    content = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*\|?\s*", "", content)
    # Italic letter run: ''xyz'' → xyz
    content = re.sub(r"''([A-Za-z]+)''", r"\1", content)
    # Sub/sup
    content = re.sub(r"<sub>([^<]+)</sub>", r"_{\1}",
                     content, flags=re.IGNORECASE)
    content = re.sub(r"<sup>([^<]+)</sup>", r"^{\1}",
                     content, flags=re.IGNORECASE)
    # Greek template: keep the character (KaTeX renders Unicode Greek)
    content = re.sub(r"\{\{Greek\|([^}]+)\}\}", r"\1",
                     content, flags=re.IGNORECASE)
    content = content.replace("\uFF1D", "=")   # fullwidth =
    content = content.replace("\u2212", "-")   # unicode minus
    content = content.replace("\u00D7", r"\times ")
    content = content.replace("\u00B7", r"\cdot ")
    content = re.sub(r"<span[^>]*>|</span>", "", content)
    content = re.sub(r"&nbsp;|&emsp;|&ensp;|&thinsp;", " ", content)
    content = re.sub(r"\s+", " ", content).strip()
    return content


def _process_math_layout_table(raw: str) -> str:
    """Emit a math-layout wikitable as a KaTeX math block.

    Equation system (rows share ``=`` column): ``\\begin{aligned}…\\end{aligned}``.
    Otherwise (matrix/determinant): ``\\begin{vmatrix}…\\end{vmatrix}``.
    """
    inner = re.sub(r"^\{\|[^\n]*\n?", "", raw)
    inner = re.sub(r"\n?\|\}\s*$", "", inner)
    raw_rows = re.split(r"^\|-[^\n]*$", inner, flags=re.MULTILINE)
    rows: list[list[str]] = []
    for raw_row in raw_rows:
        row_cells: list[str] = []
        for line in raw_row.split("\n"):
            s = line.strip()
            if not s or s.startswith("|+") or s == "|}":
                continue
            if not s.startswith("|"):
                continue
            body = s[1:]
            body = re.sub(r"\{\{[^}]*\}\}",
                          lambda m: m.group(0).replace("|", "\x04"), body)
            for chunk in body.split("||"):
                if "|" in chunk:
                    _, _, content = chunk.rpartition("|")
                else:
                    content = chunk
                content = content.replace("\x04", "|").strip()
                if content:
                    row_cells.append(_math_cell_to_latex(content))
        if row_cells:
            rows.append(row_cells)
    if not rows:
        return ""
    is_eqn = any("=" in "".join(row) for row in rows)
    if is_eqn:
        lines = []
        for row in rows:
            line = " ".join(row).strip()
            # Align on first = → &=
            line = re.sub(r"^(.*?)=(.*)$", r"\1 &= \2", line, count=1)
            lines.append(line)
        latex = ("\\begin{aligned}\n" + " \\\\\n".join(lines)
                 + "\n\\end{aligned}")
    else:
        lines = [" & ".join(row) for row in rows]
        latex = ("\\begin{vmatrix}\n" + " \\\\\n".join(lines)
                 + "\n\\end{vmatrix}")
    return f"\u00abMATH:{latex}\u00ab/MATH\u00bb"


def _is_equation_layout(inner: str, inner_registry: ElementRegistry | None) -> bool:
    """Detect wiki tables used for equation alignment, not data display.

    Two signatures:
      1. Mostly MATH placeholders (from <math> tags in cells)
      2. Mostly empty spacer cells without cell-level align attributes
    """
    # Check 1: majority MATH placeholders
    if _PH in inner and inner_registry:
        math_ct = sum(1 for _, (t, _) in inner_registry.elements.items() if t == "MATH")
        if math_ct >= 2 and math_ct >= len(inner_registry.elements) * 0.5:
            return True
    # Check 2: spacer-heavy alignment (>50% empty cells).
    # Data tables use cell-level align/valign attributes; equation layout never does.
    if re.search(r'\balign\s*=', inner, re.IGNORECASE):
        return False
    # Need _extract_cells logic inline — lightweight version for detection only
    raw_rows = re.split(r"\|-[^\n]*", inner)
    total_cells = 0
    empty_cells = 0
    for raw_row in raw_rows:
        # Simple cell split (no text_transform needed for counting)
        protected = re.sub(r"\{\{[^}]*\}\}", lambda m: m.group(0).replace("|", "\x04"), raw_row)
        protected = re.sub(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH),
                           lambda m: m.group(0).replace("|", "\x04"), protected)
        raw_cells = re.findall(r"\|([^|\n]*)", protected)
        _ATTR = re.compile(
            r"^(?:colspan|rowspan|width|style|align|valign|class|"
            r"cellpadding|nowrap|border|bgcolor|height)[\s=|]", re.IGNORECASE)
        for c in raw_cells:
            s = c.replace("\x04", "|").strip()
            if s in ("}", "{|") or (s and _ATTR.match(s)):
                continue
            total_cells += 1
            if not s:
                empty_cells += 1
    if total_cells >= 4 and empty_cells > total_cells * 0.5:
        return True
    return False


def _process_equation_layout(inner: str, text_transform) -> str:
    """Process an equation-layout table: join each row's content cells into one line.

    These are wiki tables used for visual alignment of equations,
    not for tabular data.  Each row becomes a single text line.
    """
    inner = re.sub(r"<br\s*/?>", " ", inner, flags=re.IGNORECASE)
    _ATTR = re.compile(
        r"^(?:colspan|rowspan|width|style|align|valign|class|"
        r"cellpadding|nowrap|border|bgcolor|height)[\s=|]", re.IGNORECASE)

    def _extract_cells(row_text):
        protected = re.sub(r"\{\{[^}]*\}\}", lambda m: m.group(0).replace("|", "\x04"), row_text)
        protected = re.sub(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH),
                           lambda m: m.group(0).replace("|", "\x04"), protected)
        raw_cells = re.findall(r"\|([^|\n]*)", protected)
        raw_cells = [c.replace("\x04", "|") for c in raw_cells]
        cells = []
        for c in raw_cells:
            s = c.strip()
            if s in ("}", "{|"):
                continue
            if s and _ATTR.match(s):
                continue
            cells.append(text_transform(s) if s else " ")
        return cells

    raw_rows = re.split(r"\|-[^\n]*", inner)
    lines = []
    for raw_row in raw_rows:
        cells = _extract_cells(raw_row)
        content = [c for c in cells if c.strip()]
        if content:
            lines.append(" ".join(content))
    return "\n\n".join(lines) if lines else ""


def _is_layout_wrapper(raw: str, inner: str, inner_registry: ElementRegistry | None) -> bool:
    """Detect tables that wrap other tables/images for layout purposes.

    These are outer tables used to arrange images, captions, and nested
    tables (e.g. Greek transliterations) visually.  They should be
    unwrapped to sequential content, not rendered as data tables.

    Detected when a table contains:
      - A nested TABLE child, or
      - An IMAGE child with mostly non-data content (captions, short text)

    Tables with explicit border or rules attributes in the {| header are
    never layout wrappers — they are definitively data tables.
    """
    if not inner_registry:
        return False
    # Data table signals in the header override layout wrapper detection.
    header = raw.split("\n", 1)[0]
    if re.search(r'border\s*=\s*"?[1-9]', header, re.IGNORECASE):
        return False
    if re.search(r'rules\s*=', header, re.IGNORECASE):
        return False
    if re.search(r'class\s*=\s*"[^"]*(?:wikitable|tablecolhd|border)', header, re.IGNORECASE):
        return False
    child_types = {t for t, _ in inner_registry.elements.values()}
    if "TABLE" in child_types:
        # A nested TABLE usually means layout (outer is a shell around
        # the sub-table).  Exception: if the outer declares a wikitext
        # table caption via ``|+`` at the top of the table body, it's
        # a genuine data table.  ``|+`` is the MediaWiki table-caption
        # sigil — only data tables carry it.  This catches AFRICA's
        # "BANTU NEGROIDS" table (40 rows of tribe names, plus one
        # incidental nested bracket-grouping table) without relying on
        # content-length heuristics.
        if re.search(r"^\|\+", inner, re.MULTILINE):
            return False
        return True
    if "IMAGE" in child_types:
        # Strong signal: table contains a `Fig. N.—` / `Plate N.—`
        # caption line.  HYDROMEDUSAE Fig. 30 has ~800 chars of legend
        # text that would fail the length heuristic below, but it IS a
        # figure layout — the Fig.-caption pattern makes that
        # unambiguous and overrides the length check.
        if re.search(r"\{\{\s*sc\s*\|\s*(?:Fig|Plate)s?\.?|"
                     r"(?<![A-Za-z])(?:Fig|Plate)s?\.?\s*\d",
                     inner, re.IGNORECASE):
            return True
        # Check if non-image content is just captions (short text, no data)
        non_ph = re.sub(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH), "", inner)
        non_ph = re.sub(r"[-|{}\n]", " ", non_ph)
        non_ph = re.sub(r"\b(?:align|valign|colspan|rowspan|style|width|cellpadding|cellspacing|center|right|left|top|bottom)\b", "", non_ph, flags=re.IGNORECASE)
        non_ph = re.sub(r'[="]+', "", non_ph)
        non_ph = re.sub(r"\s+", " ", non_ph).strip()
        # If remaining text is short relative to number of images, it's a layout table
        n_images = sum(1 for _, (t, _) in inner_registry.elements.items() if t == "IMAGE")
        if len(non_ph) < n_images * 300:
            return True
    return False


# ── Image-layout subclassification ────────────────────────────────────
#
# Layout wikitables wrapping a single image fall into a few structural
# subclasses we recognize explicitly. Each subclass has a dedicated
# handler that emits `{{IMG:filename|caption}}` plus, when applicable,
# `{{LEGEND:…}LEGEND}` for the structured legend. Classes:
#
#   IMG_INLINE_LEGEND  — image cell + same-line `||` legend items;
#                        caption in a `|colspan=N|…Fig.` row below.
#                        Example: ABBEY vol 1 p. 43 (Fig. 1, Santa Laura).
#   IMG_MULTICOL_LEGEND — image row + caption row + subsequent rows of
#                         `||`-separated (label, text) pairs that need
#                         re-sorting into alphabetic reading order.
#                         Example: ABBEY vol 1 p. 46 (Fig. 5, Cluny).
#   IMG_POEM_LEGEND    — outer table wraps image + caption + a nested
#                        POEM-only layout table (left/right columns of
#                        `<poem>` legends with `{{csc|…}}` subheadings).
#                        Example: ABBEY vol 1 p. 44 (Fig. 3, St Gall).
#
# Anything that doesn't match falls back to the generic layout unwrap
# logic further down.


# Accepts legend labels like:
#   A              single letter
#   P₁             letter + subscript
#   X₁X₁           repeated letter-subscript pair (Abbey_3 X₁X₁, X₂X₂)
#   c,c            comma-separated repeats (Abbey_3 "c,c. Mills.")
#   k,k,k          same, 3 entries
#   1              single digit (Fig. 9 Kirkstall Abbey)
#   10             multi-digit (Fig. 10 Fountains third column)
#   16-19          inclusive range (Fig. 9 "16-19. Uncertain…")
#   c.c            dotted compound abbreviation (HYDROMEDUSAE Fig. 30
#                    "c.c,  Circular canal.")
#   st.c           similar
# Label must start AND end with an alphanumeric; internal chars may
# include letters, digits, subscript chars, a hyphen (for ranges),
# or a period (for compound abbreviations).
# The trailing `.` is required (legends always use "L. text" form).
_LEGEND_LABEL = (
    r"[A-Za-z0-9](?:[A-Za-z0-9₁₂₃.\-]*[A-Za-z0-9₁₂₃])?")
_LEGEND_ENTRY_RE = re.compile(
    # Label terminator may be `.` OR `,` — HEXAPODA Fig. 18 Springtail
    # uses `1, Ocular segment.` form inside `<poem>` blocks.
    r"^\s*(" + _LEGEND_LABEL +
    r"(?:\s*,\s*" + _LEGEND_LABEL + r")*)[.,]\s+(.*\S)\s*$")


def _clean_legend_text(text: str) -> str:
    """Clean a legend entry (letter or text).  Strips layout templates,
    entity refs, and inline markers.  Runs after text_transform."""
    text = text.replace("&thinsp;", " ").replace("&ensp;", " ")
    text = text.replace("&emsp;", " ").replace("&nbsp;", " ")
    text = re.sub(r"\{\{\s*(?:em|gap|dhr|vr|hr|thinsp)\s*(?:\|[^{}]*)?\}\}",
                  " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    # Unwrap any layout/style templates that snuck through, keep arg
    for _ in range(3):
        text = re.sub(r"\{\{\s*(?:sc|smaller|c|center|small|csc|b|i)\s*\|"
                      r"([^{}]*)\}\}",
                      r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\u00ab/?[A-Z]+\u00bb", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _format_legend_entries(entries: list[tuple[str, str]],
                            sort_alphabetic: bool = False) -> str:
    """Render (label, text) pairs as one entry per line: `L. text`.

    When `sort_alphabetic` is True, entries are sorted by their label
    in reading order (A, B, C…) — used for MULTICOL layouts where the
    source row-major order is a visual grid, not the reading order."""
    if sort_alphabetic:
        def _key(e):
            lbl = e[0]
            # Pad any embedded integer runs so `2` sorts before `10`.
            # Uppercase variants sort before lowercase ones
            # (A-T first, then a-t for "Menial Department" style).
            case_rank = 0 if lbl[:1].isupper() else 1
            padded = re.sub(r"\d+", lambda m: m.group(0).zfill(6), lbl)
            return (case_rank, padded)
        entries = sorted(entries, key=_key)
    return "\n".join(f"{label}. {text}"
                     for label, text in entries if text)


def _parse_inline_legend_cell(
    cell_text: str, text_transform
) -> tuple[str, list[tuple[str, str]]]:
    """Parse a cell like `«PH_IMG»||A. Gateway.\n\nB. Chapels.\n…` into
    (image_placeholder, legend-entries). Returns ("", []) if the cell
    isn't an image + inline-legend.

    The `||` is MediaWiki same-line cell shorthand, but here we treat
    it as a soft separator between the image and the first legend
    entry.  Subsequent entries appear on separate lines.
    """
    # Split on the FIRST `||` only (image || first-entry-starts-here)
    if "||" not in cell_text:
        return "", []
    head, _, rest = cell_text.partition("||")
    head = head.strip()
    # Head must be a bare placeholder for this to be the pattern
    if not re.fullmatch(
            re.escape(_PH) + r"ELEM:\d+" + re.escape(_PH), head):
        return "", []
    # Parse rest into one-entry-per-line.  Any remaining `||` inside
    # `rest` (shouldn't occur for the canonical pattern but guard
    # anyway) and blank lines become line breaks.  `_LEGEND_ENTRY_RE`
    # matches each non-empty line against the `L. text` shape.
    rest = rest.replace("||", "\n")
    entries: list[tuple[str, str]] = []
    for raw in rest.split("\n"):
        raw = raw.strip()
        if not raw:
            continue
        raw = _strip_cell_attributes(raw)
        line = text_transform(raw)
        line = _clean_legend_text(line)
        m = _LEGEND_ENTRY_RE.match(line)
        if m:
            entries.append((m.group(1), m.group(2)))
        # Non-matching lines get dropped (whitespace or stray text).
    return head, entries


_MULTICOL_FULL_ENTRY_RE = re.compile(
    r"^\s*([A-Za-z0-9]+(?:\s*,\s*[A-Za-z0-9]+)*)\.\s+(.+\S)\s*$")

# Strict validator for a parsed legend label — rejects "Steiner," and
# similar chemist-name false positives while accepting "A", "P₁",
# "X₁X₁", "c,c", "k,k,k", "1", "10", "16-19", "c.c", "st.c", etc.
#
# Also accepts multi-word italicized biological abbreviations
# (HYDROMEDUSAE Fig. 30 "c.c,  Circular canal.", SPONGES Fig. 2
# "cl. osc.,  Closed osculum.", etc.) — up to ~20 chars, made of
# short alphanumeric words separated by periods or spaces.
_LEGEND_LABEL_STRICT_RE = re.compile(
    r"^" + _LEGEND_LABEL +
    r"(?:\s*,\s*" + _LEGEND_LABEL + r")*$")
_LEGEND_LABEL_MULTIWORD_RE = re.compile(
    r"^[A-Za-z][A-Za-z]{0,5}(?:[.,]?\s+[A-Za-z][A-Za-z]{0,5}){1,3}\.?$")


_SUPERSCRIPT_TO_ASCII = {
    0x2070: "0", 0x00B9: "1", 0x00B2: "2", 0x00B3: "3",
    0x2074: "4", 0x2075: "5", 0x2076: "6", 0x2077: "7",
    0x2078: "8", 0x2079: "9",
}
_SUBSCRIPT_TO_ASCII = {
    0x2080: "0", 0x2081: "1", 0x2082: "2", 0x2083: "3",
    0x2084: "4", 0x2085: "5", 0x2086: "6", 0x2087: "7",
    0x2088: "8", 0x2089: "9",
}
_PRIMES = (0x2032, 0x2033, 0x2034, 0x2035, 0x2036, 0x2037,
           0x02B9, 0x02BA, 0x02BC)


def _ascii_fold_label(label: str) -> str:
    """Fold a label to plain ASCII for regex-shape validation.

    * Unicode Mathematical Italic letters (𝑎–𝑧, 𝐴–𝑍, ℎ) → ASCII
      (MUSCULAR SYSTEM Fig. 9)
    * Unicode superscript digits (⁰¹²³⁴⁵⁶⁷⁸⁹) → ASCII digits
      (HEXAPODA Fig. 14 `T⁸`, `S⁷`)
    * Unicode subscript digits (₀₁₂…) → ASCII digits
    * Prime family (′ ″ ‴ ‵ etc.) → dropped (HYDROMEDUSAE Fig. 26
      `a′, g″, k′`)

    The display form stays intact — only the validator sees the fold."""
    out = []
    for ch in label:
        cp = ord(ch)
        if 0x1D44E <= cp <= 0x1D467:
            out.append(chr(ord('a') + cp - 0x1D44E))
        elif 0x1D434 <= cp <= 0x1D44D:
            out.append(chr(ord('A') + cp - 0x1D434))
        elif cp == 0x210E:
            out.append('h')
        elif cp in _SUPERSCRIPT_TO_ASCII:
            out.append(_SUPERSCRIPT_TO_ASCII[cp])
        elif cp in _SUBSCRIPT_TO_ASCII:
            out.append(_SUBSCRIPT_TO_ASCII[cp])
        elif cp in _PRIMES:
            continue
        else:
            out.append(ch)
    return ''.join(out)


_LEGEND_LABEL_LENIENT_RE = re.compile(
    # Short, starts+ends with alphanumeric, allows spaces, periods,
    # commas, hyphens, ampersand (HEXAPODA Fig. 14 `T8 &c`).  Capped at
    # 15 chars so it can't swallow sentence fragments.
    r"^[A-Za-z0-9](?=.{0,14}$)[A-Za-z0-9 &,.\-]*[A-Za-z0-9.]$")


def _entries_look_like_legend(entries: list[tuple[str, str]]) -> bool:
    """Return True only if every parsed (label, text) tuple has a
    label matching one of the accepted legend-label shapes.  Defence
    against mis-classifying non-legend `||`-rich tables (e.g. FULMINIC
    ACID chemist names).  Three progressively lenient patterns:

      1. strict: purely alphanumeric (A, P₁, X₁X₁, c,c, 1, 10, 16-19)
      2. multi-word: biological abbreviations (cl. osc., osc. div.)
      3. lenient: short (≤15 chars) with spaces/&/punctuation
         allowed, for cases like HEXAPODA `T8 &c` (et cetera).
    """
    if not entries:
        return False
    for label, text in entries:
        folded = _ascii_fold_label(label)
        if (not _LEGEND_LABEL_STRICT_RE.match(folded)
                and not _LEGEND_LABEL_MULTIWORD_RE.match(folded)
                and not _LEGEND_LABEL_LENIENT_RE.match(folded)):
            return False
        if not text:
            return False
    return True


_CELL_ATTR_PREFIX_RE = re.compile(
    # Attribute-value may NOT contain `{` / `}` — otherwise the greedy
    # `[^"|\n]*` slurps across a following `{{Ts|…}}` styling template
    # and mis-consumes it as an attr value, which then breaks cap-row
    # detection (`colspan=2 {{Ts|ac}}|{{sc|Fig. 54}}…` is a real
    # Mosque of Amr example).
    r"^(?:\s*(?:colspan|rowspan|align|valign|style|width|class|"
    r"cellpadding|cellspacing|bgcolor|height|nowrap|border|scope|id)"
    r"\s*=\s*\"?[^\"|\n{}]*\"?\s*)+\|",
    re.IGNORECASE,
)


def _strip_cell_attributes(cell: str) -> str:
    """Strip leading `attr=val|` cell-attribute prefix and `{{Ts|…}}`
    styling templates from a wikitable cell's content.  Used by the
    legend parsers so `colspan=3|Malpighian corpuscles.` renders as
    `Malpighian corpuscles.`, not as literal attribute text.  Also
    drops a bare leading `|` that a `{{Ts|…}}|content` sequence
    leaves behind after template stripping (WEAVING Fig. 20)."""
    cell = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", cell)
    m = _CELL_ATTR_PREFIX_RE.match(cell)
    if m:
        cell = cell[m.end():]
    if cell.startswith("|"):
        cell = cell[1:].lstrip()
    return cell


def _parse_multicol_legend_row(
    row_text: str, text_transform
) -> list[tuple[str, str]]:
    """Parse a row of `||`-separated legend entries.

    Two shapes are supported:

    1. Alternating-pair (Cluny vol 1 p. 46):
         `A.||Gateway.||F.||Tomb of St Hugh.||M.||Bakehouse.`
       Every OTHER cell is a label, the next is its text.

    2. Full-entry-per-cell (Mosque of Amr vol 2 p. 450):
         `1. Kibla. || 5. Fountain for Ablution`
       Every cell is a complete `label. text` entry.

    Detection: if the first cell itself matches the `label. text`
    shape, we treat every cell as a full entry; otherwise we fall back
    to alternating-pair parsing.
    """
    pieces = row_text.replace("||", "\x01").split("\x01")
    pieces = [p.lstrip("|").strip() for p in pieces if p.strip()]
    if not pieces:
        return []
    # Strip per-cell attribute prefixes (colspan=, rowspan=, width=,
    # etc.) — these are cell-layout hints, not legend content.
    pieces = [_strip_cell_attributes(p).strip() for p in pieces]
    pieces = [p for p in pieces if p]
    if not pieces:
        return []
    out: list[tuple[str, str]] = []
    # Apply text_transform up front so {{em|…}} spacers, italics, and
    # entity refs are normalized before label detection.
    transformed = [text_transform(p) for p in pieces]

    # Shape detection on the first cell.
    #
    # If the first cell is italicized (biological-abbreviation
    # convention, SPONGES Fig. 2 "''cl. osc.''"), it's a label-only
    # cell — the format is label || text alternating, NOT full-entry.
    # Without this guard `cl. osc.,` would match the full-entry regex
    # as (label=`cl`, text=`osc.,`) and produce garbage.
    first_is_italic = transformed[0].strip().startswith(
        "\u00abI\u00bb")
    first = _clean_legend_text(transformed[0])
    if not first_is_italic and _MULTICOL_FULL_ENTRY_RE.match(first):
        # Full-entry-per-cell
        for t in transformed:
            cell = _clean_legend_text(t)
            m = _MULTICOL_FULL_ENTRY_RE.match(cell)
            if m:
                out.append((m.group(1), m.group(2).rstrip(". ")))
        return out
    # Alternating-pair.  Labels may terminate with `.` OR `,`
    # (HYDROMEDUSAE Fig. 30 uses `''ex'',||Ex-umbral ectoderm.`);
    # strip both trailing punctuations.
    i = 0
    while i + 1 < len(transformed):
        label = _clean_legend_text(transformed[i]).rstrip(".,")
        text = _clean_legend_text(transformed[i + 1])
        if label and text:
            out.append((label, text))
        i += 2
    return out


def _extract_poem_legend(
    table_raw: str, text_transform
) -> list[str]:
    """Extract legend content from a nested layout table as a list of
    LEGEND-format lines (`### Subhead.` or `L. text`).  Tries three
    shapes in preference order:

      A. `<poem>` blocks with `{{csc|…}}` subheadings (Abbey_3)
      B. `||`-separated (label, text) rows (HYDROMEDUSAE Fig. 73)
      C. Plain-paragraph `''label'', text` entries in a single cell
         (HYDROMEDUSAE Fig. 55)
    """
    body = re.sub(r"^\{\|[^\n]*\n?", "", table_raw)
    body = re.sub(r"\n?\|\}\s*$", "", body)
    cells = re.split(r"\n\s*\|-+[^\n]*\n", body)

    # --- Shape A: poems + csc subheadings ---
    poem_lines: list[str] = []
    for cell_block in cells:
        current_cell: list[str] = []

        def flush_cell():
            if not current_cell:
                return
            text = "\n".join(current_cell)
            _emit_legend_chunk(text, text_transform, poem_lines)

        for line in cell_block.split("\n"):
            stripped = line.strip()
            if stripped.startswith("|") and current_cell:
                flush_cell()
                current_cell = [stripped.lstrip("|").strip()]
            elif stripped.startswith("|"):
                current_cell = [stripped.lstrip("|").strip()]
            else:
                current_cell.append(line)
        flush_cell()
    if poem_lines:
        return poem_lines

    # --- Shape B: ||-separated (label, text) rows ---
    pair_entries: list[tuple[str, str]] = []
    for cell_block in cells:
        if "||" in cell_block:
            pair_entries.extend(
                _parse_multicol_legend_row(cell_block, text_transform))
    if pair_entries and _entries_look_like_legend(pair_entries):
        return [f"{lbl}. {text}" for lbl, text in pair_entries]

    # --- Shape C: plain-paragraph `''label'', text` entries ---
    plain_entries: list[tuple[str, str]] = []
    entry_re = re.compile(
        r"^\s*(?:''\s*)?([A-Za-z0-9](?:[A-Za-z0-9.\-]{0,15})?)"
        r"(?:\s*''\s*)?[.,]\s+(.+\S)\s*$",
        re.DOTALL,
    )
    for cell_block in cells:
        for para in re.split(r"\n\s*\n", cell_block):
            para = para.strip()
            if not para:
                continue
            if para.startswith("|"):
                para = para[1:].strip()
                if not para:
                    continue
            transformed = text_transform(para)
            cleaned = _clean_legend_text(transformed)
            m = entry_re.match(cleaned)
            if m:
                plain_entries.append((m.group(1), m.group(2)))
    if plain_entries and _entries_look_like_legend(plain_entries):
        return [f"{lbl}. {text}" for lbl, text in plain_entries]

    return []


def _emit_legend_chunk(text: str, text_transform,
                        out: list[str]) -> None:
    """Parse one cell's worth of legend source text, appending entries
    and `### Subhead.` lines to `out` in SOURCE ORDER.

    Subheadings (`{{csc|Church.}}`) and `<poem>` blocks are
    interleaved in the source; this single-pass scanner walks forward
    and emits them in the order they appear, so the reader sees e.g.:

        ### Church.
        A. High altar.
        B. Altar of St Paul.
        ### Monastic Buildings.
        G. Cloister.
    """
    sub_re = re.compile(r"\{\{\s*csc\s*\|([^{}]*)\}\}", re.IGNORECASE)
    poem_re = re.compile(r"<poem>([\s\S]*?)</poem>", re.IGNORECASE)
    pos = 0
    while pos < len(text):
        m_sub = sub_re.search(text, pos)
        m_poem = poem_re.search(text, pos)
        # Pick whichever matches first
        if m_sub and (not m_poem or m_sub.start() < m_poem.start()):
            content = _clean_legend_text(m_sub.group(1)).rstrip(".")
            if content:
                out.append(f"### {content}.")
            pos = m_sub.end()
        elif m_poem:
            for ln in m_poem.group(1).splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                ln = text_transform(ln)
                ln = _clean_legend_text(ln)
                em = _LEGEND_ENTRY_RE.match(ln)
                if em:
                    out.append(f"{em.group(1)}. {em.group(2)}")
            pos = m_poem.end()
        else:
            break


def _image_ph_filename(
    ph_id: str, inner_registry: ElementRegistry
) -> str | None:
    """Look up the filename for an IMAGE element placeholder."""
    info = inner_registry.elements.get(ph_id)
    if not info or info[0] != "IMAGE":
        return None
    m = re.match(r"\[\[(?:File|Image):([^\]|]+)",
                 info[1], re.IGNORECASE)
    return m.group(1).strip() if m else None


_FIG_CAPTION_START_RE = re.compile(
    # Accepts leading italic `''`, smallcaps `{{sc|`, or bare `Fig.` /
    # `Plate.` text.  HYDROMEDUSAE sources use all three variants.
    r"^\s*(?:''|\{\{\s*sc\s*\|\s*)*(?:Fig|Plate)s?\.?",
    re.IGNORECASE,
)


# Matches a `Fig. N.` / `Plate N.` caption anywhere in a string.
# Allows up to 10 chars of punctuation/whitespace between `Fig` and
# the number so variants like `{{sc|Fig}}. 8` (period AFTER the `}}`)
# still match.
_FIG_CAPTION_INLINE_RE = re.compile(
    r"(?:''|\{\{\s*sc\s*\|\s*)*"
    r"(?:Fig|Plate)s?[\s.}]{1,10}\d",
    re.IGNORECASE,
)


def _looks_like_caption(text: str) -> bool:
    """True if `text` starts with `Fig. N.` / `Plate N.` / `{{sc|Fig` /
    `''Fig.''`."""
    return bool(_FIG_CAPTION_START_RE.match(text))


def _find_caption_row_idx(
    rows: list[str], start_idx: int, text_transform
) -> int | None:
    """Locate the caption row (one starting with `Fig. N.—` or similar)
    among `rows[start_idx+1:]`.  This lets us skip attribution lines
    like `From Allman's Gymnoblastic Hydroids…` that sit between the
    image and the real caption.  Returns the row index, or None.

    Falls back to accepting a row where the `Fig. N.` pattern appears
    MID-CELL after an in-cell attribution (HYDROMEDUSAE Fig. 71 Velella:
    `From G. H. Fowler, after Cuvier, …  {{sc|Fig. 71.}}—…`)."""
    # Preferred: a row whose prefix-stripped content STARTS with Fig.
    for i in range(start_idx + 1, len(rows)):
        body = rows[i].strip()
        body = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", body)
        for _ in range(5):
            before = body
            if body.startswith("|"):
                body = body[1:].lstrip()
            m = _CELL_ATTR_PREFIX_RE.match(body)
            if m:
                body = body[m.end():]
            body = body.lstrip()
            if body == before:
                break
        if _looks_like_caption(body):
            return i
    # Fallback: a row where `{{sc|Fig.}}` / `''Fig.''` / `Fig. N.`
    # appears mid-cell (attribution precedes the caption in the same
    # cell).  `_extract_caption_from_colspan_row` handles extraction.
    for i in range(start_idx + 1, len(rows)):
        if _FIG_CAPTION_INLINE_RE.search(rows[i]):
            return i
    return None


def _extract_caption_from_colspan_row(
    row_text: str, text_transform
) -> str | None:
    """Pull caption text from a `|colspan=N …|caption` row.  In-cell
    attribution (HYDROMEDUSAE Fig. 71 Velella: `From G. H. Fowler,
    after Cuvier… {{sc|Fig. 71.}}—…`) is appended to the caption in
    parens so the credit survives."""
    body = row_text.strip()
    if body.startswith("|"):
        body = body[1:]
    body = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", body)
    m = re.match(
        r"^(?:(?:colspan|rowspan|align|valign|style|width|class)"
        r"\s*=\s*\"?[^\"|\n{}]*\"?\s*)+\|",
        body, re.IGNORECASE)
    if m:
        body = body[m.end():]
    body = body.strip()
    # Split out in-cell attribution preceding the Fig. caption.
    attribution = None
    if not _looks_like_caption(body):
        fig_m = _FIG_CAPTION_INLINE_RE.search(body)
        if fig_m:
            prefix = body[:fig_m.start()].strip()
            body = body[fig_m.start():]
            if prefix:
                attr_clean = _clean_text(text_transform(prefix))
                attr_clean = attr_clean.rstrip(" .,;:")
                if attr_clean:
                    attribution = attr_clean
    caption = _clean_text(text_transform(body.strip()))
    if not caption:
        return None
    if attribution:
        caption = _append_attribution(caption, attribution)
    return caption


def _append_attribution(caption: str, attribution: str) -> str:
    """Combine a caption with its attribution in a stable parenthetical
    form.  Avoids doubling parens when attribution itself already
    wraps in parens, and idempotent if called twice."""
    attribution = attribution.strip(" .")
    if not attribution:
        return caption
    if attribution in caption:
        return caption
    # If attribution is already parenthesized, keep its form.
    if attribution.startswith("(") and attribution.endswith(")"):
        return f"{caption.rstrip()} {attribution}"
    return f"{caption.rstrip()} ({attribution}.)"


def _collect_attribution_rows(
    rows: list[str], img_row_idx: int, cap_row_idx: int,
    text_transform,
) -> str:
    """Collect clean attribution text from rows strictly between the
    image row and the caption row.  Typical sources: `{{sm|From A. M.
    Paterson, …}}` or `|style="font-size:smaller"|From O. Maas, …`.
    Returns a single joined string (may be empty)."""
    parts: list[str] = []
    for i in range(img_row_idx + 1, cap_row_idx):
        body = rows[i].strip()
        body = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", body)
        body = re.sub(r"\{\{sm\|([^{}]*)\}\}", r"\1", body,
                      flags=re.IGNORECASE)
        if body.startswith("|"):
            body = body[1:].lstrip()
        m = _CELL_ATTR_PREFIX_RE.match(body)
        if m:
            body = body[m.end():]
        body = body.strip()
        if not body:
            continue
        t = _clean_text(text_transform(body))
        t = t.strip(" .,;")
        if t:
            parts.append(t)
    return " ".join(parts).strip()


# Prose-legend entry: `LABEL, text.` or `LABEL. text.` chunk where
# LABEL is a short alphanumeric token (possibly Roman numeral).
_PROSE_ENTRY_SPLIT_RE = re.compile(
    r"(?=(?:^|\. |; |\s)(?:[IVX]+|[A-Za-z][A-Za-z0-9.]{0,4})[,.] )")


def _parse_prose_legend_rows(
    legend_rows: list[str], text_transform
) -> list[str]:
    """Parse rows that contain prose-format legend entries (no ||
    separator, multiple `LABEL, text.` or `LABEL. text.` chunks per
    line, optional `''Subheading'':` lines).

    Returns LEGEND-format lines (`### Sub.` or `L. text`), or []
    if no plausible entries were found.
    """
    out: list[str] = []
    subhead_re = re.compile(
        r"^\s*(?:&emsp;|&ensp;|&nbsp;|\s)*"
        r"''([^']{2,30})''\s*:\s*(?:<br\s*/?>)?\s*(.*)$",
        re.IGNORECASE)
    entry_label = _LEGEND_LABEL
    entry_re = re.compile(
        r"^\s*(" + entry_label +
        r"(?:\s*,\s*" + entry_label + r")*)[.,]\s+(.+)$",
        re.DOTALL)

    for row in legend_rows:
        # Strip cell attrs, Ts styling, and leading `|`
        row = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", row)
        # `{{hi|…}}` has two forms: `{{hi|text}}` and
        # `{{hi|amount|text}}`.  Unwrap both, keeping only the text
        # argument.
        row = re.sub(r"\{\{hi\|[^|{}]*\|([^{}]*)\}\}", r"\1", row,
                     flags=re.IGNORECASE)
        row = re.sub(r"\{\{hi\|([^{}]*)\}\}", r"\1", row,
                     flags=re.IGNORECASE)
        # Work line by line within the row
        cell_content = row
        if cell_content.lstrip().startswith("|"):
            cell_content = cell_content.lstrip()[1:]
        for line in cell_content.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Subheading line: `''Name'':<br>rest`  or  `''Name'':`
            m = subhead_re.match(line)
            if m:
                sub = m.group(1).strip().rstrip(":")
                out.append(f"### {sub}.")
                line = m.group(2).strip()
                if not line:
                    continue
            # Transform + clean the line
            tl = text_transform(line)
            tl = _clean_legend_text(tl)
            if not tl:
                continue
            # Split on sentence boundaries that precede a label.
            chunks = re.split(
                r"(?<=\.)\s+(?=(?:[IVX]+|[A-Za-z][A-Za-z0-9.]{0,4})"
                r"[,.] )", tl)
            for chunk in chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue
                em = entry_re.match(chunk)
                if em:
                    label = em.group(1).strip()
                    text = em.group(2).strip().rstrip(". ")
                    if text:
                        out.append(f"{label}. {text}")
                # Chunks that don't parse are silently dropped —
                # we only want real legend entries.
    # Only return if we got multiple real entries (not just
    # subheadings) — a single-subheading-only legend is suspicious.
    entry_count = sum(1 for line in out if not line.startswith("###"))
    if entry_count >= 3 and _entries_look_like_legend(
            [tuple(line.split(". ", 1)) for line in out
             if not line.startswith("###")]):
        return out
    return []


def _try_image_layout_subclass(
    inner: str, text_transform,
    inner_registry: ElementRegistry
) -> str | None:
    """Attempt to recognize one of the three known image-layout
    subclasses (INLINE, MULTICOL, POEM).  Returns the processed output
    on match, or None to fall through to the generic unwrapper."""
    if not inner_registry:
        return None
    image_phs = [k for k, (t, _) in inner_registry.elements.items()
                 if t == "IMAGE"]
    if not image_phs:
        return None

    # Multi-image layout: outer table wraps 2+ images.
    if len(image_phs) >= 2:
        table_phs = [k for k, (t, _) in inner_registry.elements.items()
                     if t == "TABLE"]
        poem_phs = [k for k, (t, _) in inner_registry.elements.items()
                     if t == "POEM"]
        if table_phs or poem_phs:
            return None
        rows_local = re.split(r"\n\s*\|-+[^\n]*\n", inner)
        # Per-image row positions
        img_row_of: dict[str, int] = {}
        for ph in image_phs:
            for i, r in enumerate(rows_local):
                if ph in r:
                    img_row_of[ph] = i
                    break

        # Side-by-side variant: all images on the SAME row AND the
        # next row is a single `||`-separated caption row (WEAVING
        # Figs 19/20, 11/12).  Split caption by position.
        unique_rows = set(img_row_of.values())
        if (len(unique_rows) == 1 and len(img_row_of) == len(image_phs)):
            img_row = next(iter(unique_rows))
            if img_row + 1 < len(rows_local):
                cap_row_text = rows_local[img_row + 1]
                if "||" in cap_row_text:
                    # Split caption row into per-cell captions.
                    pieces = cap_row_text.replace("||", "\x01").split("\x01")
                    pieces = [p.lstrip("|").strip() for p in pieces if p.strip()]
                    # Strip cell attrs per piece
                    pieces = [_strip_cell_attributes(p).strip() for p in pieces]
                    pieces = [p for p in pieces if p]
                    if len(pieces) == len(image_phs):
                        # Determine image order in the row
                        row_text = rows_local[img_row]
                        ordered_phs = sorted(
                            image_phs,
                            key=lambda p: row_text.find(p))
                        parts_out = []
                        for ph, piece in zip(ordered_phs, pieces):
                            fn = _image_ph_filename(ph, inner_registry)
                            if not fn:
                                continue
                            cap = _clean_text(text_transform(piece))
                            if cap:
                                parts_out.append(
                                    f"{{{{IMG:{fn}|{cap}}}}}")
                            else:
                                parts_out.append(f"{{{{IMG:{fn}}}}}")
                        if parts_out:
                            return "\n\n" + "\n\n".join(parts_out) + "\n\n"

        # Vertical variant (MUSCULAR SYSTEM Figs 7-8): each image has
        # its OWN attribution + caption rows beneath.
        parts_out: list[str] = []
        for ph in image_phs:
            filename = _image_ph_filename(ph, inner_registry)
            if not filename:
                continue
            img_row = img_row_of.get(ph)
            if img_row is None:
                continue
            cap_row = _find_caption_row_idx(
                rows_local, img_row, text_transform)
            caption = None
            if cap_row is not None:
                caption = _extract_caption_from_colspan_row(
                    rows_local[cap_row], text_transform)
                attr = _collect_attribution_rows(
                    rows_local, img_row, cap_row, text_transform)
                if caption and attr:
                    caption = _append_attribution(caption, attr)
            if caption:
                parts_out.append(f"{{{{IMG:{filename}|{caption}}}}}")
            else:
                parts_out.append(f"{{{{IMG:{filename}}}}}")
        if parts_out:
            return "\n\n" + "\n\n".join(parts_out) + "\n\n"
        return None

    img_ph = image_phs[0]
    filename = _image_ph_filename(img_ph, inner_registry)
    if not filename:
        return None

    table_phs = [k for k, (t, _) in inner_registry.elements.items()
                 if t == "TABLE"]

    # Split into rows on `|-`
    rows = re.split(r"\n\s*\|-+[^\n]*\n", inner)

    # Locate the row containing the image placeholder and the row
    # containing the caption (typically colspan=N … Fig. …).
    img_row_idx = None
    for i, r in enumerate(rows):
        if img_ph in r:
            img_row_idx = i
            break
    if img_row_idx is None:
        return None

    poem_phs = [k for k, (t, _) in inner_registry.elements.items()
                 if t == "POEM"]

    # Locate the caption row.  `fig_cap_idx` is set only when we find
    # a row that actually begins with `Fig. N.—` / `Plate N.—` —
    # strong signal that this table IS a figure layout.  When absent,
    # most subclasses fall back to `img_row_idx + 1`, but the MULTICOL
    # and IMG_ATTRIBUTION_CAPTION paths REQUIRE `fig_cap_idx` so that
    # non-figure tables (FULMINIC ACID formula comparison) can't
    # masquerade as legends.
    fig_cap_idx = _find_caption_row_idx(rows, img_row_idx, text_transform)
    cap_idx = fig_cap_idx
    if cap_idx is None and img_row_idx + 1 < len(rows):
        cap_idx = img_row_idx + 1

    # -- POEM_COLUMNS_LEGEND: outer has 1 image + N poems as DIRECT
    #    children (not wrapped in a nested table).  Fig. 6 / Fig. 7
    #    in ABBEY use this.  Row 0 = colspan image, row 1 = colspan
    #    caption, rows 2+ = cells containing `<poem>` placeholders.
    if poem_phs and not table_phs:
        # Image row + caption row expected
        if cap_idx is not None:
            caption = _extract_caption_from_colspan_row(
                rows[cap_idx], text_transform)
            if caption:
                # Walk each poem in registry-insertion order (which
                # matches source order because extract() is linear).
                # For each POEM, extract its content and parse into
                # LEGEND entries. CSC subheadings that sit OUTSIDE
                # poems (between cells) aren't common in this shape
                # but we support them by also scanning the raw inner
                # text between poem placeholders.
                legend_lines: list[str] = []
                for ph, (et, eraw) in inner_registry.elements.items():
                    if et != "POEM":
                        continue
                    # Extract poem body, apply _emit_legend_chunk so
                    # it goes through the same entry-pattern matcher
                    # as the other legend handlers.
                    _emit_legend_chunk(eraw, text_transform, legend_lines)
                if legend_lines:
                    img_marker = f"{{{{IMG:{filename}|{caption}}}}}"
                    legend_block = (
                        "{{LEGEND:" + "\n".join(legend_lines) +
                        "}LEGEND}")
                    # Wrap in \n\n on both sides so the figure+legend
                    # always ends up as its own paragraph, regardless
                    # of surrounding whitespace. Excess newlines get
                    # collapsed by the transform normalizer.
                    return f"\n\n{img_marker}\n\n{legend_block}\n\n"

    # -- NESTED_LEGEND: outer has a single TABLE child (a nested
    #    layout table containing the legend).  `_extract_poem_legend`
    #    tries three shapes (poems / ||-pairs / plain paragraphs) and
    #    returns an empty list if none matches — in that case we fall
    #    through so that data tables aren't mis-claimed as legends.
    if len(table_phs) == 1:
        inner_table_ph = table_phs[0]
        inner_table_raw = inner_registry.elements[inner_table_ph][1]
        legend_lines = _extract_poem_legend(
            inner_table_raw, text_transform)
        if legend_lines:
            # Caption: prefer a Fig.-matched row.  In the Abbey_3
            # shape, the caption row ALSO contains the inner-table
            # placeholder, which we must strip before caption
            # extraction (otherwise its processed legend content
            # would get substituted back into the caption field).
            caption = None
            if fig_cap_idx is not None:
                row_without_ph = rows[fig_cap_idx].replace(
                    inner_table_ph, "")
                caption = _extract_caption_from_colspan_row(
                    row_without_ph, text_transform)
            if not caption:
                caption_row = next(
                    (r for r in rows if inner_table_ph in r), None)
                if caption_row is not None:
                    caption_cell = caption_row.replace(
                        inner_table_ph, "").strip()
                    caption_cell = re.sub(r"^\|\s*", "", caption_cell)
                    caption_cell = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*",
                                           "", caption_cell)
                    caption = _clean_text(text_transform(caption_cell))
            img_marker = (f"{{{{IMG:{filename}|{caption}}}}}"
                          if caption
                          else f"{{{{IMG:{filename}}}}}")
            legend_block = (
                "{{LEGEND:" + "\n".join(legend_lines) + "}LEGEND}")
            return f"\n\n{img_marker}\n\n{legend_block}\n\n"

    # -- INLINE_LEGEND: image row contains `||` on the image's own line.
    if "||" in rows[img_row_idx]:
        # Image row: `|[[Image:…]]||A. x\n\nB. y\n…`
        img_row = rows[img_row_idx]
        # Skip any leading `{{ts|…}}` styling line before the image cell.
        row_lines = [l for l in img_row.split("\n") if l.strip()]
        # The image-cell line is whichever one contains img_ph.
        image_line = next(l for l in row_lines if img_ph in l)
        # Image cell starts at `|` and runs across multiple lines until
        # the next line starting with `|` (next cell) or end of row.
        idx = row_lines.index(image_line)
        cell_lines = [image_line]
        for nxt in row_lines[idx + 1:]:
            if nxt.lstrip().startswith("|"):
                break
            cell_lines.append(nxt)
        cell_text = "\n".join(cell_lines).lstrip("|")
        _, entries = _parse_inline_legend_cell(cell_text, text_transform)
        if entries and _entries_look_like_legend(entries):
            # Caption: first row AFTER the image row that looks like a
            # colspan caption.
            caption = None
            for r in rows[img_row_idx + 1:]:
                c = _extract_caption_from_colspan_row(r, text_transform)
                if c:
                    caption = c
                    break
            img_marker = (f"{{{{IMG:{filename}|{caption}}}}}"
                          if caption else f"{{{{IMG:{filename}}}}}")
            legend_block = ("{{LEGEND:" +
                             _format_legend_entries(entries) + "}LEGEND}")
            return f"\n\n{img_marker}\n\n{legend_block}\n\n"

    # -- MULTICOL_LEGEND: image row + caption row + N rows of
    #    ||-separated (label, text) pairs.  Guards:
    #    1. Caption row must start with `Fig. N.—` / `Plate N.—`.
    #    2. At least one legend row must contain `||`.
    #    3. At least 2 (label,text) entries must parse.
    #    4. Every label must match the strict legend-label shape.
    if fig_cap_idx is not None:
        legend_rows = rows[fig_cap_idx + 1:]
        has_multicol_marker = any("||" in r for r in legend_rows)
        if has_multicol_marker:
            caption = _extract_caption_from_colspan_row(
                rows[fig_cap_idx], text_transform)
            if caption:
                entries: list[tuple[str, str]] = []
                for r in legend_rows:
                    entries.extend(
                        _parse_multicol_legend_row(r, text_transform))
                if (len(entries) >= 2
                        and _entries_look_like_legend(entries)):
                    img_marker = f"{{{{IMG:{filename}|{caption}}}}}"
                    legend_block = (
                        "{{LEGEND:" +
                        _format_legend_entries(
                            entries, sort_alphabetic=True) +
                        "}LEGEND}")
                    return f"\n\n{img_marker}\n\n{legend_block}\n\n"

    # -- IMG_PROSE_LEGEND: image + caption + rows of prose-format
    #    entries (multiple `LABEL, text.` chunks per line, optional
    #    `''Subheading'':` lines).  HEXAPODA Fig. 3 Thorax of Saw-Fly.
    #    Runs before IMG_SIMPLE_CAPTION so the sub-legend survives as
    #    a LEGEND block.
    if (fig_cap_idx is not None
            and not poem_phs and not table_phs
            and not any("||" in r for r in rows[fig_cap_idx + 1:])):
        legend_lines = _parse_prose_legend_rows(
            rows[fig_cap_idx + 1:], text_transform)
        if legend_lines:
            caption = _extract_caption_from_colspan_row(
                rows[fig_cap_idx], text_transform)
            if caption:
                img_marker = f"{{{{IMG:{filename}|{caption}}}}}"
                legend_block = (
                    "{{LEGEND:" + "\n".join(legend_lines) + "}LEGEND}")
                return f"\n\n{img_marker}\n\n{legend_block}\n\n"

    # -- IMG_SIMPLE_CAPTION / IMG_ATTRIBUTION_CAPTION: 1 image + a
    #    Fig.-matched caption row, no legend (no meaningful `||`, no
    #    POEM/TABLE children).  Covers simple 2-row image+caption
    #    (Corymorpha Fig. 3) and 3-row image+attribution+caption
    #    (HYDROMEDUSAE Fig. 5/29).  Rows between image and caption
    #    are attribution and get dropped.
    #
    #    A SPURIOUS `||` at the start of the image row (the MediaWiki
    #    `||[[Image:…]]` shorthand for "no attrs, content follows") is
    #    tolerated — detect it by asking whether the image row has
    #    any substantive text content besides the image placeholder.
    def _image_row_has_legend_text() -> bool:
        text = rows[img_row_idx].replace(img_ph, "")
        text = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}", "", text)
        text = re.sub(r"(?:colspan|rowspan|align|valign|style|width|"
                      r"class|cellpadding|cellspacing|bgcolor)"
                      r"\s*=\s*\"?[^\"|]*\"?", "", text,
                      flags=re.IGNORECASE)
        text = text.replace("||", "").replace("|", "")
        return bool(text.strip())

    if (fig_cap_idx is not None
            and not poem_phs and not table_phs
            and not any("||" in r for r in rows[fig_cap_idx + 1:])
            and not _image_row_has_legend_text()):
        caption = _extract_caption_from_colspan_row(
            rows[fig_cap_idx], text_transform)
        if caption:
            attr = _collect_attribution_rows(
                rows, img_row_idx, fig_cap_idx, text_transform)
            if attr:
                caption = _append_attribution(caption, attr)
            return f"\n\n{{{{IMG:{filename}|{caption}}}}}\n\n"

    return None


def _unwrap_layout_table(inner: str, text_transform,
                         inner_registry: ElementRegistry | None = None) -> str:
    """Unwrap a layout table to sequential content.

    Extracts cell content row by row, joining each cell's content
    as a separate block.  Child placeholders (images, nested tables)
    pass through and get substituted by the caller.

    Special case: if the table contains exactly one image placeholder
    + one or more caption rows, bundle them into a single
    {{IMG:filename|caption}} so the figure renders with its caption
    inside (avoids the duplicate-caption-paragraph regression seen in
    SEWING MACHINES Fig. 2 / ACACIA Senegal).
    """
    # First try the explicit image-layout subclasses (INLINE_LEGEND /
    # MULTICOL_LEGEND / POEM_LEGEND). These have dedicated handlers
    # that emit a structured `{{LEGEND:…}LEGEND}` block alongside the
    # image marker, which the generic unwrap cannot do. On no-match,
    # fall through to the legacy generic logic below.
    subclassed = _try_image_layout_subclass(
        inner, text_transform, inner_registry)
    if subclassed is not None:
        return subclassed

    inner = re.sub(r"<br\s*/?>", " ", inner, flags=re.IGNORECASE)
    _ATTR = re.compile(
        r"^(?:colspan|rowspan|width|style|align|valign|class|"
        r"cellpadding|nowrap|border|bgcolor|height)[\s=|]",
        re.IGNORECASE,
    )

    raw_rows = re.split(r"\|-[^\n]*", inner)
    parts = []
    for raw_row in raw_rows:
        # Collect all content: cell text, standalone placeholders,
        # and any text not inside cell markup
        row_content = []

        # Protect placeholders and templates from pipe splitting
        protected = re.sub(r"\{\{[^}]*\}\}", lambda m: m.group(0).replace("|", "\x04"), raw_row)
        protected = re.sub(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH),
                           lambda m: m.group(0).replace("|", "\x04"), protected)

        for line in protected.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Standalone placeholder (child element on its own line)
            if _PH in line and line.replace("\x04", "|").strip().startswith(_PH):
                row_content.append(line.replace("\x04", "|").strip())
                continue
            # Cell content after |
            if line.startswith("|"):
                cell = line[1:].replace("\x04", "|").strip()
                if not cell or cell in ("}", "{|"):
                    continue
                # Strip {{Ts|...}} styling and split attr|content
                cell = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", cell)
                if _ATTR.match(cell):
                    parts_after = cell.split("|", 1)
                    if len(parts_after) > 1:
                        cell = parts_after[1].strip()
                    else:
                        continue
                # Also split on remaining attr|content boundary
                elif "|" in cell:
                    before, _, after = cell.partition("|")
                    # If before is empty or only whitespace/templates, take after
                    stripped_before = re.sub(r"\{\{[^{}]*\}\}", "", before).strip()
                    if not stripped_before:
                        cell = after.strip()
                if cell:
                    row_content.append(cell)

        for c in row_content:
            # Placeholders (child elements) must pass through untouched,
            # but any surrounding text in the cell still needs
            # text_transform (entities, italic/bold, etc). Split on
            # placeholder boundaries, transform the text chunks only,
            # then rejoin.
            if _PH in c:
                ph_re = re.compile(
                    re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+"
                    + re.escape(_PH))
                out = []
                last = 0
                for m in ph_re.finditer(c):
                    if m.start() > last:
                        chunk = c[last:m.start()]
                        if chunk.strip():
                            out.append(text_transform(chunk))
                        else:
                            out.append(chunk)
                    out.append(m.group(0))
                    last = m.end()
                if last < len(c):
                    tail = c[last:]
                    if tail.strip():
                        out.append(text_transform(tail))
                    else:
                        out.append(tail)
                joined = "".join(out).strip()
                if joined:
                    parts.append(joined)
            else:
                content = text_transform(c)
                if content.strip():
                    parts.append(content.strip())

    # Image + caption bundling: when the unwrap produced a single
    # IMAGE placeholder plus one or more text parts, fold the first
    # text part into the IMG marker as its caption. Reuses the same
    # caption-cleaning step _process_image applies, so the caption
    # comes out as plain text (no «I»/«SC» leak) like any other IMG.
    if inner_registry is not None and len(parts) >= 2:
        ph_re = re.compile(re.escape(_PH) + r"ELEM:\d+" + re.escape(_PH))
        image_indices = [
            i for i, p in enumerate(parts)
            if ph_re.fullmatch(p.strip())
            and inner_registry.elements.get(p.strip(), ("",))[0] == "IMAGE"
        ]
        text_indices = [
            i for i, p in enumerate(parts)
            if not ph_re.fullmatch(p.strip())
            and p.strip()
        ]
        if len(image_indices) == 1 and text_indices:
            img_idx = image_indices[0]
            ph_id = parts[img_idx].strip()
            etype, eraw = inner_registry.elements[ph_id]
            # Case-insensitive: wikitext uses `[[File:…]]`, `[[Image:…]]`,
            # and (rarely) lowercase `[[image:…]]` (ABBEY vol 1 p. 44).
            fname_m = re.match(
                r"\[\[(?:File|Image):([^\]|]+)", eraw, re.IGNORECASE)
            if fname_m:
                filename = fname_m.group(1).strip()
                caption_idx = next(
                    (i for i in text_indices if i > img_idx), None)
                if caption_idx is not None:
                    # Caption is already through text_transform (cells
                    # were processed in _extract_cells). Apply the
                    # same _clean_text used by _process_image to
                    # strip any «I»/«SC»/etc. markers and produce
                    # plain figcaption text.
                    caption = _clean_text(parts[caption_idx].strip())
                    if caption:
                        img_marker = f"{{{{IMG:{filename}|{caption}}}}}"
                    else:
                        img_marker = f"{{{{IMG:{filename}}}}}"
                    # Preserve trailing parts (e.g. nested legend
                    # tables following the caption, attribution text)
                    # as siblings after the figure.  Without this the
                    # St Gall ground-plan legend on Abbey_3 would be
                    # dropped entirely when bundling fired.
                    trailing = [
                        parts[i] for i in range(len(parts))
                        if i != img_idx and i != caption_idx
                        and parts[i].strip()
                    ]
                    if trailing:
                        return "\n\n".join([img_marker, *trailing])
                    return img_marker

    return "\n\n".join(parts)


def _extract_subtable_values(table_text: str) -> list[str]:
    """Extract cell values from a nested sub-table (single-column layout)."""
    values = []
    for line in table_text.split("\n"):
        line = line.strip()
        if line.startswith("|-") or line.startswith("{|") or line == "|}":
            continue
        if line.startswith("|"):
            cell = line[1:].strip()
            # Strip attributes: everything before last |
            if "|" in cell:
                cell = cell.rpartition("|")[2].strip()
            # Strip {{Ts}} and other templates
            cell = re.sub(r"\{\{[^{}]*\}\}\s*", "", cell).strip()
            values.append(cell)
    return values


def _process_compound_table(raw: str, text_transform) -> str:
    """Process a data table with nested sub-tables in cells.

    These tables have parallel sub-tables (one per column) where each
    sub-table lists values vertically.  We zip the sub-table rows together
    to reconstruct the intended grid layout.

    Self-contained: works from raw wikitext, does not use the recursive
    extract/process pipeline, so it cannot affect other table types.
    """
    # Strip outer delimiters
    inner = re.sub(r"^\{\|[^\n]*\n?", "", raw)
    inner = re.sub(r"\n?\|\}\s*$", "", inner)

    # Split into outer rows on top-level |- only (not inside nested tables)
    outer_rows = []
    current = []
    depth = 0
    for line in inner.split("\n"):
        stripped = line.strip()
        if stripped.startswith("{|"):
            depth += 1
        elif stripped == "|}":
            depth -= 1
        if stripped.startswith("|-") and depth == 0:
            outer_rows.append("\n".join(current))
            current = []
        else:
            current.append(line)
    if current:
        outer_rows.append("\n".join(current))

    html_rows = []

    for row_text in outer_rows:
        # Check if this row contains nested sub-tables
        subtables = list(re.finditer(
            r"\{\|.*?\|\}", row_text, re.DOTALL))

        if subtables:
            # Extract values from each sub-table
            all_values = [_extract_subtable_values(m.group(0))
                          for m in subtables]
            n_rows_list = [len(v) for v in all_values]

            if n_rows_list and len(set(n_rows_list)) == 1 and n_rows_list[0] > 0:
                # Parallel sub-tables — zip into rows
                for i in range(n_rows_list[0]):
                    cells = []
                    for vs in all_values:
                        content = vs[i]
                        content = re.sub(r"&nbsp;", " ", content)
                        content = _strip_br(content)
                        content = content.strip()
                        if content and text_transform:
                            content = text_transform(content)
                        cells.append(f"<td>{content}</td>")
                    html_rows.append("<tr>" + "".join(cells) + "</tr>")
            else:
                # Unequal sub-tables — flatten each to <br>-joined content
                for m in subtables:
                    values = _extract_subtable_values(m.group(0))
                    content = "<br>".join(
                        text_transform(v) if text_transform and v.strip()
                        else v for v in values)
                    html_rows.append(f"<tr><td>{content}</td></tr>")
        else:
            # Regular row (no nested tables) — process normally
            cells_html = []
            for line in row_text.split("\n"):
                line = line.strip()
                if not line or line.startswith("|+"):
                    continue
                if not (line.startswith("|") or line.startswith("!")):
                    continue
                tag = "th" if line.startswith("!") else "td"

                # Strip {{Ts}} from cell lines
                cell_text = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "",
                                   line[1:])
                # Protect pipes inside remaining {{...}} templates (e.g.
                # {{brace2|4|l}}, {{sub|1}}) so the attr/content rpartition
                # below doesn't mis-split on a template-internal pipe.
                cell_text = re.sub(
                    r"\{\{[^}]*\}\}",
                    lambda m: m.group(0).replace("|", "\x04"),
                    cell_text,
                )
                # Split on || for multi-cell lines
                sep = "!!" if tag == "th" else "||"
                for cell in cell_text.split(sep):
                    # Strip attributes
                    if "|" in cell:
                        _, _, content = cell.rpartition("|")
                    else:
                        content = cell
                    content = content.replace("\x04", "|")
                    content = re.sub(r"\{\{[^{}]*\}\}", "", content)
                    content = re.sub(r"&nbsp;", " ", content)
                    content = _strip_br(content)
                    content = re.sub(r"<td[^>]*>", "", content,
                                     flags=re.IGNORECASE)
                    content = content.strip()
                    if content and text_transform:
                        content = text_transform(content)
                    cells_html.append(f"<{tag}>{content}</{tag}>")

            if cells_html:
                html_rows.append("<tr>" + "".join(cells_html) + "</tr>")

    if not html_rows:
        return ""

    return "\u00abHTMLTABLE:<table>" + "".join(html_rows) + "</table>\u00ab/HTMLTABLE\u00bb"


def _process_complex_table(inner: str, text_transform) -> str:
    """Convert a wiki table with rowspan/colspan to HTML.

    Strategy: each cell in wiki markup has the form
        {{ts|style}} rowspan=N colspan=M {{ts|style}}| content
    Everything before the last | is attributes; everything after is content.
    We keep only rowspan/colspan from the attributes and transform the content.
    Pipes inside {{...}} are protected so they don't confuse the split.

    Receives `inner` (delimiters already stripped, child elements replaced
    with placeholders) so that nested elements like <math> are preserved.
    """

    # Extract the wikitext table caption (`|+ TEXT` on its own line)
    # so we can render it inside the HTML table's <caption> element.
    # Without this the caption silently disappears (AFRICA's "BANTU
    # NEGROIDS", EXCHEQUER's "Revenue"/"Expenditure" / "Surplus", etc.).
    caption_html = ""
    cap_match = re.search(r"^\|\+\s*(.+?)$", inner, re.MULTILINE)
    if cap_match:
        cap_raw = cap_match.group(1).strip()
        cap_text = text_transform(cap_raw) if cap_raw else ""
        if cap_text:
            caption_html = f"<caption>{cap_text}</caption>"

    # Row split on `|-` wiki row separators — but only when `|-` is at
    # the start of a line. A `|-` in the middle of a line always means
    # something else (template arg like ``{{rotate|-90|…}}``, math
    # inline, etc.) and must not terminate a row. The old pattern
    # `\|-[^\n]*` ate templates that happened to contain a `|-`.
    rows = re.split(r"(?:^|\n)\|-[^\n]*", inner)
    html_rows = []

    for row in rows:
        # Merge continuation lines into the preceding cell: a wiki cell
        # can have content that spills onto subsequent lines (e.g.
        # `|attr|\n content\n more content`). Any non-empty line that
        # doesn't start with `|`, `!`, or `{|` belongs to the previous
        # cell.
        merged: list[str] = []
        for ln in row.split("\n"):
            stripped = ln.strip()
            if not stripped:
                continue
            if stripped.startswith(("|", "!")) or stripped == "{|":
                merged.append(ln)
            elif merged:
                merged[-1] = merged[-1].rstrip() + " " + stripped
            else:
                # orphan text before any cell — keep as-is
                merged.append(ln)

        cells_html = []
        for line in merged:
            line = line.strip()
            if not line or line.startswith("|+"):
                continue
            if not (line.startswith("|") or line.startswith("!")):
                continue
            tag = "th" if line.startswith("!") else "td"
            sep = "!!" if tag == "th" else "||"

            # Protect pipes inside {{...}} and [[...]] before any splitting
            prot = re.sub(r"\{\{[^}]*\}\}",
                          lambda m: m.group(0).replace("|", "\x04"), line[1:])
            prot = re.sub(r"\[\[[^\]]*\]\]",
                          lambda m: m.group(0).replace("|", "\x04"), prot)

            for cell in prot.split(sep):
                # Split attributes from content on the last real |
                if "|" in cell:
                    attr_part, _, content = cell.rpartition("|")
                    attr_part = attr_part.replace("\x04", "|")
                else:
                    attr_part = ""
                    content = cell
                content = content.replace("\x04", "|")

                # Extract structural attributes
                attrs = ""
                rs = re.search(r'rowspan\s*=\s*"?(\d+)"?', attr_part, re.IGNORECASE)
                cs = re.search(r'colspan\s*=\s*"?(\d+)"?', attr_part, re.IGNORECASE)
                if rs:
                    attrs += f' rowspan="{rs.group(1)}"'
                if cs:
                    attrs += f' colspan="{cs.group(1)}"'

                # Clean content
                # Convert [[Image:...|params]] to {{IMG:filename}}
                img_m = re.match(r"\s*\[\[(?:Image|File):([^|\]]+)[^\]]*\]\]\s*$",
                                 content, re.IGNORECASE)
                if img_m:
                    content = f"{{{{IMG:{img_m.group(1).strip()}}}}}"
                else:
                    content = re.sub(r"\[\[(?:Image|File):[^\]]*\]\]", "", content, flags=re.IGNORECASE)
                    content = re.sub(r"\{\{ditto(?:\|[^{}]*)?\}\}", "\u2033",
                                     content, flags=re.IGNORECASE)
                    content = re.sub(r"\{\{\.\.\.\}\}", "...", content)
                    content = _strip_br(content)
                    content = content.strip()
                    # Run text_transform FIRST so it can convert
                    # templates it knows about (``{{sfrac|…}}``,
                    # ``{{hi|…}}``, ``{{sc|…}}``, etc.) into their
                    # marker form.  Previously the catch-all
                    # ``\{\{[^{}]*\}\}`` strip ran first and ate every
                    # unlabelled template, dropping SHIPBUILDING's
                    # ``{{sfrac|…|Volume of Displacement|Length × …}}``
                    # entirely from the "Block coefficients or" cell.
                    if content:
                        content = text_transform(content)
                    # Strip any templates text_transform didn't handle.
                    content = re.sub(r"\{\{[^{}]*\}\}", "", content)
                cells_html.append(f"<{tag}{attrs}>{content}</{tag}>")

        if cells_html:
            html_rows.append("<tr>" + "".join(cells_html) + "</tr>")

    if not html_rows:
        return ""

    # Pull out leading colspan rows that contain images or captions —
    # these are header material that belongs above the table, not in it.
    preamble = []
    while html_rows:
        row = html_rows[0]
        # Check if every cell in this row has colspan (full-width row)
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL)
        has_colspan = 'colspan=' in row
        if has_colspan and len(cells) == 1:
            content = cells[0].strip()
            if content:
                preamble.append(content)
            html_rows.pop(0)
        else:
            break

    parts = []
    for p in preamble:
        parts.append("\n\n" + p + "\n\n")
    if html_rows:
        parts.append("\n\n\u00abHTMLTABLE:<table>" +
                     caption_html +
                     "".join(html_rows) + "</table>\u00ab/HTMLTABLE\u00bb\n\n")
    return "".join(parts)


def _process_ref(inner: str, text_transform) -> str:
    """Convert ref content to «FN:...«/FN» with clean text."""
    # Transform internal wiki markup (bold, italic, links)
    content = text_transform(inner)
    # Clean to plain text — footnotes should have no formatting markers
    content = _clean_text(content)
    return f"\u00abFN:{content}\u00ab/FN\u00bb"


def _process_image(inner: str, text_transform) -> str:
    """Convert image content (already stripped of [[File:...]]) to {{IMG:filename|clean caption}}."""
    # Check for external caption (from plate pages: image + caption on next line)
    ext_caption = ""
    if "|EXTCAP:" in inner:
        inner, ext_caption = inner.rsplit("|EXTCAP:", 1)

    parts = [p.strip() for p in inner.split("|")]
    filename = parts[0]

    # Extract caption (last non-keyword, non-size part)
    keywords = {"center", "left", "right", "thumb", "thumbnail", "frameless",
                "frame", "border", "upright", "none"}
    caption = ""
    for part in reversed(parts[1:]):
        lower = part.lower()
        if lower in keywords:
            continue
        if re.match(r"^\d+px$|^x\d+px$|^\d+x\d+px$", lower):
            continue
        if "=" in part:  # named parameter
            continue
        caption = part
        break

    # Use external caption if no inline caption
    if not caption and ext_caption:
        caption = ext_caption

    if caption:
        caption = text_transform(caption)
        caption = _clean_text(caption)
        return f"{{{{IMG:{filename}|{caption}}}}}"
    return f"{{{{IMG:{filename}}}}}"


def _process_image_float(inner: str, text_transform) -> str:
    """Convert img float content to {{IMG:filename|caption}}.

    Inner is the content between {{ and }}, e.g.:
    'img float |file=Foo.jpg |cap=A caption |width=240px'
    """
    file_m = re.search(r"\|file=([^|]+)", inner)
    cap_m = re.search(r"\|cap=((?:[^|{}]|\{\{[^{}]*\}\})+)", inner)
    if not file_m:
        return ""
    filename = file_m.group(1).strip()
    caption = ""
    if cap_m:
        caption = cap_m.group(1).strip()
        caption = text_transform(caption)
        caption = _clean_text(caption)
    if caption:
        return f"{{{{IMG:{filename}|{caption}}}}}"
    return f"{{{{IMG:{filename}}}}}"


_CSS_CROP_RE = re.compile(
    r"\{\{Css image crop\s*\n(.*?)\}\}", re.DOTALL | re.IGNORECASE
)


def _parse_crop_param(body: str, name: str) -> str:
    m = re.search(rf"\|{name}\s*=\s*([^\n|]*)", body, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _process_djvu_crop(raw: str, text_transform, context: dict) -> str:
    """Process a table containing a {{Css image crop}} template.

    Extracts the crop filename and caption from the table, producing
    {{IMG:djvu_volNN_pageNNNN_cropN.jpg|caption}}.

    Crop indices are tracked in context['_djvu_crop_counters'] to match
    the order used by tools/download_djvu_crops.py.
    """
    crop_m = _CSS_CROP_RE.search(raw)
    if not crop_m:
        return ""

    body = crop_m.group(1)
    image = _parse_crop_param(body, "Image")
    if not image:
        return ""

    # Build the local filename
    if image.endswith(".djvu"):
        page_str = _parse_crop_param(body, "Page")
        if not page_str:
            return ""
        page = int(page_str)
        vol_m = re.search(r"Volume (\d+)", image)
        vol = int(vol_m.group(1)) if vol_m else context.get("volume", 0)
        counters = context.setdefault("_djvu_crop_counters", {})
        key = (vol, page)
        idx = counters.get(key, 0)
        counters[key] = idx + 1
        filename = f"djvu_vol{vol:02d}_page{page:04d}_crop{idx}.jpg"
    else:
        filename = image.replace(" ", "_")

    # Extract caption from the table (everything that isn't the crop template
    # or wiki table markup)
    caption_text = raw[:crop_m.start()] + raw[crop_m.end():]
    # Strip table delimiters and markup
    caption_text = re.sub(r"^\{\|[^\n]*\n?", "", caption_text)
    caption_text = re.sub(r"\n?\|\}\s*$", "", caption_text)
    caption_text = re.sub(r"^\|[\-\+].*$", "", caption_text, flags=re.MULTILINE)
    caption_text = re.sub(r"^\|(?:colspan[^|]*\|)?", "", caption_text, flags=re.MULTILINE)
    caption_text = re.sub(r"^\!", "", caption_text, flags=re.MULTILINE)
    # Collapse to single line
    caption_text = re.sub(r"\s*<br\s*/?>", " ", caption_text, flags=re.IGNORECASE)
    caption_text = re.sub(r"\s*\n\s*", " ", caption_text)
    caption_text = re.sub(r"  +", " ", caption_text).strip()

    if caption_text:
        caption_text = text_transform(caption_text)
        caption_text = _clean_text(caption_text)
        return f"\n\n{{{{IMG:{filename}|{caption_text}}}}}\n\n"
    return f"\n\n{{{{IMG:{filename}}}}}\n\n"


# Static lookup: (volume, page) → chart image filename
_CHART2_IMAGES = {
    (1, 124): "chart2_vol01_page0124.jpg",
    (21, 573): "chart2_vol21_page0573.jpg",
    (23, 945): "chart2_vol23_page0945.jpg",
    (24, 271): "chart2_vol24_page0271.jpg",
    (28, 952): "chart2_vol28_page0952.jpg",
}


def _process_chart2(raw: str, context: dict) -> str:
    """Replace a chart2 genealogical tree with a pre-cropped page scan image.

    The 5 chart2 blocks in the encyclopedia have been manually cropped
    from DjVu page scans and saved as chart2_volNN_pageNNNN.jpg.
    """
    vol = context.get("volume", 0)
    # Try all known charts for this volume
    for (v, p), filename in _CHART2_IMAGES.items():
        if v == vol:
            return f"\n\n{{{{IMG:{filename}|Genealogical table}}}}\n\n"
    # Unknown chart — strip rather than crash
    return ""


def _process_poem(inner: str, text_transform) -> str:
    """Convert poem content to {{VERSE:...}VERSE}."""
    content = text_transform(inner)
    return "{{VERSE:" + content + "}VERSE}"


def _process_table(inner: str, text_transform,
                   inner_registry: ElementRegistry | None = None) -> str:
    """Convert table rows to {{TABLE:...}TABLE} with clean cells.

    The table processor handles STRUCTURE: rows, cell boundaries, attributes.
    Each cell's content is processed through text_transform — cells are
    elements in their own right.
    """
    # Convert <br> to space before cell parsing (and strip soft-hyphen
    # line breaks, e.g. "Circum-<br>ference" → "Circumference").
    inner = _strip_br(inner)

    # Cell attribute pattern
    _ATTR = re.compile(
        r"^(?:colspan|rowspan|width|style|align|valign|class|"
        r"cellpadding|nowrap|border|bgcolor|height)[\s=|]",
        re.IGNORECASE,
    )

    def _extract_cells(row_text):
        """Extract data cells from a row, stripping attributes, processing each."""
        # Strip cell-styling templates ({{Ts|...}} / {{ts|...}}) — these are
        # cell attributes, not content.  Leaving them in would produce
        # phantom cells once their internal `|` is re-protected.
        row_text = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}\s*", "", row_text)
        # Protect {{...}} and placeholders from pipe-splitting
        protected = re.sub(r"\{\{[^}]*\}\}", lambda m: m.group(0).replace("|", "\x04"), row_text)
        protected = re.sub(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH),
                           lambda m: m.group(0).replace("|", "\x04"), protected)

        # Normalize `||` (MediaWiki same-line cell shorthand) to `\n|`
        # so it's treated as a single cell separator, not two.
        protected = protected.replace("||", "\n|")

        # Split cells on `|` at line starts.
        raw_cells = re.findall(r"\|([^|\n]*)", protected)
        raw_cells = [c.replace("\x04", "|") for c in raw_cells]

        cells = []
        for c in raw_cells:
            s = c.strip()
            if s in ("}", "{|"):
                continue
            if s and _ATTR.match(s):
                continue
            # Process cell content through text_transform (empty → " ")
            cells.append(text_transform(s) if s else " ")
        return cells

    # Tiny inline tables (few cells, short content) → unwrap to inline text.
    # Only for single-row tables with no row separators and no block-level
    # child elements (poems produce VERSE blocks that need table wrapping).
    _BLOCK_TYPES = {"POEM", "TABLE", "HTML_TABLE"}
    has_block_child = inner_registry and any(
        ctype in _BLOCK_TYPES for ctype, _ in inner_registry.elements.values())
    if "|-" not in inner and not has_block_child:
        all_cells = _extract_cells(inner)
        content_cells = [c for c in all_cells if c.strip()]
        if len(content_cells) <= 4 and sum(len(c) for c in all_cells) < 120:
            return " ".join(content_cells)

    # Image + caption wikitable: row 1 contains a single image placeholder
    # and row 2+ contains caption / attribution text. Bundle into a single
    # {{IMG:filename|caption}} so the image renders with its caption inside
    # the figure rather than leaving the caption row as a duplicate paragraph
    # below the figure (e.g. SEWING MACHINES Fig. 2). Skips trailing
    # attribution rows (typically beginning "From …" / "After …").
    if "|-" in inner and inner_registry is not None:
        ph_re = re.compile(re.escape(_PH) + r"ELEM:\d+" + re.escape(_PH))
        rows_filtered = [r for r in re.split(r"\|-[^\n]*", inner) if r.strip()]
        if len(rows_filtered) >= 2:
            row1_cells = _extract_cells(rows_filtered[0])
            if (len(row1_cells) == 1
                    and ph_re.fullmatch(row1_cells[0].strip())):
                ph_id = row1_cells[0].strip()
                etype, eraw = inner_registry.elements.get(ph_id, ("", ""))
                if etype == "IMAGE":
                    fname_m = re.match(
                        r"\[\[(?:File|Image):([^\]|]+)",
                        eraw, re.IGNORECASE)
                    if fname_m:
                        filename = fname_m.group(1).strip()
                        # Take row 2 as the primary caption.
                        row2_cells = _extract_cells(rows_filtered[1])
                        caption = " ".join(c.strip() for c in row2_cells
                                           if c.strip())
                        if caption:
                            return f"{{{{IMG:{filename}|{caption}}}}}"
                        return f"{{{{IMG:{filename}}}}}"

    # Single-column tables (1 cell per row) are text blocks, not data tables.
    # Render as preformatted text with line breaks preserved.
    if "|-" in inner:
        raw_rows = re.split(r"\|-[^\n]*", inner)
        all_single = True
        text_lines = []
        for raw_row in raw_rows:
            cells = _extract_cells(raw_row)
            content = [c for c in cells if c.strip()]
            if len(content) == 0:
                continue
            if len(content) > 1:
                all_single = False
                break
            text_lines.append(content[0])
        if all_single and text_lines:
            joined = "\n".join(text_lines)
            return f"\u00abPRE:{joined}\u00ab/PRE\u00bb"

    # Check for image-layout table (plate pages: grid of images + captions)
    if _PH in inner:
        # Count child placeholders that are images vs text content
        placeholders = re.findall(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH), inner)
        non_placeholder = re.sub(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH), "", inner)
        # Strip wiki table markup and whitespace, but keep actual cell text
        non_placeholder = re.sub(r"[-|{}\n]", " ", non_placeholder)
        non_placeholder = re.sub(r"\b(?:align|valign|colspan|rowspan|style|width|cellpadding|cellspacing|center|right|left|top|bottom)\b", "", non_placeholder, flags=re.IGNORECASE)
        non_placeholder = re.sub(r'[="]+', "", non_placeholder)
        non_placeholder = re.sub(r"\s+", " ", non_placeholder).strip()
        if len(placeholders) >= 2 and len(non_placeholder) < len(placeholders) * 20:
            # Mostly images — extract placeholders and any caption text
            parts = []
            for ph in placeholders:
                parts.append(ph)
            # Find numbered captions in the remaining text
            for m in re.finditer(r"(\d+)\.\s*([A-Z][A-Z\s,.:;()\-']+)", inner):
                parts.append(f"{m.group(1)}. {m.group(2).strip()}")
            return "\n\n".join(parts)

    # Check for brace layout (poem + translation side by side)
    if "brace" in inner.lower() and "rowspan" in inner.lower():
        result = _process_brace_table(inner, text_transform)
        if result:
            return result

    # Check for verse-layout table: 2 columns where col 1 is just punctuation
    # (quote marks) and col 2 has the actual verse text.
    raw_rows_v = re.split(r"\|-[^\n]*", inner)
    verse_rows_v = []
    is_verse_layout = len(raw_rows_v) >= 1
    for rv in raw_rows_v:
        cells_v = _extract_cells(rv)
        if not cells_v:
            continue
        if len(cells_v) == 2:
            col1 = cells_v[0].strip()
            col2 = cells_v[1].strip()
            # Col 1 must be only punctuation/quotes (or empty)
            if col1 and not re.match(r'^[\s"\'\u201c\u201d\u2018\u2019,.\-;:—]+$', col1):
                is_verse_layout = False
                break
            if col2:
                verse_rows_v.append((col1, col2))
        elif len(cells_v) == 1 and not cells_v[0].strip():
            continue  # empty row
        else:
            is_verse_layout = False
            break
    if is_verse_layout and verse_rows_v:
        # Combine leading/trailing punctuation with verse lines
        lines = []
        for col1, col2 in verse_rows_v:
            line = f"{col1}{col2}" if col1 else col2
            if text_transform:
                line = text_transform(line)
            lines.append(line)
        return "\n\n{{VERSE:" + "\n".join(lines) + "}VERSE}\n\n"

    # Check for structural formula (monospaced, spatial layout)
    if _is_structural_formula(inner):
        return _format_structural_formula(inner)

    # Check for table caption (|+ ...)
    caption = ""
    cap_match = re.search(r"\|\+\s*(.*?)(?:\n|$)", inner)
    if cap_match:
        caption = re.sub(r"\{\{[^{}]*\}\}", "", cap_match.group(1)).strip()

    # Split into rows on |- separators
    raw_rows = re.split(r"\|-[^\n]*", inner)

    text_rows = []
    image_parts = []

    for raw_row in raw_rows:
        # Skip caption rows
        if "|+" in raw_row:
            continue

        # Preserve any child element placeholders outside cells
        for line in raw_row.split("\n"):
            stripped_line = line.strip()
            if _PH in stripped_line and not stripped_line.startswith("|"):
                image_parts.append(stripped_line)

        # Extract and process cells
        cells = _extract_cells(raw_row)

        # Separate image-only cells from data cells — but only when
        # the entire row is images (plate layout).  If a row mixes
        # images and text (e.g. score + description), keep them together.
        img_cells = [c for c in cells if re.match(r"^\s*\{\{IMG:[^}]+\}\}\s*$", c)]
        non_img_cells = [c for c in cells if not re.match(r"^\s*\{\{IMG:[^}]+\}\}\s*$", c)]

        if img_cells and not non_img_cells:
            # All-image row — separate for plate layout
            image_parts.extend(c.strip() for c in img_cells)
            continue

        data_cells = cells  # keep images and text together

        # Handle <br> in cells
        br_cells = [i for i, c in enumerate(data_cells)
                    if re.search(r"<br\s*/?>", c, re.IGNORECASE)]
        if len(br_cells) >= 2:
            # Multi-row data: expand
            split = [re.split(r"<br\s*/?>", c, flags=re.IGNORECASE)
                     for c in data_cells]
            max_sub = max(len(s) for s in split)
            for s in split:
                while len(s) < max_sub:
                    s.append("")
            for i in range(max_sub):
                sub = [s[i].strip() for s in split]
                if any(sub):
                    text_rows.append(" | ".join(sub))
        elif br_cells:
            # Single-cell br: collapse to space (strip soft-hyphen breaks)
            data_cells = [_strip_br(c).strip() for c in data_cells]
            text_rows.append(" | ".join(data_cells))
        else:
            text_rows.append(" | ".join(data_cells))

    # Strip spacer columns from colspan tables only.  These tables have
    # group headers spanning multiple data columns, with empty separator
    # columns between groups.  The colspan attribute in the raw markup
    # is the reliable signal — no single-header table uses colspan.
    if "colspan" in inner and len(text_rows) >= 4:
        split_rows = [r.split(" | ") for r in text_rows]
        ncols = max(len(r) for r in split_rows)
        # Identify data rows vs section-divider rows.  Data rows repeat
        # 3+ times (e.g. 1897, 1901, 1906) at a consistent column count.
        # Section dividers (group labels) repeat fewer times.
        from collections import Counter
        col_counts = Counter(len(r) for r in split_rows)
        # Column counts with 3+ occurrences are data row groups.
        # Counts with exactly 2 are sub-header + section-divider pairs.
        # Use 3+ as the threshold to separate data from labels.
        data_col_groups = {n for n, cnt in col_counts.items() if cnt >= 3}
        if not data_col_groups:
            # Fallback: use the most common count with 2+
            data_col_groups = {col_counts.most_common(1)[0][0]}
            if col_counts.most_common(1)[0][1] < 2:
                data_col_groups = set()

        # For each group, find columns empty in ALL rows of that group
        empty_by_group: dict[int, set[int]] = {}
        for ncols_g in data_col_groups:
            group_rows = [r for r in split_rows if len(r) == ncols_g]
            empty = set()
            for j in range(ncols_g):
                if all(not r[j].strip() for r in group_rows):
                    empty.add(j)
            if empty:
                empty_by_group[ncols_g] = empty

        if empty_by_group:
            new_rows = []
            for cells in split_rows:
                nc = len(cells)
                if nc in empty_by_group:
                    new_rows.append(" | ".join(
                        cells[j] for j in range(nc)
                        if j not in empty_by_group[nc]
                    ))
                else:
                    # Section-divider row (group labels from colspan).
                    # Strip empty cells, then pad to match the stripped
                    # data column count so labels align over their groups.
                    content_cells = [c for c in cells if c.strip()]
                    if content_cells and empty_by_group:
                        # Find the stripped data column count
                        target = max(empty_by_group)
                        stripped_ncols = target - len(empty_by_group[target])
                        if stripped_ncols < 2:
                            new_rows.append(" | ".join(
                                c for c in cells if c.strip()))
                            continue
                        # Check if first raw cell is empty (no row label)
                        has_label = bool(cells[0].strip()) if cells else True
                        if has_label:
                            # First content cell is the row label;
                            # remaining cells are group headers
                            n_groups = len(content_cells) - 1
                            data_cols = stripped_ncols - 1
                            span = data_cols // n_groups if n_groups > 0 else 1
                            padded = [""] * stripped_ncols
                            padded[0] = content_cells[0]
                            for k, lbl in enumerate(content_cells[1:]):
                                pos = 1 + k * span
                                if pos < stripped_ncols:
                                    padded[pos] = lbl
                        else:
                            # No row label on this row — all content cells are
                            # group headers.  But a label column may still exist
                            # (populated in the sub-header row, e.g. "Year.").
                            n_groups = len(content_cells)
                            data_cols = stripped_ncols - 1  # assume label column
                            if n_groups > 0 and data_cols >= n_groups:
                                span = data_cols // n_groups
                                padded = [""] * stripped_ncols
                                for k, lbl in enumerate(content_cells):
                                    pos = 1 + k * span
                                    if pos < stripped_ncols:
                                        padded[pos] = lbl
                            else:
                                # No label column — groups fill all columns
                                span = stripped_ncols // n_groups if n_groups > 0 else 1
                                padded = [""] * stripped_ncols
                                for k, lbl in enumerate(content_cells):
                                    pos = k * span
                                    if pos < stripped_ncols:
                                        padded[pos] = lbl
                        new_rows.append(" | ".join(padded))
                    else:
                        new_rows.append(" | ".join(
                            c for c in cells if c.strip()
                        ))
            text_rows = new_rows

    # Assemble output
    parts = []
    if image_parts:
        parts.extend(image_parts)
    if text_rows:
        header = "H" if caption else ""
        parts.append("{{TABLE" + header + ":" + "\n".join(text_rows) + "}TABLE}")

    if parts:
        return "\n\n".join(parts)
    return ""


def _is_html_illustration_wrapper(
    raw: str, inner_registry: ElementRegistry | None
) -> bool:
    """Detect HTML tables that wrap an image+caption for layout.

    EB1911 Wikisource uses HTML tables like:

        <table ... summary="Illustration">
          <tr><td>[[File:...]]</td></tr>
          <tr><td>Fig. 1. caption text.</td></tr>
        </table>

    Signals:
      - summary="Illustration" attribute on the opening <table> tag, OR
      - contains exactly one IMAGE child and the non-image cells are short
        caption text.
    """
    if re.search(r'summary\s*=\s*"?Illustration', raw, re.IGNORECASE):
        return True
    if inner_registry is None:
        return False
    child_types = [t for t, _ in inner_registry.elements.values()]
    n_images = sum(1 for t in child_types if t == "IMAGE")
    if n_images < 1:
        return False
    # No other block-level children (nested tables etc.)
    if any(t not in ("IMAGE", "REF", "MATH") for t in child_types):
        return False
    return True


def _unwrap_html_illustration(
    inner: str, text_transform, inner_registry: ElementRegistry | None
) -> str:
    """Unwrap an HTML illustration table to a bundled IMG+caption.

    Collects every image child and every caption cell, then emits
    `{{IMG:filename|caption}}` where the caption is the concatenated
    non-image cell text. This lets the viewer render the caption under
    the image instead of as a detached paragraph.

    For single-image illustrations we bypass the placeholder mechanism
    entirely and emit the final IMG tag directly — the placeholder
    substitution step in _process_element won't find the placeholder in
    the output, so it simply does nothing for this child.

    Falls back to emitting placeholders + caption paragraph if there's
    no single image or no inner_registry.
    """
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", inner, re.DOTALL | re.IGNORECASE)

    image_cells: list[str] = []    # cell text containing an IMAGE placeholder
    caption_parts: list[str] = []  # plain-text caption cells
    for row in rows:
        cells = re.findall(
            r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE)
        for cell in cells:
            c = re.sub(r"<[^>]+>", " ", cell)
            c = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}", "", c)
            c = re.sub(r"\s+", " ", c).strip()
            if not c:
                continue
            if _PH in c:
                # Cell contains a placeholder (image). Transform any
                # surrounding text (entity decoding, bold/italic) but
                # preserve the placeholder verbatim for substitution.
                ph_re = re.compile(
                    re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+"
                    + re.escape(_PH))
                out = []
                last = 0
                for m in ph_re.finditer(c):
                    if m.start() > last:
                        chunk = c[last:m.start()]
                        if chunk.strip():
                            out.append(text_transform(chunk))
                        else:
                            out.append(chunk)
                    out.append(m.group(0))
                    last = m.end()
                if last < len(c):
                    tail = c[last:]
                    if tail.strip():
                        out.append(text_transform(tail))
                    else:
                        out.append(tail)
                image_cells.append("".join(out))
            else:
                caption_parts.append(text_transform(c))

    caption_text = " ".join(p for p in caption_parts if p).strip()

    # Single-image case: emit the IMG tag directly with caption bundled.
    if len(image_cells) == 1 and inner_registry is not None:
        cell = image_cells[0]
        m = re.search(re.escape(_PH) + r"ELEM:\d+" + re.escape(_PH), cell)
        if m:
            key = m.group(0)
            if key in inner_registry.elements:
                img_type, img_raw = inner_registry.elements[key]
                if img_type == "IMAGE":
                    # Inject the caption via EXTCAP so _process_image bundles it.
                    if caption_text:
                        new_raw = img_raw + "\n\n" + caption_text
                    else:
                        new_raw = img_raw
                    return _process_image_from_raw(new_raw, text_transform)

    # Fallback: paragraph-style (images as placeholders, captions below)
    parts: list[str] = list(image_cells)
    if caption_text:
        parts.append(caption_text)
    return "\n\n".join(parts) if parts else ""


def _process_image_from_raw(raw: str, text_transform) -> str:
    """Convenience: strip `[[File:...]]` and call _process_image."""
    m = re.match(r"\[\[(?:File|Image):(.+)\]\](?:\s*\n\n?(.+))?$",
                 raw, re.IGNORECASE | re.DOTALL)
    if not m:
        return raw
    inner = m.group(1)
    ext_caption = m.group(2)
    if ext_caption:
        inner = inner + "|EXTCAP:" + ext_caption
    return _process_image(inner, text_transform)


def _process_html_table(
    raw: str,
    inner: str,
    text_transform,
    inner_registry: ElementRegistry | None,
) -> str:
    """Convert HTML table content to either an unwrapped illustration,
    a {{TABLE:...}TABLE} data table, or an HTMLTABLE marker when
    rowspan/colspan need to be preserved."""
    # Illustration wrapper — unwrap to IMG + caption
    if _is_html_illustration_wrapper(raw, inner_registry):
        return _unwrap_html_illustration(inner, text_transform, inner_registry)

    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", inner, re.DOTALL | re.IGNORECASE)
    if not rows:
        # No <tr> wrappers (e.g. HYDRAULICS: `<table><td>...</td></table>`
        # with td directly under table). Try to pull out <td> cells; if
        # none, strip and run the plain content through text_transform so
        # italic/bold/entities get converted.
        cells = re.findall(
            r"<t[dh][^>]*>(.*?)</t[dh]>",
            inner, re.DOTALL | re.IGNORECASE)
        if cells:
            parts = []
            for c in cells:
                c = _strip_br(c)
                c = re.sub(r"<[^>]+>", " ", c)
                c = re.sub(r"\s+", " ", c).strip()
                if c:
                    parts.append(text_transform(c))
            return " | ".join(parts)
        text = re.sub(r"<[^>]+>", " ", inner)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            text = text_transform(text)
        return text

    parsed_rows = []
    has_header = False
    has_span = False
    for row in rows:
        if "<th" in row.lower():
            has_header = True
        matches = re.findall(
            r"<(t[dh])([^>]*)>(.*?)</\1>",
            row, re.DOTALL | re.IGNORECASE)
        if not matches:
            continue
        parsed = []
        for tag, attrs, cell in matches:
            rs = re.search(r'rowspan\s*=\s*"?(\d+)"?', attrs, re.IGNORECASE)
            cs = re.search(r'colspan\s*=\s*"?(\d+)"?', attrs, re.IGNORECASE)
            rowspan = int(rs.group(1)) if rs else 1
            colspan = int(cs.group(1)) if cs else 1
            if rowspan > 1 or colspan > 1:
                has_span = True
            c = _strip_br(cell)
            c = re.sub(r"<[^>]+>", " ", c)
            c = re.sub(r"\s+", " ", c).strip()
            if c:
                c = text_transform(c)
            parsed.append((tag.lower(), rowspan, colspan, c))
        if parsed:
            parsed_rows.append(parsed)

    if not parsed_rows:
        return ""

    if has_span:
        html_rows = []
        for parsed in parsed_rows:
            cells_html = []
            for tag, rowspan, colspan, content in parsed:
                attrs = ""
                if rowspan > 1:
                    attrs += f' rowspan="{rowspan}"'
                if colspan > 1:
                    attrs += f' colspan="{colspan}"'
                cells_html.append(f"<{tag}{attrs}>{content}</{tag}>")
            html_rows.append("<tr>" + "".join(cells_html) + "</tr>")
        return ("\u00abHTMLTABLE:<table>" +
                "".join(html_rows) +
                "</table>\u00ab/HTMLTABLE\u00bb")

    text_rows = []
    for parsed in parsed_rows:
        cells = [content for _, _, _, content in parsed if content]
        if cells:
            text_rows.append(" | ".join(cells))
    if text_rows:
        header = "H" if has_header else ""
        return "{{TABLE" + header + ":" + "\n".join(text_rows) + "}TABLE}"
    return ""


def _process_brace_table(inner: str, text_transform) -> str | None:
    """Handle tables with {{brace}} + rowspan used for poem/translation layout.

    Pattern: left column has verse lines (one per row), middle has a brace,
    right column has a merged translation cell.  Output as verse + translation.
    """
    rows = re.split(r"\|-[^\n]*", inner)

    left_lines = []
    right_text = ""

    for row in rows:
        # Strip templates and attributes
        cleaned = re.sub(r"\{\{[^{}]*\}\}", "", row)
        cells = re.findall(r"\|([^|\n]+)", cleaned)
        cells = [c.strip() for c in cells
                 if c.strip()
                 and not re.match(
                     r"^(?:colspan|rowspan|width|style|align|valign|class|"
                     r"cellpadding|nowrap|border|bgcolor|height)[\s=|]",
                     c.strip(), re.IGNORECASE)
                 and c.strip() not in ("}", "{|")]

        for cell in cells:
            # Skip brace artifacts and empty cells
            if not cell or len(cell) < 2:
                continue
            # The right-side translation tends to be the longest cell
            if len(cell) > 40 and not right_text:
                right_text = text_transform(cell)
            elif len(cell) > 2:
                left_lines.append(text_transform(cell))

    if not left_lines:
        return None

    # Build verse block with translation
    verse = "{{VERSE:" + "\n".join(left_lines) + "}VERSE}"
    if right_text:
        return verse + "\n\n" + right_text
    return verse


def _is_structural_formula(text: str) -> bool:
    """Detect tables that represent structural chemical formulas.

    Structural formulas use spatial arrangement of short cells with
    dashes, dots, pipes, and chemical symbols.  They typically have
    many rows, very short cell content, and characters like ─ │ ╲ ╱.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) < 6:
        return False
    # Need many short pipe-cells AND structural characters
    short_cells = sum(1 for l in lines
                      if l.startswith("|") and len(l) < 8)
    has_structural = bool(re.search(r"[─│╲╱\\\/\.\-]{3,}", text))
    return short_cells > len(lines) * 0.6 and has_structural


def _format_structural_formula(text: str) -> str:
    """Convert a structural formula table to a PRE block."""
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("|"):
            line = line[1:].strip()
        if line and line not in ("|-", "}", "{|"):
            lines.append(line)
    content = "\n".join(lines)
    return f"\u00abPRE:{content}\u00ab/PRE\u00bb"


# ── Public API ────────────────────────────────────────────────────────

def process_elements(text: str, text_transform, context: dict) -> str:
    """Extract, process, and reassemble all embedded elements.

    Args:
        text: raw wikitext (may contain tables, images, footnotes, etc.)
        text_transform: function that transforms plain wikitext to marker format
        context: dict with 'volume', 'page_number' for score lookups

    Returns:
        text with all embedded elements processed to their final form
    """
    extracted, registry = extract(text)

    # Transform the body text (everything between elements)
    extracted = text_transform(extracted)

    # Process each element (recursion handles nesting)
    processed_map = {}
    for key, (element_type, raw) in registry.elements.items():
        processed_map[key] = _process_element(
            element_type, raw, text_transform, context)

    # Substitute all processed elements — repeat until stable
    # (handles cross-element references: table placeholder inside a ref)
    result = extracted
    for _pass in range(3):  # max 3 passes for deeply nested cross-refs
        changed = False
        for key, processed in processed_map.items():
            if key in result:
                result = result.replace(key, processed)
                changed = True
            # Also check if the placeholder appears inside other processed elements
            for other_key in processed_map:
                if key in processed_map[other_key]:
                    processed_map[other_key] = processed_map[other_key].replace(
                        key, processed)
        if not changed:
            break

    return result

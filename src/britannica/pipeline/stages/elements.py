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
    """Stores extracted elements keyed by placeholder strings."""
    elements: dict[str, tuple[str, str]] = field(default_factory=dict)
    _counter: int = 0

    def add(self, element_type: str, raw: str) -> str:
        """Add an element to the registry, return its placeholder."""
        self._counter += 1
        key = f"{_PH}ELEM:{self._counter}{_PH}"
        self.elements[key] = (element_type, raw)
        return key


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
    ("IMAGE_FLOAT", re.compile(
        r"\{\{(?:img float|figure|FI)\s*\|(?:[^{}]|\{\{[^{}]*\}\})*\}\}",
        re.DOTALL | re.IGNORECASE), 0),
    ("IMAGE", re.compile(
        r"\[\[(?:File|Image):([^\]]+)\]\]"
        r"(?:\s*\n\n?(\{\{sc\|Fig\.[^}]*\}\}[^\n]*|\d+\.\s*[A-Z][^\n]+))?",
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

        # Find the balanced |} by tracking depth
        depth = 0
        i = idx
        found = False
        while i < len(text) - 1:
            if text[i:i+2] == "{|":
                depth += 1
                i += 2
            elif text[i:i+2] == "|}":
                depth -= 1
                if depth == 0:
                    # Found the balanced close
                    table_text = text[idx:i+2]
                    # Classify at extraction time
                    if re.search(r"\{\{Css image crop", table_text, re.IGNORECASE):
                        etype = "DJVU_CROP"
                    elif _is_compound_table(table_text):
                        etype = "COMPOUND_TABLE"
                    else:
                        etype = "TABLE"
                    placeholder = registry.add(etype, table_text)
                    text = text[:idx] + placeholder + text[i+2:]
                    found = True
                    break
                i += 2
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
        if table_kind == "EQUATION_LAYOUT":
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

    # NOW reinsert processed children into the result
    for key, processed_child in processed_children.items():
        result = result.replace(key, processed_child)

    return result


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
    if _is_equation_layout(inner, inner_registry):
        return "EQUATION_LAYOUT"
    return "DATA_TABLE"


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
        return True
    if "IMAGE" in child_types:
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
            # Don't transform placeholders — they'll be substituted later
            if _PH in c:
                parts.append(c)
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
            fname_m = re.match(r"\[\[(?:File|Image):([^\]|]+)", eraw)
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
                        return f"{{{{IMG:{filename}|{caption}}}}}"
                    return f"{{{{IMG:{filename}}}}}"

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
                        content = re.sub(r"<br\s*/?>", " ", content,
                                         flags=re.IGNORECASE)
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
                # Split on || for multi-cell lines
                sep = "!!" if tag == "th" else "||"
                for cell in cell_text.split(sep):
                    # Strip attributes
                    if "|" in cell:
                        _, _, content = cell.rpartition("|")
                    else:
                        content = cell
                    content = re.sub(r"\{\{[^{}]*\}\}", "", content)
                    content = re.sub(r"&nbsp;", " ", content)
                    content = re.sub(r"<br\s*/?>", " ", content,
                                     flags=re.IGNORECASE)
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

    rows = re.split(r"\|-[^\n]*", inner)
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
                    content = re.sub(r"\{\{sc\|([^{}]*)\}\}", r"\1", content, flags=re.IGNORECASE)
                    content = re.sub(r"\{\{[^{}]*\}\}", "", content)
                    content = re.sub(r"<br\s*/?>", " ", content, flags=re.IGNORECASE)
                    content = content.strip()
                    if content:
                        content = text_transform(content)
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
    # Convert <br> to space before cell parsing
    inner = re.sub(r"<br\s*/?>", " ", inner, flags=re.IGNORECASE)

    # Cell attribute pattern
    _ATTR = re.compile(
        r"^(?:colspan|rowspan|width|style|align|valign|class|"
        r"cellpadding|nowrap|border|bgcolor|height)[\s=|]",
        re.IGNORECASE,
    )

    def _extract_cells(row_text):
        """Extract data cells from a row, stripping attributes, processing each."""
        # Protect {{...}} and placeholders from pipe-splitting
        protected = re.sub(r"\{\{[^}]*\}\}", lambda m: m.group(0).replace("|", "\x04"), row_text)
        protected = re.sub(re.escape(_PH) + r"[^" + re.escape(_PH) + r"]+" + re.escape(_PH),
                           lambda m: m.group(0).replace("|", "\x04"), protected)

        # Split cells: each | starts a cell. Handle both same-line (||)
        # and separate-line (|\n|) formats.  An empty cell (| followed
        # immediately by \n or |) produces an empty string.
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
                        r"\[\[(?:File|Image):([^\]|]+)", eraw)
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
            # Single-cell br: collapse to space
            data_cells = [re.sub(r"<br\s*/?>", " ", c,
                                 flags=re.IGNORECASE).strip()
                          for c in data_cells]
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
                image_cells.append(c)
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
    """Convert HTML table content to either an unwrapped illustration
    or a {{TABLE:...}TABLE} data table."""
    # Illustration wrapper — unwrap to IMG + caption
    if _is_html_illustration_wrapper(raw, inner_registry):
        return _unwrap_html_illustration(inner, text_transform, inner_registry)

    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", inner, re.DOTALL | re.IGNORECASE)
    if not rows:
        # No rows found — just strip all HTML and return content
        text = re.sub(r"<[^>]+>", " ", inner)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    text_rows = []
    has_header = False
    for row in rows:
        if "<th" in row.lower():
            has_header = True
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL | re.IGNORECASE)
        if cells:
            cleaned = []
            for cell in cells:
                c = re.sub(r"<[^>]+>", " ", cell)
                c = re.sub(r"\s+", " ", c).strip()
                if c:
                    cleaned.append(text_transform(c))
            if cleaned:
                text_rows.append(" | ".join(cleaned))

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

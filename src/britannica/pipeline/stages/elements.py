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
        r"(?:\s*\n\n?(\{\{sc\|Fig\.[^}]*\}\}[^\n]+|\d+\.\s*[A-Z][^\n]+))?",
        re.IGNORECASE), 0),
    ("HIEROGLYPH", re.compile(
        r"\{\{hieroglyph\|([^{}]*)\}\}", re.IGNORECASE), 0),
    ("HIEROGLYPH", re.compile(
        r"<hiero>([^<]*)</hiero>", re.IGNORECASE), 0),
]


def _extract_balanced_tables(text: str, registry: ElementRegistry) -> str:
    """Extract wiki tables using balanced {| |} matching.

    Handles nested tables correctly by finding outermost {| first.
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
                    placeholder = registry.add("TABLE", table_text)
                    text = text[:idx] + placeholder + text[i+2:]
                    found = True
                    break
                i += 2
            else:
                i += 1

        if not found:
            break  # Unbalanced — stop

    return text


def extract(text: str) -> tuple[str, ElementRegistry]:
    """Extract all embedded elements from text, outermost first.

    Returns the text with placeholders and a registry of extracted elements.
    """
    registry = ElementRegistry()

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
    if element_type == "SCORE":
        result = _process_score(raw, context)
    elif element_type == "MATH":
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
        result = _process_table(inner, text_transform, inner_registry)
    elif element_type == "HTML_TABLE":
        result = _process_html_table(inner, text_transform)
    else:
        result = inner

    # NOW reinsert processed children into the result
    for key, processed_child in processed_children.items():
        result = result.replace(key, processed_child)

    return result


def _clean_text(text: str) -> str:
    """Strip all internal markers and wiki templates from text, producing plain text."""
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
    return f"\u00abMATH:{inner.strip()}\u00ab/MATH\u00bb"


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


def _process_html_table(inner: str, text_transform) -> str:
    """Convert HTML table content (<tr>, <td>, <th>) to {{TABLE:...}TABLE}."""
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

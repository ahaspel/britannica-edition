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
    # (element_type, pattern, flags)
    ("TABLE", re.compile(r"\{\|.*?\|\}", re.DOTALL), 0),
    ("POEM", re.compile(r"<poem>.*?</poem>", re.DOTALL | re.IGNORECASE), 0),
    ("IMAGE_FLOAT", re.compile(
        r"\{\{(?:img float|figure|FI)\s*\|(?:[^{}]|\{\{[^{}]*\}\})*\}\}",
        re.DOTALL | re.IGNORECASE), 0),
    ("IMAGE", re.compile(
        r"\[\[(?:File|Image):([^\]]+)\]\]", re.IGNORECASE), 0),
    ("SCORE", re.compile(r"<score[^>]*>.*?</score>", re.DOTALL), 0),
    ("REF", re.compile(r"<ref(?:\s[^>]*)?>.*?</ref>", re.DOTALL | re.IGNORECASE), 0),
    ("MATH", re.compile(r"<math[^>]*>.*?</math>", re.DOTALL | re.IGNORECASE), 0),
]


def extract(text: str) -> tuple[str, ElementRegistry]:
    """Extract all embedded elements from text, outermost first.

    Returns the text with placeholders and a registry of extracted elements.
    """
    registry = ElementRegistry()

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
    elif element_type == "REF":
        return re.sub(r"<ref(?:\s[^>]*)?>|</ref>", "", raw, flags=re.IGNORECASE).strip()
    elif element_type == "POEM":
        return re.sub(r"</?poem>", "", raw, flags=re.IGNORECASE).strip()
    elif element_type == "MATH":
        return re.sub(r"<math[^>]*>|</math>", "", raw, flags=re.IGNORECASE).strip()
    elif element_type == "SCORE":
        return re.sub(r"<score[^>]*>|</score>", "", raw, flags=re.IGNORECASE).strip()
    elif element_type == "IMAGE":
        m = re.match(r"\[\[(?:File|Image):(.+)\]\]$", raw, re.IGNORECASE | re.DOTALL)
        return m.group(1) if m else raw
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
    for key, (child_type, child_raw) in inner_registry.elements.items():
        processed_child = _process_element(
            child_type, child_raw, text_transform, context)
        inner = inner.replace(key, processed_child)

    # Now process this element itself (children already resolved)
    if element_type == "SCORE":
        return _process_score(raw, context)
    elif element_type == "MATH":
        return _process_math(inner)
    elif element_type == "REF":
        return _process_ref(inner, text_transform)
    elif element_type == "IMAGE":
        return _process_image(inner, text_transform)
    elif element_type == "IMAGE_FLOAT":
        return _process_image_float(inner, text_transform)
    elif element_type == "POEM":
        return _process_poem(inner, text_transform)
    elif element_type == "TABLE":
        return _process_table(inner, text_transform)
    else:
        return inner


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
    return f"{{{{VERSE:{inner}}}}}VERSE}}"


def _process_table(inner: str, text_transform) -> str:
    """Convert table rows to {{TABLE:...}TABLE} with clean cells.

    By this point, child elements (footnotes, images, scores) have
    already been extracted, processed, and reinserted as final markers.
    The table processor only deals with table structure: rows, cells,
    and cell attributes.
    """
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

    # Cell attribute patterns to strip
    _ATTR = re.compile(
        r"^(?:colspan|rowspan|width|style|align|valign|class|"
        r"cellpadding|nowrap|border|bgcolor|height)[\s=|]",
        re.IGNORECASE,
    )

    text_rows = []
    image_parts = []

    for raw_row in raw_rows:
        # Skip caption rows
        if "|+" in raw_row:
            continue

        # Strip remaining wiki templates, but preserve our markers
        # ({{IMG:, {{TABLE, {{VERSE:, «FN:, «MATH:)
        cleaned = re.sub(
            r"\{\{(?!IMG:|TABLE|VERSE:)[^{}]*\}\}", "", raw_row)

        # Extract cell values: each | starts a cell.
        # Protect {{...}} markers from pipe-splitting.
        protected = re.sub(r"\{\{[^}]*\}\}", lambda m: m.group(0).replace("|", "\x04"), cleaned)
        cells = re.findall(r"\|([^|\n]+)", protected)
        cells = [c.replace("\x04", "|") for c in cells]
        cells = [c.strip() for c in cells
                 if c.strip()
                 and not _ATTR.match(c.strip())
                 and c.strip() not in ("}", "{|")]

        # Collect any image markers that were reinserted as children
        for cell in cells:
            if "{{IMG:" in cell or "\u00abFN:" in cell:
                # Cell contains a processed child marker — keep it
                pass

        # Separate image-only cells from data cells
        data_cells = []
        for c in cells:
            if re.match(r"^\s*\{\{IMG:[^}]+\}\}\s*$", c):
                image_parts.append(c.strip())
            else:
                data_cells.append(c)

        if not data_cells:
            continue

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

    # Process each element (recursion handles nesting)
    for key, (element_type, raw) in registry.elements.items():
        processed = _process_element(element_type, raw, text_transform, context)
        extracted = extracted.replace(key, processed)

    return extracted

"""Transform raw wikitext article bodies into internal marker format.

This stage runs after boundary detection.  Each article's body contains
raw Wikisource wikitext at this point.  We convert it to the internal
marker format (``«B»``, ``«FN:``, ``{{IMG:``, etc.) by running the same
26 fetch stages and clean_pages transformations — but per-article instead
of per-page, and skipping stage 3 (section-tag conversion) since
boundaries have already been determined.

Articles are processed one at a time and committed individually so that
only one article body is in memory at any point.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from britannica.db.models import Article, ArticleSegment, SourcePage
from britannica.db.session import SessionLocal

# --- Import clean_pages helpers (always available via src/) ----------------
from britannica.cleaners.headers_footers import strip_headers
from britannica.cleaners.hyphenation import fix_hyphenation
from britannica.cleaners.reflow import reflow_paragraphs
from britannica.cleaners.unicode import normalize_unicode
from britannica.cleaners.whitespace import normalize_whitespace
from britannica.pipeline.stages.clean_pages import (
    _STRAY_CONTROL,
    _clean_plate_layout,
    _convert_img_float,
    _clean_leaked_table_markup,
    _fix_unclosed_footnotes,
    _fix_unclosed_tables,
    _replace_score_tags,
)

# Fetch stages are loaded lazily — tools/fetch/ is not on sys.path at import
# time in all contexts (e.g. pytest collection).
_FETCH_STAGES = None


def _get_fetch_stages():
    global _FETCH_STAGES
    if _FETCH_STAGES is None:
        # Walk up from src/britannica/pipeline/stages/ to project root
        project_root = Path(__file__).resolve().parents[4]
        tools_fetch = str(project_root / "tools" / "fetch")
        if tools_fetch not in sys.path:
            sys.path.insert(0, tools_fetch)
        from fetch_wikisource_pages import STAGES
        _FETCH_STAGES = STAGES
    return _FETCH_STAGES


def _preprocess_text(text: str) -> str:
    """Run preprocessing stages on raw wikitext.

    Safe stages that don't destroy element delimiters.
    """
    # Strip <noinclude> blocks (page headers, quality tags, contributor tables)
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.DOTALL | re.IGNORECASE)
    stages = _get_fetch_stages()
    # 1: line endings, 4: HTML comments, 6: poem wrappers, 7: fine print
    # 24: decode HTML entities, 25: normalize whitespace
    for i in [0, 3, 5, 6, 23, 24]:
        text = stages[i](text)
    return text


# ── Body text processing stages ──────────────────────────────────────
#
# Each function handles one kind of wiki markup.  They run on body text
# AFTER embedded elements have been extracted, so they never see tables,
# images, footnotes, poems, math, or scores.

# Control characters for intermediate markers.
# \x03 is used by elements.py for placeholders, so we avoid it.
_FMT = "\x05"   # formatting (bold/italic/small-caps)
_LNK = "\x06"   # link markers
_SH  = "\x07"   # shoulder headings


def _convert_hieroglyphs(text: str) -> str:
    """{{hieroglyph|code}} → [hieroglyph: code]"""
    return re.sub(
        r"\{\{hieroglyph\|([^{}]*)\}\}",
        r"[hieroglyph: \1]", text, flags=re.IGNORECASE,
    )


def _convert_links(text: str) -> str:
    """Convert link templates and wikilinks to link markers."""

    # {{EB1911 article link|...}} — multiple parameter forms
    def _eb1911_link(m):
        inner = m.group(1)
        # Unwrap nested {{sc|...}}
        inner = re.sub(r"\{\{sc\|([^{}]*)\}\}", r"\1", inner, flags=re.IGNORECASE)
        parts = [p.strip() for p in inner.split("|")]
        positional = [p for p in parts if "=" not in p and p]
        if len(positional) >= 2:
            display, target = positional[0], positional[1]
        elif len(positional) == 1:
            display = target = positional[0]
        else:
            return ""
        # Subpage targets → plain text for section labels, link for articles
        if "/" in target:
            if re.match(r"^[IVXLC]+\.", display):
                return display
            return f"{_LNK}{display}|{display}{_LNK}"
        return f"{_LNK}{target}|{display}{_LNK}"

    # Unwrap nested {{sc|}} before matching EB1911 article link
    text = re.sub(
        r"(\{\{EB1911 article link\|[^}]*)(\{\{sc\|)([^}]*)(\}\})",
        lambda m: m.group(1) + m.group(3), text, flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\{\{EB1911 article link\|([^{}]*)\}\}",
        _eb1911_link, text, flags=re.IGNORECASE,
    )

    # {{1911link|Target}}, {{11link|Target}}
    text = re.sub(
        r"\{\{(?:1911link|11link)\|([^{}|]*)\}\}",
        lambda m: f"{_LNK}{m.group(1)}|{m.group(1)}{_LNK}",
        text, flags=re.IGNORECASE,
    )

    # {{EB1911 lkpl|...}} and {{DNB lkpl|...}}
    text = re.sub(
        r"\{\{(?:EB1911|DNB)\s+lkpl\|([^{}]+)\}\}",
        lambda m: f"{_LNK}{m.group(1).split('|')[0]}|{m.group(1).split('|')[-1]}{_LNK}",
        text, flags=re.IGNORECASE,
    )

    # [[wikilinks]] — handle nested brackets
    def _wikilink(m):
        content = m.group(1)
        # Skip File/Image/Category
        if re.match(r"(?i)^(File|Image|Category):", content):
            return ""
        # Protect {{...}} from pipe-splitting
        protected = re.sub(r"\{\{[^{}]*\}\}", lambda m2: m2.group(0).replace("|", "\x04"), content)
        parts = protected.split("|")
        parts = [p.replace("\x04", "|") for p in parts]
        target = parts[0].strip()
        display = parts[1].strip() if len(parts) > 1 else target
        # Unwrap templates in display text
        display = re.sub(r"\{\{sc\|([^{}]*)\}\}", r"\1", display, flags=re.IGNORECASE)
        display = re.sub(r"\{\{[^{}|]*\|([^{}]*)\}\}", r"\1", display)
        display = display.replace("'''", "").replace("''", "")
        # Interwiki/Author/Portal → display text only
        if re.match(r"(?i)^(Author|wikt|wiktionary|s|w|d|wikipedia|Portal|Page|File|1911):", target):
            return display
        return f"{_LNK}{target}|{display}{_LNK}"

    text = re.sub(r"\[\[(.*?)\]\]", _wikilink, text, flags=re.DOTALL)

    return text


def _convert_small_caps(text: str) -> str:
    """{{sc|text}}, {{asc|text}} → «SC»text«/SC»"""
    text = re.sub(
        r"\{\{sc\|([^{}]*)\}\}",
        f"{_FMT}SC\\1{_FMT}/SC", text, flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\{\{asc\|([^{}]*)\}\}",
        f"{_FMT}SC\\1{_FMT}/SC", text, flags=re.IGNORECASE,
    )
    return text


def _unwrap_content_templates(text: str) -> str:
    """Unwrap content templates to their text content."""
    # Language/script templates → plain text
    text = re.sub(r"\{\{Greek\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{polytonic\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{Hebrew\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{lang\|[^{}|]*\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    # Formatting wrappers → content
    text = re.sub(r"\{\{uc\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{nowrap\s*\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{smaller\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{larger\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    # Abbreviation/tooltip → first arg (display text)
    text = re.sub(r"\{\{abbr\|([^{}|]*)\|[^{}]*\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{tooltip\|([^{}|]*)\|[^{}]*\}\}", r"\1", text, flags=re.IGNORECASE)
    # Special markers
    text = re.sub(r"\{\{sic\}\}", "[sic]", text, flags=re.IGNORECASE)
    return text


def _convert_shoulder_headings(text: str) -> str:
    """{{EB1911 Shoulder Heading|text}} → «SH»text«/SH»"""
    text = re.sub(
        r"\{\{EB1911 Shoulder Heading(?:Small\d?)?\|([^{}]*)\}\}",
        lambda m: f"{_SH}SH{m.group(1).replace(chr(39)*3, '').replace(chr(39)*2, '').strip()}{_SH}/SH",
        text, flags=re.IGNORECASE,
    )
    return text


def _unwrap_layout_templates(text: str) -> str:
    """Unwrap {{center|...}}, {{c|...}}, {{fine block|...}} to content.
    {{csc|...}} → «SC»...«/SC»."""
    for name in ["center", "c", "fine block", "EB1911 Fine Print"]:
        text = re.sub(
            r"\{\{" + re.escape(name) + r"\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}",
            r"\1", text, flags=re.IGNORECASE,
        )
    # {{csc|...}} = centered small caps
    text = re.sub(
        r"\{\{csc\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}",
        f"{_FMT}SC\\1{_FMT}/SC", text, flags=re.IGNORECASE,
    )
    return text


def _convert_sub_sup(text: str) -> str:
    """<sub>x</sub> → Unicode subscript, <sup>x</sup> → Unicode superscript."""
    _SUB = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")
    _SUP = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")

    def _sub_repl(m):
        return m.group(1).translate(_SUB)

    def _sup_repl(m):
        return m.group(1).translate(_SUP)

    text = re.sub(r"<sub>([^<]*)</sub>", _sub_repl, text, flags=re.IGNORECASE)
    text = re.sub(r"<sup>([^<]*)</sup>", _sup_repl, text, flags=re.IGNORECASE)
    return text


def _convert_bold_italic(text: str) -> str:
    """'''bold''' → «B»bold«/B», ''italic'' → «I»italic«/I»."""
    # Bold-italic (5 quotes) first
    text = re.sub(r"'''''(.*?)'''''",
                  lambda m: f"{_FMT}B{_FMT}I{m.group(1)}{_FMT}/I{_FMT}/B",
                  text, flags=re.DOTALL)
    # Normalize 4 quotes to 3
    text = text.replace("''''", "'''")
    # Bold (3 quotes)
    text = re.sub(r"'''(.*?)'''", f"{_FMT}B\\1{_FMT}/B", text, flags=re.DOTALL)
    # Italic (2 quotes)
    text = re.sub(r"''(.*?)''", f"{_FMT}I\\1{_FMT}/I", text, flags=re.DOTALL)
    # Strip any residual '' markers
    text = text.replace("''", "")
    return text


def _strip_templates(text: str) -> str:
    """Strip all remaining {{...}} wiki templates and orphaned markup."""
    # Iterative stripping handles nesting
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # Orphaned closing braces
    text = re.sub(r"^\s*\}\}+\s*$", "", text, flags=re.MULTILINE)
    # Orphaned wiki table markup
    text = re.sub(r"^\s*\|\}+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\{\|\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\|-\s*$", "", text, flags=re.MULTILINE)
    return text


def _strip_html(text: str) -> str:
    """Strip remaining HTML tags (safe on body text — elements already extracted)."""
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)
    return text


def _decode_entities(text: str) -> str:
    """Decode HTML entities to characters."""
    import html as html_mod
    return html_mod.unescape(text)


def _finalize_markers(text: str) -> str:
    """Convert control-character markers to readable «» format."""
    text = text.replace(f"{_FMT}B", "\u00abB\u00bb")
    text = text.replace(f"{_FMT}/B", "\u00ab/B\u00bb")
    text = text.replace(f"{_FMT}I", "\u00abI\u00bb")
    text = text.replace(f"{_FMT}/I", "\u00ab/I\u00bb")
    text = text.replace(f"{_FMT}SC", "\u00abSC\u00bb")
    text = text.replace(f"{_FMT}/SC", "\u00ab/SC\u00bb")
    text = text.replace(f"{_SH}SH", "\u00abSH\u00bb")
    text = text.replace(f"{_SH}/SH", "\u00ab/SH\u00bb")
    # Link markers
    text = re.sub(
        re.escape(_LNK) + r"([^|" + re.escape(_LNK) + r"]+)\|([^" + re.escape(_LNK) + r"]+)" + re.escape(_LNK),
        lambda m: f"\u00abLN:{m.group(1)}|{m.group(2)}\u00ab/LN\u00bb",
        text,
    )
    return text


def _transform_body_text(text: str) -> str:
    """Transform plain wikitext body text to internal marker format.

    Each step is explicit.  No fetch stage dependencies.
    Embedded elements have already been extracted.
    """
    text = _convert_hieroglyphs(text)
    text = _convert_links(text)
    text = _unwrap_content_templates(text)
    text = _convert_small_caps(text)
    text = _convert_shoulder_headings(text)
    text = _unwrap_layout_templates(text)
    text = _convert_sub_sup(text)
    text = _convert_bold_italic(text)
    text = _strip_templates(text)
    text = _strip_html(text)
    text = _decode_entities(text)
    text = _finalize_markers(text)
    # Normalize whitespace
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" +([,.;:!?])", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _transform_plate(raw_wikitext: str) -> str:
    """Transform a plate page: extract images and numbered captions, pair them.

    Plate pages are image grids with captions — not regular article text.
    No table processing, no text transformation. Just images and captions.
    """
    # Strip noinclude, section tags, comments
    text = re.sub(r"<noinclude>.*?</noinclude>", "", raw_wikitext,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<section[^>]+>', "", text, flags=re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Extract all images
    images = []
    for m in re.finditer(r"\[\[(?:File|Image):([^|\]]+)", text, re.IGNORECASE):
        images.append(m.group(1).strip())

    # Extract all numbered captions: "N. CAPTION TEXT"
    captions = {}
    for m in re.finditer(r"(\d+)\.\s+([A-Z][A-Z\s,.:;()\-']+)", text):
        num = int(m.group(1))
        cap = m.group(2).strip().rstrip(",.|;")
        if len(cap) >= 3 and num not in captions:
            captions[num] = cap

    # Extract title lines (plate title, e.g. "EARLY EGYPTIAN ART")
    title_lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("[[") or line.startswith("{|") or line.startswith("|}"):
            continue
        if line.startswith("|") or line.startswith("{{"):
            continue
        # Clean wiki markup
        clean = re.sub(r"\{\{[^{}]*\}\}", "", line)
        clean = re.sub(r"'''|''", "", clean)
        clean = re.sub(r"<[^>]+>", "", clean)
        clean = clean.strip()
        if clean and len(clean) > 2 and not re.match(r"^\d+\.", clean):
            if clean.isupper() or clean.startswith("Plate"):
                title_lines.append(clean)

    # Pair images with captions by keyword matching
    sorted_caps = sorted(captions.items())
    used_images = set()
    paired = []

    def _img_words(filename):
        name = filename.rsplit("/", 1)[-1]
        name = re.sub(r"\.jpg$|\.png$", "", name, flags=re.IGNORECASE)
        if " - " in name:
            name = name.rsplit(" - ", 1)[-1]
        return set(re.findall(r"[A-Za-z]{3,}", name.upper()))

    for num, cap in sorted_caps:
        cap_words = set(re.findall(r"[A-Z]{3,}", cap))
        best_img = None
        best_score = 0
        for i, img in enumerate(images):
            if i in used_images:
                continue
            img_words = _img_words(img)
            score = len(cap_words & img_words)
            if score > best_score:
                best_score = score
                best_img = i
        if best_img is not None and best_score > 0:
            used_images.add(best_img)
            paired.append(f"{{{{IMG:{images[best_img]}|{num}. {cap}}}}}")
        else:
            paired.append(f"{num}. {cap}")

    # Add unmatched images
    for i, img in enumerate(images):
        if i not in used_images:
            paired.append(f"{{{{IMG:{img}}}}}")

    # Assemble: title + paired images
    result_parts = []
    for t in title_lines:
        result_parts.append(t)
    result_parts.extend(paired)

    return "\n\n".join(result_parts)


def _transform_text_v2(raw_wikitext: str, volume: int, page_number: int) -> str:
    """New architecture: extract-process-reassemble.

    1. Minimal preprocessing (strip section tags, noinclude, normalize)
    2. process_elements does everything:
       - Extracts embedded elements
       - Transforms body text (bold, italic, links, etc.)
       - Processes each element recursively
       - Reassembles
    3. Done.
    """
    from britannica.pipeline.stages.elements import process_elements

    # Strip section tags — boundaries already determined
    text = re.sub(r'<section\s+(?:begin|end)="[^"]*"\s*/?>', "",
                  raw_wikitext, flags=re.IGNORECASE)

    # Strip <noinclude> blocks (page headers, quality tags)
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text,
                  flags=re.DOTALL | re.IGNORECASE)

    # Replace <score> tags (static lookup, must happen before extraction)
    text = _replace_score_tags(text, volume, page_number)

    # Normalize
    text = normalize_unicode(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Unwrap poem wrappers: {{block center|<poem>...</poem>}} → <poem>...</poem>
    text = re.sub(
        r"\{\{block center\|(<poem>.*?</poem>)\}\}",
        r"\1", text, flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(
        r"\{\{center\|(<poem>.*?</poem>)\}\}",
        r"\1", text, flags=re.DOTALL | re.IGNORECASE,
    )

    # Unwrap fine print markers
    text = re.sub(
        r"\{\{EB1911 fine print/s\}\}(.*?)\{\{EB1911 fine print/e\}\}",
        r"\1", text, flags=re.DOTALL | re.IGNORECASE,
    )

    # Unwrap {{fine block|...}} with balanced brace matching
    def _unwrap_balanced(text, template_name):
        """Unwrap a template by finding the balanced closing }}."""
        prefix = "{{" + template_name + "|"
        while True:
            idx = text.lower().find(prefix.lower())
            if idx < 0:
                break
            # Find balanced close
            depth = 0
            i = idx
            while i < len(text) - 1:
                if text[i:i+2] == "{{":
                    depth += 1
                    i += 2
                elif text[i:i+2] == "}}":
                    depth -= 1
                    if depth == 0:
                        # Replace: strip outer {{ and }}
                        content = text[idx + len(prefix):i]
                        text = text[:idx] + content + text[i+2:]
                        break
                    i += 2
                else:
                    i += 1
            else:
                break  # unbalanced — give up
        return text

    for tmpl in ["fine block", "center", "c", "larger", "smaller",
                  "EB1911 Fine Print"]:
        text = _unwrap_balanced(text, tmpl)

    # Unwrap {{nowrap|...}} before table extraction so inner | isn't
    # mistaken for cell separators
    text = re.sub(r"\{\{nowrap\s*\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    # Strip table style templates ({{ts|...}}, {{Ts|...}}) that interfere
    # with cell parsing
    text = re.sub(r"\{\{[Tt]s\|[^{}]*\}\}", "", text)

    # Wrap orphaned table rows so the extractor can find them
    text = _wrap_orphaned_table_rows(text)

    # Extract, process, reassemble — this does all the work
    context = {"volume": volume, "page_number": page_number}
    text = process_elements(text, _transform_body_text, context)

    # Reflow paragraphs — join lines that were hard-wrapped in the source
    text = reflow_paragraphs(text)

    return text


def _run_fetch_stages(text: str) -> str:
    """Run the 26 fetch conversion stages, skipping stage 3 (section tags).

    Stage 3 converts ``<section begin=...>`` to ``«SEC:...»`` markers.
    We skip it because boundaries are already locked in — the section tags
    have served their purpose and should simply be stripped.
    """
    stages = _get_fetch_stages()
    for i, stage_fn in enumerate(stages):
        if i == 2:  # stage 3 is index 2 (0-based)
            continue
        text = stage_fn(text)
    return text


def _run_clean_pages(text: str) -> str:
    """Run the clean_pages transformations on marker-format text."""
    text = normalize_unicode(text)
    text, _ = strip_headers(text)
    text, _ = fix_hyphenation(text)
    text = reflow_paragraphs(text)
    text = normalize_whitespace(text)
    text = _STRAY_CONTROL.sub("", text)
    text = text.replace("''", "")
    text = _clean_plate_layout(text)
    text = _convert_img_float(text)
    text = _clean_leaked_table_markup(text)
    text = _fix_unclosed_footnotes(text)
    text = _fix_unclosed_tables(text)
    return text


def _wrap_orphaned_table_rows(text: str) -> str:
    """Wrap orphaned wiki table rows (|- and | lines) that lack a {| opener.

    Multi-page wiki tables have {| in <noinclude> on continuation pages.
    After noinclude stripping, the rows are left bare.  Wrap them in
    {|...|} so the table converter can process them.

    Also detects runs of |lines without |- separators (two-column tables
    spanning page boundaries).
    """
    # Quick check: any lines starting with |?
    has_pipe_rows = any(
        line.strip().startswith("|") and len(line.strip()) > 3
        for line in text.split("\n")
    )
    if not has_pipe_rows:
        return text

    # If text already has a table opener, only wrap BEFORE it
    # (orphaned rows preceding the table) or leave alone
    if "{|" in text:
        # Only handle |- rows before the first {|
        first_table = text.find("{|")
        prefix = text[:first_table]
        rest = text[first_table:]
        if "\n|-" in prefix or prefix.strip().startswith("|-"):
            wrapped_prefix = _wrap_orphaned_table_rows(prefix)
            return wrapped_prefix + rest
        return text

    # Find runs of |lines and wrap them
    lines = text.split("\n")
    first_row = None
    last_row = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        is_table_line = (
            (stripped.startswith("|-") or stripped.startswith("|"))
            and len(stripped) > 3
            and not stripped.startswith("|}")
        )
        if is_table_line:
            if first_row is None:
                first_row = i
            last_row = i

    if first_row is None:
        return text

    # Wrap the table rows
    before = "\n".join(lines[:first_row])
    table = "\n".join(lines[first_row:last_row + 1])
    after = "\n".join(lines[last_row + 1:])
    parts = []
    if before.strip():
        parts.append(before)
    parts.append("{|\n" + table + "\n|}")
    if after.strip():
        parts.append(after)
    return "\n".join(parts)


def _clean_img_captions(text: str) -> str:
    """Clean image captions to plain text.

    After all marker conversions, image captions may contain formatting
    markers («I», «SC», etc.) and residual HTML.  Strip these so captions
    are clean text — the viewer should not have to process them.
    """
    def _clean(m):
        filename = m.group(1)
        caption = m.group(2) or ""
        if caption:
            # Strip formatting markers, keeping the text inside
            caption = re.sub(r"\u00abB\u00bb(.*?)\u00ab/B\u00bb", r"\1", caption)
            caption = re.sub(r"\u00abI\u00bb(.*?)\u00ab/I\u00bb", r"\1", caption)
            caption = re.sub(r"\u00abSC\u00bb(.*?)\u00ab/SC\u00bb", r"\1", caption)
            caption = re.sub(r"\u00ab/?[A-Z]+\u00bb", "", caption)
            # Strip HTML tags (<br />, etc.)
            caption = re.sub(r"<[^>]+>", " ", caption)
            # Decode common HTML entities
            caption = caption.replace("\u2001", "").replace("&nbsp;", " ")
            caption = caption.replace("&#39;", "'").replace("&amp;", "&")
            caption = caption.replace("&#8193;", "")
            # Collapse whitespace
            caption = re.sub(r"\s+", " ", caption).strip()
            return "{{IMG:" + filename + "|" + caption + "}}"
        return "{{IMG:" + filename + "}}"
    return re.sub(r"\{\{IMG:([^|}]+)(?:\|([^}]*))?\}\}", _clean, text)


def _transform_text(raw_wikitext: str) -> str:
    """Convert raw wikitext to the final internal marker format."""
    # Strip any remaining section tags (begin and end) — boundaries are done
    text = re.sub(r'<section\s+(?:begin|end)="[^"]*"\s*/?>', "", raw_wikitext, flags=re.IGNORECASE)
    text = _wrap_orphaned_table_rows(text)
    text = _run_fetch_stages(text)
    text = _run_clean_pages(text)
    text = _clean_img_captions(text)
    return text


def transform_articles(volume: int) -> int:
    """Transform raw wikitext to internal marker format for all articles in a volume.

    Transforms each segment (page-sized) individually, then joins them
    into article.body with \\x01PAGE:N\\x01 markers at page boundaries.
    The markers are injected after transformation so they survive the
    control-character stripping in clean_pages.

    Processes one article at a time with per-article commits.
    """
    session = SessionLocal()
    try:
        article_ids = [
            aid for (aid,) in session.query(Article.id)
            .filter(Article.volume == volume)
            .all()
        ]

        for aid in article_ids:
            article = session.get(Article, aid)
            segments = (
                session.query(ArticleSegment)
                .join(SourcePage, ArticleSegment.source_page_id == SourcePage.id)
                .filter(ArticleSegment.article_id == aid)
                .order_by(ArticleSegment.sequence_in_article)
                .add_columns(SourcePage.page_number)
                .all()
            )

            is_plate = article.article_type == "plate"
            parts: list[str] = []
            for seg, page_number in segments:
                raw = seg.segment_text or ""
                if is_plate:
                    text = _transform_plate(raw) if raw else ""
                else:
                    text = _transform_text_v2(raw, volume, page_number) if raw else ""
                text = text.strip()
                if not text:
                    continue
                marker = f"\x01PAGE:{page_number}\x01"
                if parts:
                    joiner = "\n\n" if re.match(r"\u00abIMG:|\u00abSC\u00bb", text) else " "
                    parts.append(joiner)
                else:
                    # First segment — marker goes at the very start
                    text = marker + text
                    parts.append(text)
                    continue
                parts.append(marker + text)

            article.body = "".join(parts).strip()
            session.commit()
            session.expire_all()

        return len(article_ids)
    finally:
        session.close()

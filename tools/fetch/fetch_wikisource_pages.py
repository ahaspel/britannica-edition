#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import html
import time
from pathlib import Path
import requests

from britannica.markers import (
    _INTERNAL_IMG as _IMG,
    _INTERNAL_FN as _FN,
    _INTERNAL_TABLE as _TBL,
    _INTERNAL_LINK as _LNK,
    _INTERNAL_MATH as _MATH,
    _INTERNAL_VERSE as _VERSE,
    _INTERNAL_FORMAT as _FMT,
    _INTERNAL_SEC as _SEC,
    _INTERNAL_PRE as _PRE,
)

API_URL = "https://en.wikisource.org/w/api.php"

HEADERS = {
    "User-Agent": "britannica-edition/0.1 (local dev)",
    "Accept": "application/json",
}


def fetch_page_wikitext(volume: int, page_number: int) -> str:
    title = f"Page:EB1911 - Volume {volume:02d}.djvu/{page_number}"
    params = {
        "action": "query",
        "prop": "revisions",
        "rvslots": "main",
        "rvprop": "content",
        "titles": title,
        "format": "json",
        "formatversion": "2",
    }

    max_retries = 3
    for attempt in range(max_retries):
        print(f"Fetching {title} ...")
        response = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
        print(f"HTTP {response.status_code} for {title}")

        if response.status_code == 429:
            print(f"  Rate limited, sleeping 1 hour...")
            time.sleep(3600)
            continue

        response.raise_for_status()
        break
    else:
        raise requests.exceptions.HTTPError(
            f"Still rate-limited after {max_retries} retries for {title}"
        )

    data = response.json()
    pages = data.get("query", {}).get("pages", [])
    if not pages:
        raise ValueError(f"No page data returned for {title}")

    page = pages[0]
    if page.get("missing"):
        print(f"  Page does not exist: {title} — writing empty placeholder")
        return ""

    revisions = page.get("revisions", [])
    if not revisions:
        raise ValueError(f"No revisions/content found for {title}")

    rev = revisions[0]

    content = rev.get("content")
    if content is None:
        content = rev.get("slots", {}).get("main", {}).get("content")

    # Extra fallback for some MediaWiki response shapes
    if content is None:
        content = rev.get("slots", {}).get("main", {}).get("*")

    if content is None:
        raise ValueError(
            f"Could not locate content for {title}. Revision keys: {list(rev.keys())}"
        )

    return content

_UNICODE_FRACTIONS = {
    ("1", "2"): "\u00bd",       # ½
    ("1", "3"): "\u2153",       # ⅓
    ("2", "3"): "\u2154",       # ⅔
    ("1", "4"): "\u00bc",       # ¼
    ("3", "4"): "\u00be",       # ¾
    ("1", "5"): "\u2155",       # ⅕
    ("2", "5"): "\u2156",       # ⅖
    ("3", "5"): "\u2157",       # ⅗
    ("4", "5"): "\u2158",       # ⅘
    ("1", "6"): "\u2159",       # ⅙
    ("5", "6"): "\u215a",       # ⅚
    ("1", "7"): "\u2150",       # ⅐
    ("1", "8"): "\u215b",       # ⅛
    ("3", "8"): "\u215c",       # ⅜
    ("5", "8"): "\u215d",       # ⅝
    ("7", "8"): "\u215e",       # ⅞
    ("1", "9"): "\u2151",       # ⅑
    ("1", "10"): "\u2152",      # ⅒
}


def _to_fraction(num: str, denom: str) -> str:
    """Convert numerator/denominator to Unicode fraction or text."""
    if not denom:
        # Single argument like {{EB1911 tfrac|2}} — probably a superscript 2
        return _to_unicode_sup(num)
    # Try Unicode fraction
    frac = _UNICODE_FRACTIONS.get((num, denom))
    if frac:
        return frac
    # Fall back to text fraction with Unicode fraction slash
    return f"{num}\u2044{denom}"


_SUB_MAP = str.maketrans("0123456789aeioruvxhklmnpst()+=-",
                          "₀₁₂₃₄₅₆₇₈₉ₐₑᵢₒᵣᵤᵥₓₕₖₗₘₙₚₛₜ₍₎₊₌₋")

_SUP_MAP = str.maketrans("0123456789abcdefghijklmnoprstuvwxyz()+=-",
                          "⁰¹²³⁴⁵⁶⁷⁸⁹ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ⁽⁾⁺⁼⁻")


def _to_unicode_sub(text: str) -> str:
    """Convert text to Unicode subscript characters where possible."""
    return text.translate(_SUB_MAP)


def _to_unicode_sup(text: str) -> str:
    """Convert text to Unicode superscript characters where possible."""
    return text.translate(_SUP_MAP)


def _parse_plate_table(table_html: str) -> str:
    """Parse an HTML plate table into sectioned image markers with captions.

    Plate tables have a repeating 3-row pattern:
      Row 1: images (3 across)
      Row 2: section labels (ALLOYS, GUN-MAKING, etc.)
      Row 3: captions (Fig. 1, Fig. 2, etc.)
    """
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, flags=re.DOTALL | re.IGNORECASE)
    if not rows:
        return ""

    def _extract_images(row_html):
        return [m.group(1) for m in re.finditer(r"\[\[(?:Image|File):([^\]|]+)", row_html, re.I)]

    def _extract_cells(row_html):
        return [re.sub(r"<[^>]+>", "", cell).strip()
                for cell in re.findall(r"<td[^>]*>(.*?)</td>", row_html, flags=re.DOTALL | re.I)]

    def _clean_caption(text):
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)
        text = text.replace("''", "").replace("&amp;", "&").replace("&deg;", "\u00b0")
        return " ".join(text.split()).strip()

    # Collect figures: (image, section, caption)
    figures = []
    i = 0
    while i < len(rows):
        images = _extract_images(rows[i])
        if not images:
            i += 1
            continue

        labels = []
        if i + 1 < len(rows):
            cells = _extract_cells(rows[i + 1])
            labels = [c.strip().rstrip(".") for c in cells if c.strip() and any(ch.isalpha() for ch in c)]

        captions = []
        if i + 2 < len(rows):
            raw_cells = re.findall(r"<td[^>]*>(.*?)</td>", rows[i + 2], flags=re.DOTALL | re.I)
            captions = [_clean_caption(c) for c in raw_cells if c.strip()]

        for j, img in enumerate(images):
            section = labels[j] if j < len(labels) else ""
            caption = captions[j] if j < len(captions) else ""
            figures.append((img, section, caption))

        i += 3

    if not figures:
        return ""

    # Group by section and produce output
    from collections import OrderedDict
    sections: dict[str, list[tuple[str, str]]] = OrderedDict()
    for img, section, caption in figures:
        if section not in sections:
            sections[section] = []
        sections[section].append((img, caption))

    parts = []
    for section, figs in sections.items():
        if section:
            parts.append(section)
        for img, caption in figs:
            marker = f"{_IMG}IMG:{img}{_IMG}"
            if caption:
                parts.append(f"{marker}\n{caption}")
            else:
                parts.append(marker)

    # Get the overall plate title (usually last row)
    last_cells = _extract_cells(rows[-1]) if rows else []
    overall_title = ""
    for c in last_cells:
        c = c.strip()
        if c and len(c) > 10 and c.upper() == c:
            overall_title = c.rstrip(".")
            break
    if overall_title:
        parts.append(overall_title)

    return "\n\n".join(parts)


def _image_to_marker(match: re.Match) -> str:
    """Convert [[File:name|opts]] to an inline marker."""
    parts = [p.strip() for p in match.group(1).split("|")]
    filename = parts[0]

    # Bracket SVGs → Unicode characters (before size check)
    fname_lower = filename.lower()
    if "langle.svg" in fname_lower:
        return "\u27e8"
    if "rangle.svg" in fname_lower:
        return "\u27e9"
    if "double bond over single bond" in fname_lower:
        return "="

    # Extract caption (last non-keyword, non-size part)
    keywords = {"center", "left", "right", "thumb", "thumbnail", "frameless",
                "frame", "border", "upright", "none"}
    caption = ""
    for part in reversed(parts[1:]):
        lower = part.lower()
        if lower in keywords or re.match(r"^\d+px$", lower) or lower.startswith("upright="):
            continue
        if part:
            caption = part
            break

    # Skip tiny inline symbols (< 20px) — these are decorative
    for part in parts[1:]:
        m = re.match(r"^(\d+)px$", part.lower())
        if m and int(m.group(1)) < 20:
            return ""

    if caption:
        return f"\n\n{_IMG}IMG:{filename}|{caption}{_IMG}\n\n"
    return f"\n\n{_IMG}IMG:{filename}{_IMG}\n\n"


# ── Helper functions extracted from clean_wikisource_page_text ──────────


def _rescue_noinclude(m: re.Match) -> str:
    content = m.group(0)
    # Look for images
    images = re.findall(
        r"\[\[(?:image|file):([^\]]+)\]\]", content, re.IGNORECASE
    )
    if not images:
        return ""
    parts = []
    for img_text in images:
        img_parts = [p.strip() for p in img_text.split("|")]
        filename = img_parts[0]
        # Skip tiny decorative images
        is_tiny = any(re.match(r"^\d+px$", p) and int(p[:-2]) < 20
                      for p in img_parts[1:])
        if is_tiny:
            continue
        # Extract caption if present
        keywords = {"center", "left", "right", "thumb", "thumbnail",
                    "frameless", "frame", "border", "upright", "none"}
        caption = ""
        for part in reversed(img_parts[1:]):
            lower = part.lower()
            if lower in keywords or re.match(r"^\d+px$", lower) or lower.startswith("x") and lower[1:].rstrip("px").isdigit():
                continue
            if part:
                caption = part
                break
        if caption:
            parts.append(f"\n\n{_IMG}IMG:{filename}|{caption}{_IMG}\n\n")
        else:
            parts.append(f"\n\n{_IMG}IMG:{filename}{_IMG}\n\n")
    # Also rescue EB1911 Fine Print captions
    for fm in re.finditer(
        r"\{\{EB1911 Fine Print\|([^}]+)\}\}", content, re.IGNORECASE
    ):
        cap = fm.group(1)
        cap = re.sub(r"\{\{sc\|([^}]*)\}\}", r"\1", cap)
        cap = re.sub(r"\{\{[^}]*\}\}", "", cap)
        cap = re.sub(r"<br\s*/?>", " ", cap, flags=re.IGNORECASE)
        cap = cap.strip()
        if cap:
            parts.append(cap)
    return "\n".join(parts)


def _fine_print_handler(m: re.Match) -> str:
    content = m.group(1).strip()
    # If it starts with a quote mark, treat as verse
    if content.startswith('"') or content.startswith('\u201c'):
        return f"\n\n{_VERSE}VERSE\n{content}\n{_VERSE}\n\n"
    # Otherwise just preserve the text
    return content


def _poem_to_marker(m: re.Match) -> str:
    content = m.group(1).strip()
    # {{gap}} between two key entries (followed by a letter key) → newline
    content = re.sub(
        r"\{\{gap(?:\|[^{}]*)?\}\}(?=''?[A-Za-z])", "\n",
        content, flags=re.IGNORECASE,
    )
    # <br> followed by {{gap}} indentation → space (continuation line)
    content = re.sub(r"<br\s*/?>\s*\{\{gap(?:\|[^{}]*)?\}\}", " ", content, flags=re.IGNORECASE)
    # Remaining <br> within poem lines → space
    content = re.sub(r"<br\s*/?>", " ", content, flags=re.IGNORECASE)
    # Spacing templates ({{em|...}}, {{gap|...}}, {{gap}}) → space
    content = re.sub(r"\{\{(?:em|gap)(?:\|[^{}]*)?\}\}", " ", content, flags=re.IGNORECASE)
    # Strip remaining templates
    content = re.sub(r"\{\{[^{}]*\}\}", "", content)
    content = content.replace("'''", "").replace("''", "")
    # HTML entities
    content = re.sub(r"&[a-z]+;", " ", content)
    content = "\n".join(line.strip() for line in content.split("\n") if line.strip())
    return f"\n\n{_VERSE}VERSE\n{content}\n{_VERSE}\n\n"


def _ref_to_marker(match: re.Match) -> str:
    content = match.group(1).strip()
    # Clean basic wiki markup from footnote content
    content = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", content)
    content = re.sub(r"\[\[([^\]]+)\]\]", r"\1", content)
    content = content.replace("'''", "").replace("''", "")
    return f"{_FN}FN:{content}{_FN}"


def _lkpl_to_marker(m: re.Match) -> str:
    parts = m.group(1).split("|")
    target = parts[0].strip()
    display = parts[1].strip() if len(parts) > 1 else target
    return f"{_LNK}{target}|{display}{_LNK}"


def _wikilink_to_marker(m: re.Match) -> str:
    content = m.group(1)
    # Skip File/Image/Category entirely
    if re.match(r"(?i)^(File|Image|Category):", content):
        return ""
    parts = content.split("|")
    target = parts[0].strip()
    display = parts[1].strip() if len(parts) > 1 else target
    # Interwiki/interlanguage links, Author:, Portal:, Page:, File: — keep display text only
    # Strip wiki bold/italic markup so exposed text doesn't create false article boundaries
    if re.match(r"(?i)^(Author|wikt|wiktionary|s|w|d|wikipedia|Portal|Page|File):", target):
        return display.replace("'''", "").replace("''", "")
    if re.match(r"^:", target):
        return display.replace("'''", "").replace("''", "")
    return f"{_LNK}{target}|{display}{_LNK}"


def _is_structural_formula(content: str) -> bool:
    """Detect tables that represent structural chemical formulas."""
    if "\u27e8" in content or "\u27e9" in content:
        return True
    if "\u2a95" in content or "\u2a2a" in content:  # bond chars ⪕ ⪪
        return True
    rows = re.split(r"\|-", content)
    if len(rows) <= 5 and "rowspan" in content.lower():
        # Small table with rowspan + chemical subscripts
        if re.search(r"[A-Z][a-z]?[₀-₉]", content):
            return True
    return False


def _structural_to_pre(content: str) -> str:
    """Extract cell text from a structural formula table, preserving rows."""
    rows = re.split(r"\|-", content)
    lines = []
    for row in rows:
        # Convert HTML sub/sup to Unicode before extraction
        row = re.sub(r"<sub[^>]*>(.*?)</sub>", lambda m: _to_unicode_sub(m.group(1)),
                     row, flags=re.DOTALL | re.IGNORECASE)
        row = re.sub(r"<sup[^>]*>(.*?)</sup>", lambda m: _to_unicode_sup(m.group(1)),
                     row, flags=re.DOTALL | re.IGNORECASE)
        # Strip templates and HTML tags
        row = re.sub(r"\{\{[^{}]*\}\}", "", row)
        row = re.sub(r"<[^>]+>", "", row)
        cells = re.findall(r"\|([^|\n]+)", row)
        cells = [c.strip() for c in cells
                 if c.strip()
                 and not re.match(r"^(?:colspan|rowspan|width|style|align|class|cellpadding|nowrap|valign|border|bgcolor|height)[\s=\|]", c.strip())
                 and c.strip() not in ("}",)]
        if cells:
            lines.append("  ".join(cells))
    return "\n".join(lines)


def _extract_caption(content: str) -> str:
    """Extract figure caption from {{center|{{sc|Fig.}}—...}} or similar."""
    # Match {{center|...}} — may contain nested templates
    m = re.search(r"\{\{center\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}", content)
    if m:
        cap = m.group(1)
    else:
        # Match a row containing {{sc|Fig.}}—Caption
        m = re.search(
            r"\{\{[Ss][Cc]\|([Ff]ig\.?\s*\d*\.?)\}\}(.*?)(?:\n|$)",
            content,
        )
        if m:
            cap = m.group(1) + m.group(2)
        else:
            # Match plain text caption after an image row (e.g., "—Bird's-eye view")
            m = re.search(r"\|(\u2014[^\n|]{5,80})(?:\n|$)", content)
            if m:
                return m.group(1).strip()
            return ""
    # Unwrap nested templates but keep text
    cap = re.sub(r"\{\{sc\|([^{}]*)\}\}", r"\1", cap, flags=re.IGNORECASE)
    cap = re.sub(r"\{\{[^{}]*\}\}", "", cap)
    cap = re.sub(r"\[\[[^|\]]*\|([^\]]*)\]\]", r"\1", cap)  # [[target|display]]
    cap = re.sub(r"\[\[([^\]]*)\]\]", r"\1", cap)  # [[target]]
    # Strip link markers already converted
    cap = re.sub(re.escape(_LNK) + r"[^" + re.escape(_LNK) + r"]*\|([^" + re.escape(_LNK) + r"]*)" + re.escape(_LNK), r"\1", cap)
    cap = re.sub(r"<br\s*/?>", " ", cap, flags=re.IGNORECASE)
    cap = re.sub(r"''([^']*?)''", r"\1", cap)  # strip wiki italic
    cap = re.sub(r"<[^>]+>", "", cap)
    cap = re.sub(r"&[a-z]+;", " ", cap)
    cap = re.sub(r"\s+", " ", cap)
    return cap.strip()


def _extract_legend(content: str) -> str:
    """Extract legend key text from VERSE markers (originally <poem> blocks).

    Returns legend as pipe-separated table rows (letter | description)
    for consistent rendering.
    """
    rows = []
    # By this point, <poem> blocks have been converted to VERSE markers
    verse_pat = re.compile(
        re.escape(_VERSE) + r"VERSE\n(.*?)\n" + re.escape(_VERSE),
        re.DOTALL,
    )
    for m in verse_pat.finditer(content):
        text = m.group(1)
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Convert HTML sub/sup to Unicode before key matching
            line = re.sub(r"<sub>(\d+)</sub>", lambda m: "".join(
                chr(0x2080 + int(c)) for c in m.group(1)), line)
            line = re.sub(r"<sup>(\d+)</sup>", lambda m: "".join(
                chr(0x2070 + int(c)) if c != "1" else "\u00b9"
                for c in m.group(1)), line)
            # Strip remaining HTML tags and entities
            line = re.sub(r"<[^>]+>", "", line)
            line = re.sub(r"&[a-z]+;", " ", line)
            line = re.sub(r"\s+", " ", line).strip()
            if not line:
                continue
            # Parse "A. Church." or "c,c.Mills" or "P₁.Scriptorium"
            # Handles subscript digits, comma-separated compound keys
            key_match = re.match(
                r"^([A-Za-z0-9₀-₉]+(?:[,\-–][A-Za-z0-9₀-₉]+)*\.)\s*(.+)$", line,
            )
            if key_match:
                rows.append(f"{key_match.group(1)} | {key_match.group(2)}")
            else:
                rows.append(line)
    if not rows:
        return ""
    return f"{_TBL}TABLE\n" + "\n".join(rows) + f"\n{_TBL}"


def _convert_table(match: re.Match) -> str:
    content = match.group(0)

    # Structural formula tables → PRE blocks
    if _is_structural_formula(content):
        pre_text = _structural_to_pre(content)
        if pre_text.strip():
            return f"{_PRE}PRE\n{pre_text}\n{_PRE}"

    # Extract image markers first
    img_pat = re.compile(re.escape(_IMG) + r"IMG:[^" + re.escape(_IMG) + r"]+" + re.escape(_IMG))
    img_markers = img_pat.findall(content)

    # Image-layout tables: image + caption/legend.
    # Detect by: has images AND (verse legend, figure caption, or multiple images)
    has_verse_legend = bool(re.search(re.escape(_VERSE) + r"VERSE", content))
    has_fig_caption = bool(re.search(r"\{\{sc\|[Ff]ig", content))
    is_image_layout = len(img_markers) >= 2
    if img_markers and (has_verse_legend or has_fig_caption or is_image_layout):
        caption = _extract_caption(content)
        legend = _extract_legend(content)

        parts = []
        for img in img_markers:
            if caption:
                # Append caption to the image marker
                # Strip the trailing delimiter, add caption, re-add delimiter
                img_base = img.rstrip(_IMG)
                if "|" in img_base:
                    parts.append(img)  # already has caption
                else:
                    parts.append(f"{img_base}|{caption}{_IMG}")
            else:
                parts.append(img)
        if legend:
            parts.append(legend)

        # Also extract any non-poem table rows (letter keys in normal rows)
        key_rows = []
        rows = re.split(r"\|-", content)
        for row in rows:
            if _VERSE in row or img_pat.search(row):
                continue
            if re.search(r"\{\{(?:center|sc)\|", row):
                continue  # caption row, already extracted
            cleaned_row = re.sub(r"\{\{[^{}]*\}\}", "", row)
            cells = re.findall(r"\|([^|\n]+)", cleaned_row)
            cells = [c.strip() for c in cells
                     if c.strip()
                     and not re.match(r"^(?:colspan|rowspan|width|style|align|class|cellpadding|nowrap|valign|border|bgcolor|height)[\s=\|]", c.strip())
                     and c.strip() not in ("}",)]
            if cells:
                if any(re.search(r"<br\s*/?>", c, re.IGNORECASE) for c in cells):
                    split_cells = [re.split(r"<br\s*/?>", c, flags=re.IGNORECASE) for c in cells]
                    max_sub = max(len(sc) for sc in split_cells)
                    for sc in split_cells:
                        while len(sc) < max_sub:
                            sc.append("")
                    for sub_i in range(max_sub):
                        sub_row = [sc[sub_i].strip() for sc in split_cells]
                        if any(sub_row):
                            key_rows.append(" | ".join(sub_row))
                else:
                    key_rows.append(" | ".join(cells))
        if key_rows:
            parts.append(
                f"{_TBL}TABLE\n" + "\n".join(key_rows) + f"\n{_TBL}"
            )

        result = "\n\n".join(parts)
        return f"\n\n{result}\n\n" if result else ""

    # Check for table caption (|+ ...) — indicates headers follow
    caption_match = re.search(r"\|\+\s*(.*?)(?:\n|$)", content)
    caption = ""
    has_caption = False
    if caption_match:
        has_caption = True
        cap_text = re.sub(r"\{\{[^{}]*\}\}", "", caption_match.group(1)).strip()
        if cap_text:
            caption = cap_text

    # Try to extract table rows as simple text
    rows = re.split(r"\|-", content)
    text_rows = []
    for row in rows:
        # Skip caption rows
        if "|+" in row:
            continue
        # Strip all remaining templates from row
        cleaned_row = re.sub(r"\{\{[^{}]*\}\}", "", row)
        # Extract cell values
        cells = re.findall(r"\|([^|\n]+)", cleaned_row)
        cells = [c.strip() for c in cells
                 if c.strip()
                 and not re.match(r"^(?:colspan|rowspan|width|style|align|class|cellpadding|nowrap|valign|border|bgcolor|height)[\s=\|]", c.strip())
                 and c.strip() not in ("}",)]
        if cells:
            # Expand <br>-stacked cells into multiple rows.
            # If any cell contains <br>, split all cells on <br>, zip them
            # row-by-row, and emit one output row per sub-row.
            if any(re.search(r"<br\s*/?>", c, re.IGNORECASE) for c in cells):
                split_cells = [re.split(r"<br\s*/?>", c, flags=re.IGNORECASE) for c in cells]
                max_sub = max(len(sc) for sc in split_cells)
                for sc in split_cells:
                    while len(sc) < max_sub:
                        sc.append("")
                for sub_i in range(max_sub):
                    sub_row = [sc[sub_i].strip() for sc in split_cells]
                    if any(sub_row):
                        text_rows.append(" | ".join(sub_row))
            else:
                text_rows.append(" | ".join(cells))

    parts = []
    if img_markers:
        parts.extend(img_markers)
    if text_rows:
        # Mark first row as header if table had a caption
        header_marker = "H" if has_caption else ""
        table_text = "\n".join(text_rows)
        parts.append(f"{_TBL}TABLE{header_marker}\n{table_text}\n{_TBL}")

    result = "\n\n".join(parts)
    return f"\n\n{result}\n\n" if result else ""


def _shoulder_to_heading(m: re.Match) -> str:
    content = m.group(1)
    # Strip formatting params (width=, align=, section=)
    content = re.sub(r"(?:width|align|section)=[^|]*\|?", "", content)
    # Unwrap nested font-size templates: {{Fs|108%|text}} -> text
    content = re.sub(r"\{\{Fs\|[^|]*\|([^{}]*)\}\}", r"\1", content, flags=re.IGNORECASE)
    content = re.sub(r"\{\{[^{}]*\}\}", "", content)
    content = re.sub(r"'''", "", content)
    content = re.sub(r"<br\s*/?>", " ", content, flags=re.IGNORECASE)
    content = content.strip("| \n")
    if content:
        return f"\n\n{_FMT}SH{content}{_FMT}/SH\n\n"
    return "\n"


# ── Stage functions ─────────────────────────────────────────────────────


def _stage_01_normalize_line_endings(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text


def _stage_02_rescue_noinclude_images(text: str) -> str:
    text = re.sub(
        r"<noinclude>.*?</noinclude>", _rescue_noinclude,
        text, flags=re.DOTALL | re.IGNORECASE,
    )
    return text


def _stage_03_convert_section_tags(text: str) -> str:
    text = re.sub(
        r'<section\s+begin="([^"]+)"\s*/?>',
        lambda m: f"\n{_SEC}SEC:{m.group(1)}{_SEC}\n",
        text, flags=re.IGNORECASE,
    )
    text = re.sub(r'<section\s+end="[^"]*"\s*/?>', "", text, flags=re.IGNORECASE)
    return text


def _stage_04_strip_html_comments(text: str) -> str:
    # When a comment sits between two newlines, collapse to single newline
    text = re.sub(r"\n<!--.*?-->\n", "\n", text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return text


def _stage_05_convert_hieroglyphics(text: str) -> str:
    text = re.sub(
        r"<hiero>(.*?)</hiero>",
        lambda m: f"[hieroglyph: {m.group(1).strip()}]",
        text, flags=re.DOTALL | re.IGNORECASE,
    )
    return text


def _stage_06_unwrap_poem_wrappers(text: str) -> str:
    text = re.sub(
        r"\{\{block center\|(<poem>.*?</poem>)\}\}",
        r"\1",
        text, flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(
        r"\{\{center\|(<poem>.*?</poem>)\}\}",
        r"\1",
        text, flags=re.DOTALL | re.IGNORECASE,
    )
    return text


def _stage_07_convert_fine_print(text: str) -> str:
    text = re.sub(
        r"\{\{EB1911 Fine Print\|([^{}]+)\}\}",
        _fine_print_handler,
        text, flags=re.IGNORECASE,
    )
    return text


def _stage_08_convert_poems(text: str) -> str:
    text = re.sub(r"<poem>(.*?)</poem>", _poem_to_marker, text, flags=re.DOTALL | re.IGNORECASE)
    return text


def _stage_09_convert_math(text: str) -> str:
    text = re.sub(
        r"<math>(.*?)</math>",
        lambda m: f"{_MATH}MATH:{m.group(1)}{_MATH}",
        text, flags=re.DOTALL | re.IGNORECASE,
    )
    return text


def _stage_10_convert_plate_tables(text: str) -> str:
    def _maybe_plate_table(m: re.Match) -> str:
        table_html = m.group(0)
        image_count = len(re.findall(r"\[\[(?:Image|File):", table_html, re.I))
        if image_count >= 3:
            parsed = _parse_plate_table(table_html)
            if parsed:
                return "\n\n" + parsed + "\n\n"
        return table_html  # not a plate table, leave for later processing
    text = re.sub(r"<table[^>]*>.*?</table>", _maybe_plate_table, text, flags=re.DOTALL | re.IGNORECASE)
    return text


def _stage_11_convert_refs(text: str) -> str:
    # Remove self-closing ref tags FIRST (back-references to named notes)
    # so they don't steal </ref> closings from content refs
    text = re.sub(r"<ref[^/]*/\s*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<ref[^>]*>(.*?)</ref>", _ref_to_marker, text, flags=re.DOTALL | re.IGNORECASE)
    return text


def _stage_12_convert_images(text: str) -> str:
    text = re.sub(
        r"\[\[(?:File|Image):([^\]]+)\]\]",
        _image_to_marker,
        text,
        flags=re.IGNORECASE,
    )
    return text


def _stage_13_convert_link_templates(text: str) -> str:
    text = re.sub(r"\{\{(?:EB1911|DNB)\s+lkpl\|([^{}]+)\}\}", _lkpl_to_marker, text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{1911link\|([^{}|]*)\}\}", lambda m: f"{_LNK}{m.group(1)}|{m.group(1)}{_LNK}", text, flags=re.IGNORECASE)
    # {{EB1911 article link|Target}} — explicit cross-references
    text = re.sub(r"\{\{EB1911 article link\|([^{}|]*)\}\}", lambda m: f"{_LNK}{m.group(1)}|{m.group(1)}{_LNK}", text, flags=re.IGNORECASE)
    # {{11link|Target}} — another article link form
    text = re.sub(r"\{\{11link\|([^{}|]*)\}\}", lambda m: f"{_LNK}{m.group(1)}|{m.group(1)}{_LNK}", text, flags=re.IGNORECASE)
    return text


def _stage_14_convert_wikilinks(text: str) -> str:
    text = re.sub(r"\[\[([^\]]+)\]\]", _wikilink_to_marker, text)
    return text


def _stage_15_convert_wiki_tables(text: str) -> str:
    text = re.sub(r"\{\|.*?\|\}", _convert_table, text, flags=re.DOTALL)
    return text


def _stage_16_unwrap_content_templates(text: str) -> str:
    text = re.sub(r"\{\{Greek\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{polytonic\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{Hebrew\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)

    # Convert fraction templates to Unicode or text fractions
    text = re.sub(
        r"\{\{(?:EB1911 tfrac|sfrac)\|([^{}|]+?)(?:\|([^{}|]+?))?\}\}",
        lambda m: _to_fraction(m.group(1).strip(), (m.group(2) or "").strip()),
        text, flags=re.IGNORECASE,
    )
    # {{sub|3}} -> ₃   (Unicode subscript)
    # {{sup|2}} -> ²   (Unicode superscript)
    # Small caps → marker (used for author names, cross-references)
    text = re.sub(r"\{\{sc\|([^{}|]*)\}\}", lambda m: f"{_FMT}SC{m.group(1)}{_FMT}/SC", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{asc\|([^{}|]*)\}\}", lambda m: f"{_FMT}SC{m.group(1)}{_FMT}/SC", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{uc\|([^{}|]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{nowrap\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{lang\|[^{}|]*\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{abbr\|([^{}|]*)\|[^{}]*\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{tooltip\|([^{}|]*)\|[^{}]*\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{sic\}\}", "[sic]", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{smaller\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{larger\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\{\{sub\|([^{}|]*)\}\}",
        lambda m: _to_unicode_sub(m.group(1)),
        text, flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\{\{sup\|([^{}|]*)\}\}",
        lambda m: _to_unicode_sup(m.group(1)),
        text, flags=re.IGNORECASE,
    )
    return text


def _stage_17_convert_shoulder_headings(text: str) -> str:
    text = re.sub(
        r"\n?\{\{EB1911 Shoulder Heading\w*\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}\n?",
        _shoulder_to_heading, text, flags=re.IGNORECASE,
    )
    return text


def _stage_18_unwrap_layout_templates(text: str) -> str:
    for unwrap_name in ["center", "c", "EB1911 Fine Print"]:
        text = re.sub(
            r"\{\{" + re.escape(unwrap_name) + r"\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}",
            r"\1", text, flags=re.IGNORECASE,
        )
    return text


def _stage_19_strip_presentation_templates(text: str) -> str:
    for name in [
        "csc", "fs", "ts", "ditto",
        "eb1911 page heading", "eb1911 fine print/s", "eb1911 fine print/e",
        "eb1911 shoulder headingsmall", "eb1911 shoulder heading",
    ]:
        pattern = r"\{\{\s*" + re.escape(name) + r"\b.*?\}\}"
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
    return text


def _stage_20_strip_remaining_templates(text: str) -> str:
    # General iterative template stripping.
    # This removes innermost templates first, which helps with nesting.
    # Exclude control characters (\x00-\x08) so preserved markers aren't consumed.
    previous = None
    while text != previous:
        previous = text
        text = re.sub(r"\{\{[^{}\x00-\x08]*\}\}", "", text)

    # Remove orphaned closing braces left by nested template cleanup
    text = re.sub(r"^\s*\}\}+\s*$", "", text, flags=re.MULTILINE)
    # Also strip trailing braces at end of lines (e.g. "...some text. }}")
    text = re.sub(r"\s*\}\}+\s*$", "", text, flags=re.MULTILINE)

    # Remove orphaned wiki table markers that survived table stripping
    text = re.sub(r"^\s*\|\}+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\{\|\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\|-\s*$", "", text, flags=re.MULTILINE)

    # Remove any remaining orphaned {{ and }}
    # At this point all valid markers use control char delimiters, not braces
    text = text.replace("{{", "").replace("}}", "")
    return text


def _stage_21_convert_sub_sup(text: str) -> str:
    # Strip wiki italic markers ('') inside sub/sup first — otherwise they
    # cluster with adjacent '' and create false ''' bold sequences.
    def _clean_sub(m: re.Match) -> str:
        return _to_unicode_sub(m.group(1).replace("''", ""))
    def _clean_sup(m: re.Match) -> str:
        return _to_unicode_sup(m.group(1).replace("''", ""))
    text = re.sub(
        r"<sub[^>]*>(.*?)</sub>",
        _clean_sub,
        text, flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(
        r"<sup[^>]*>(.*?)</sup>",
        _clean_sup,
        text, flags=re.DOTALL | re.IGNORECASE,
    )
    return text


def _stage_22_convert_bold_italic(text: str) -> str:
    # Convert wiki bold and italic to markers.
    # First handle bold-italic (5 quotes), then bold (3), then italic (2).
    # Also normalize stray 4-quote sequences that arise when italic markers
    # cluster after HTML tag removal (e.g., ''e''''ˣ'' from math expressions).
    text = re.sub(r"'''''(.*?)'''''", lambda m: f"{_FMT}B{_FMT}I{m.group(1)}{_FMT}/I{_FMT}/B", text, flags=re.DOTALL)
    text = re.sub(r"''''", "'''", text)  # normalize 4 quotes to 3 (trailing apostrophe lost but prevents mispairing)
    text = re.sub(r"'''(.*?)'''", lambda m: f"{_FMT}B{m.group(1)}{_FMT}/B", text, flags=re.DOTALL)
    text = re.sub(r"''(.*?)''", lambda m: f"{_FMT}I{m.group(1)}{_FMT}/I", text, flags=re.DOTALL)
    return text


def _stage_23_strip_html_tags(text: str) -> str:
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)
    return text


def _stage_24_decode_html_entities(text: str) -> str:
    text = html.unescape(text)
    return text


def _stage_25_normalize_whitespace(text: str) -> str:
    # Normalize odd spacing left by entity decoding/template removal
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)

    # Clean up spaces around punctuation a bit
    text = re.sub(r" +([,.;:!?])", r"\1", text)
    text = re.sub(r"\( ", "(", text)
    text = re.sub(r" \)", ")", text)

    # Trim trailing whitespace from each line, preserving newline structure.
    # Single \n = hard wrap (column break); \n\n = paragraph break.
    text = "\n".join(line.rstrip() for line in text.split("\n"))

    # Collapse 3+ consecutive newlines to paragraph break, drop leading/trailing
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def _stage_26_finalize_markers(text: str) -> str:
    # Convert image markers from internal delimiters to readable format
    text = text.replace(f"{_IMG}IMG:", "{{IMG:").replace(_IMG, "}}")

    # Convert footnote markers to readable format: «FN:text«/FN»
    text = text.replace(f"{_FN}FN:", "\u00abFN:").replace(_FN, "\u00ab/FN\u00bb")

    # Convert PRE markers to readable format (must come BEFORE table conversion)
    text = text.replace(f"{_PRE}PRE\n", "\u00abPRE:").replace(f"\n{_PRE}", "\u00ab/PRE\u00bb")
    def _protect_pre_newlines(m):
        return m.group(0).replace("\n", _TBL)
    text = re.sub(r"\u00abPRE:.*?\u00ab/PRE\u00bb", _protect_pre_newlines, text, flags=re.DOTALL)

    # Convert table markers to readable format.
    # Use _TBL as line separators within tables to prevent reflow from joining rows.
    # Tables with headers use {{TABLEH: instead of {{TABLE:
    text = text.replace(f"{_TBL}TABLEH\n", "{{TABLEH:").replace(f"{_TBL}TABLE\n", "{{TABLE:").replace(f"\n{_TBL}", "}TABLE}")
    # Convert internal newlines within table blocks to _TBL to protect from reflow
    def _protect_table_newlines(m: re.Match) -> str:
        return m.group(0).replace("\n", _TBL)
    text = re.sub(r"\{\{TABLE:.*?\}TABLE\}", _protect_table_newlines, text, flags=re.DOTALL)

    # Convert verse markers to readable format (protect newlines like tables)
    def _protect_verse_newlines(m: re.Match) -> str:
        return m.group(0).replace("\n", _TBL)
    text = text.replace(f"{_VERSE}VERSE\n", "{{VERSE:").replace(f"\n{_VERSE}", "}VERSE}")
    text = re.sub(r"\{\{VERSE:.*?\}VERSE\}", _protect_verse_newlines, text, flags=re.DOTALL)

    # Convert math markers to readable format
    text = re.sub(
        re.escape(_MATH) + r"MATH:(.*?)" + re.escape(_MATH),
        lambda m: f"\u00abMATH:{m.group(1)}\u00ab/MATH\u00bb",
        text, flags=re.DOTALL,
    )

    # Convert section markers to readable format
    text = re.sub(
        re.escape(_SEC) + r"SEC:([^" + re.escape(_SEC) + r"]+)" + re.escape(_SEC),
        lambda m: f"\u00abSEC:{m.group(1)}\u00bb",
        text,
    )

    # Convert bold/italic/small-caps markers to readable format
    text = text.replace(f"{_FMT}B", "\u00abB\u00bb").replace(f"{_FMT}/B", "\u00ab/B\u00bb")
    text = text.replace(f"{_FMT}I", "\u00abI\u00bb").replace(f"{_FMT}/I", "\u00ab/I\u00bb")
    text = text.replace(f"{_FMT}SC", "\u00abSC\u00bb").replace(f"{_FMT}/SC", "\u00ab/SC\u00bb")
    text = text.replace(f"{_FMT}SH", "\u00abSH\u00bb").replace(f"{_FMT}/SH", "\u00ab/SH\u00bb")

    # Convert link markers to readable format: «LN:Target|Display«/LN»
    text = re.sub(
        re.escape(_LNK) + r"([^|" + re.escape(_LNK) + r"]+)\|([^" + re.escape(_LNK) + r"]+)" + re.escape(_LNK),
        lambda m: f"\u00abLN:{m.group(1)}|{m.group(2)}\u00ab/LN\u00bb",
        text,
    )

    return text


# ── Pipeline ────────────────────────────────────────────────────────────

STAGES = [
    _stage_01_normalize_line_endings,
    _stage_02_rescue_noinclude_images,
    _stage_03_convert_section_tags,
    _stage_04_strip_html_comments,
    _stage_05_convert_hieroglyphics,
    _stage_06_unwrap_poem_wrappers,
    _stage_07_convert_fine_print,
    _stage_08_convert_poems,
    _stage_09_convert_math,
    _stage_10_convert_plate_tables,
    _stage_11_convert_refs,
    _stage_12_convert_images,
    _stage_13_convert_link_templates,
    _stage_14_convert_wikilinks,
    _stage_15_convert_wiki_tables,
    _stage_16_unwrap_content_templates,
    _stage_17_convert_shoulder_headings,
    _stage_18_unwrap_layout_templates,
    _stage_19_strip_presentation_templates,
    _stage_20_strip_remaining_templates,
    _stage_21_convert_sub_sup,
    _stage_22_convert_bold_italic,
    _stage_23_strip_html_tags,
    _stage_24_decode_html_entities,
    _stage_25_normalize_whitespace,
    _stage_26_finalize_markers,
]


def clean_wikisource_page_text(text: str) -> str:
    for stage in STAGES:
        text = stage(text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=int, required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0,
                        help="Max pages to fetch this invocation (0 = no limit)")
    args = parser.parse_args()

    print("Starting fetch...")
    print(f"Volume: {args.volume}")
    print(f"Page range: {args.start} to {args.end}")
    print(f"Outdir arg: {args.outdir}")

    if args.end < args.start:
        raise SystemExit("--end must be >= --start")

    outdir = args.outdir.resolve()
    print(f"Resolved outdir: {outdir}")

    outdir.mkdir(parents=True, exist_ok=True)
    print(f"Outdir exists: {outdir.exists()}")

    fetched_this_run = 0
    for page_number in range(args.start, args.end + 1):
        outfile = outdir / f"vol{args.volume:02d}-page{page_number:04d}.json"
        if outfile.exists():
            continue

        if args.limit and fetched_this_run >= args.limit:
            print(f"Reached limit of {args.limit} pages, stopping.")
            break

        raw = fetch_page_wikitext(args.volume, page_number)
        cleaned = clean_wikisource_page_text(raw)
        fetched_this_run += 1
        time.sleep(3)  # polite delay between requests

        payload = {
            "volume": args.volume,
            "page_number": page_number,
            "source": "wikisource",
            "title": f"Page:EB1911 - Volume {args.volume:02d}.djvu/{page_number}",
            "raw_text": raw,
            "cleaned_preview": cleaned,
        }

        outfile = outdir / f"vol{args.volume:02d}-page{page_number:04d}.json"
        outfile.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {outfile}")

    print("Done.")


if __name__ == "__main__":
    main()

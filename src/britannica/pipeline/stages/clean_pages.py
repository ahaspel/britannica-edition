import json
import re
from pathlib import Path

from britannica.cleaners.headers_footers import strip_headers
from britannica.cleaners.hyphenation import fix_hyphenation
from britannica.cleaners.reflow import reflow_paragraphs
from britannica.cleaners.unicode import normalize_unicode, replace_print_artifacts
from britannica.cleaners.whitespace import normalize_whitespace
from britannica.db.models.source_page import SourcePage
from britannica.db.session import SessionLocal


_CORRECTIONS: dict | None = None


def _load_corrections() -> dict:
    """Load data/corrections.json once.  Single source of truth for
    transcription-typo fixes; consumed only here, in clean_pages, so
    that all downstream stages (detect_boundaries, transform_articles)
    operate on already-corrected text."""
    global _CORRECTIONS
    if _CORRECTIONS is not None:
        return _CORRECTIONS
    p = Path("data/corrections.json")
    if not p.exists():
        _CORRECTIONS = {}
        return _CORRECTIONS
    with p.open(encoding="utf-8") as f:
        _CORRECTIONS = json.load(f)
    return _CORRECTIONS


def _apply_corrections(text: str, volume: int) -> str:
    """Apply per-volume corrections.json entries to `text`.  Each entry
    is a literal `{from, to}` replacement applied via str.replace, so
    repeat application is a no-op."""
    corrs = _load_corrections()
    vol_prefix = f"{volume}:"
    for key, entries in corrs.items():
        if not key.startswith(vol_prefix):
            continue
        if not isinstance(entries, list):
            continue
        for c in entries:
            if isinstance(c, dict) and "from" in c and "to" in c:
                text = text.replace(c["from"], c["to"])
    return text

# Control characters \x00-\x08 are internal fetch delimiters that should
# have been converted to «»-style markers.  Strip any that leaked through.
_STRAY_CONTROL = re.compile(r"[\x00-\x08]")

# Wiki table markup that leaked through the fetch table converter.
# Matches {|...  |-...  |}  and cell attribute prefixes like colspan="3"|
_WIKI_TABLE_OPEN = re.compile(r"\{\|[^\n]*(?:\n|$)")
_WIKI_TABLE_ROW = re.compile(r"\|-[a-z]+=\"[^\"]*\"[^\n]*", re.IGNORECASE)
_WIKI_TABLE_CLOSE = re.compile(r"^\|\}\s*$", re.MULTILINE)
_CELL_ATTR = re.compile(
    r"\|\s*(?:colspan|rowspan|style|align|valign|width|class|bgcolor|"
    r"cellpadding|cellspacing|border|height|nowrap)[^|]*\|",
    re.IGNORECASE,
)


_FN_OPEN = "\u00abFN:"
_FN_CLOSE = "\u00ab/FN\u00bb"


def _fix_unclosed_footnotes(text: str) -> str:
    """Close any «FN: markers that lack a matching «/FN».

    These typically occur when a footnote in the original wiki markup
    spans across a table boundary created during fetch processing.
    We close the footnote at the next table boundary, paragraph break,
    or end of text.
    """
    result = []
    pos = 0
    depth = 0
    while pos < len(text):
        fn_open = text.find(_FN_OPEN, pos)
        fn_close = text.find(_FN_CLOSE, pos)

        if depth == 0:
            # Not inside a footnote — look for next open
            if fn_open == -1:
                result.append(text[pos:])
                break
            result.append(text[pos:fn_open])
            result.append(_FN_OPEN)
            pos = fn_open + len(_FN_OPEN)
            depth = 1
        else:
            # Inside a footnote — find close or a boundary that forces close
            if fn_close != -1 and (fn_open == -1 or fn_close < fn_open):
                # Normal close
                result.append(text[pos:fn_close + len(_FN_CLOSE)])
                pos = fn_close + len(_FN_CLOSE)
                depth = 0
            else:
                # No close before next open (or end of text) — force close
                # at next table boundary or paragraph break
                boundary = None
                for marker in ["}TABLE}", "\n\n", "}}",]:
                    idx = text.find(marker, pos)
                    if idx != -1 and (boundary is None or idx < boundary):
                        boundary = idx
                if boundary is not None and (fn_open == -1 or boundary < fn_open):
                    result.append(text[pos:boundary])
                    result.append(_FN_CLOSE)
                    pos = boundary
                    depth = 0
                elif fn_open != -1:
                    # Nested open — close current before opening new
                    result.append(text[pos:fn_open])
                    result.append(_FN_CLOSE)
                    result.append(_FN_OPEN)
                    pos = fn_open + len(_FN_OPEN)
                else:
                    # End of text — force close
                    result.append(text[pos:])
                    result.append(_FN_CLOSE)
                    break
    return "".join(result)


def _fix_unclosed_tables(text: str) -> str:
    """Close any {{TABLE markers that lack a matching }TABLE}.

    Also remove orphaned }TABLE} without a matching open.
    """
    opens = [m.start() for m in re.finditer(r"\{\{TABLE", text)]
    closes = [m.start() for m in re.finditer(r"\}TABLE\}", text)]

    if len(opens) == len(closes):
        return text

    if len(opens) > len(closes):
        # Find unclosed opens by walking matched pairs
        close_set = set()
        for o in opens:
            # Find next close after this open that isn't already matched
            for c in closes:
                if c > o and c not in close_set:
                    close_set.add(c)
                    break
            else:
                # No close found — insert one at next paragraph break
                para = text.find("\n\n", o)
                if para == -1:
                    text = text + "}TABLE}"
                else:
                    text = text[:para] + "}TABLE}" + text[para:]
                return _fix_unclosed_tables(text)  # re-check after insertion

    if len(closes) > len(opens):
        # Remove orphaned closes (work backwards to keep positions stable)
        open_set = set()
        for c in reversed(closes):
            matched = False
            for o in reversed(opens):
                if o < c and o not in open_set:
                    open_set.add(o)
                    matched = True
                    break
            if not matched:
                text = text[:c] + text[c + 7:]  # remove "}TABLE}"
                return _fix_unclosed_tables(text)

    return text


def _clean_plate_layout(text: str) -> str:
    """Pair images with their numbered captions on plate pages.

    Plate pages have images in grid rows with numbered captions that
    may appear in ||lines, {{TABLE:...}TABLE} blocks, or bare |lines.
    This function extracts all numbered captions from everywhere,
    pairs each with its corresponding image by number, and outputs
    clean {{IMG:filename|N. CAPTION}} markers.
    """
    # Only process pages that look like plates (many images)
    img_count = text.count("{{IMG:")
    if img_count < 3:
        return text

    # Collect all images in order
    images = [m.group(1) for m in re.finditer(r"\{\{IMG:([^|}]+)", text)]

    # Extract ALL numbered captions from the entire text
    # They appear as "N. CAPTION TEXT" in various contexts
    captions = {}
    # Search the whole text for numbered captions (inside tables, pipes, etc.)
    for m in re.finditer(r"(\d+)\.\s+([A-Z][A-Z\s,.:;()\-']+)", text):
        num = int(m.group(1))
        cap = m.group(2).strip().rstrip(".,;|")
        # Skip if it looks like a date or page reference
        if len(cap) < 3:
            continue
        if num not in captions or len(cap) > len(captions[num]):
            captions[num] = cap

    if not captions:
        return text

    # Match captions to images by keyword similarity.
    # Image filenames contain descriptive words (e.g. "Limestone Lion")
    # that match caption text (e.g. "LIMESTONE LION").
    def _img_words(filename):
        # Strip prefix like "EB1911 Egypt - Earliest Art - "
        name = filename.rsplit("/", 1)[-1]
        name = re.sub(r"\.jpg$|\.png$", "", name, flags=re.IGNORECASE)
        # Take words after the last " - "
        if " - " in name:
            name = name.rsplit(" - ", 1)[-1]
        return set(re.findall(r"[A-Za-z]{3,}", name.upper()))

    sorted_caps = sorted(captions.items())
    used_images = set()
    paired = []

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
            paired.append((best_img, f"{{{{IMG:{images[best_img]}|{num}. {cap}}}}}"))
        else:
            paired.append((999, f"{num}. {cap}"))

    # Add unmatched images
    for i, img in enumerate(images):
        if i not in used_images:
            paired.append((i, f"{{{{IMG:{img}}}}}"))

    # Sort by original image order
    paired.sort(key=lambda x: x[0])
    paired = [p[1] for p in paired]

    # Extract the plate title (first non-empty lines before images/tables)
    title_lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("{{IMG:") or line.startswith("{{TABLE"):
            break
        if line.startswith("||") or line.startswith("|"):
            break
        title_lines.append(line)

    result = "\n".join(title_lines)
    if result:
        result += "\n\n"
    result += "\n\n".join(paired)
    return result


# Static mapping of <score> tags to pre-rendered Wikimedia images.
# Key: (volume, page_number, occurrence_index)
# Value: URL of the rendered PNG on upload.wikimedia.org
_SCORE_IMAGES = {
    (3, 221, 0): "https://upload.wikimedia.org/score/h/z/hzcdxxolvqb8f88rf1kv99xpbkz4fhl/hzcdxxol.png",
    (3, 221, 1): "https://upload.wikimedia.org/score/8/m/8muj660hon0gdc23klev5oueja71g2e/8muj660h.png",
    (3, 221, 2): "https://upload.wikimedia.org/score/l/e/le30qszwd023fbi5l5p72zzgp0qif4z/le30qszw.png",
    (3, 221, 3): "https://upload.wikimedia.org/score/t/a/ta4vp64mow2a4xgtut6yrr587tjqvwq/ta4vp64m.png",
    (3, 971, 0): "https://upload.wikimedia.org/score/l/e/lexak41zsl71g5wdztqfen2titdlq9w/lexak41z.png",
    (3, 972, 0): "https://upload.wikimedia.org/score/c/6/c6ls5kqiltjw1nu8qc0qh3r85v60gdx/c6ls5kqi.png",
    (6, 415, 0): "https://upload.wikimedia.org/score/9/i/9iavthct92fgw9tjxwi3s57m4yb9fw0/9iavthct.png",
    (6, 416, 0): "https://upload.wikimedia.org/score/i/y/iy808fgeauppb3nth1mdmfhjgi6rpy3/iy808fge.png",
    (6, 416, 1): "https://upload.wikimedia.org/score/5/y/5ytbiminte2jgttcfyl2swwg254v2i0/5ytbimin.png",
    (6, 416, 2): "https://upload.wikimedia.org/score/a/o/ao59rovwbfgbmxdrbumkluxcgxg7qoj/ao59rovw.png",
    (6, 416, 3): "https://upload.wikimedia.org/score/7/y/7yn0x3i1tb37t4fg4v68yj3n4pnh1vi/7yn0x3i1.png",
}

_SCORE_TAG = re.compile(r"<score[^>]*>.*?</score>", re.DOTALL)


def _replace_score_tags(text: str, volume: int, page_number: int) -> str:
    """Replace <score> tags with {{IMG:url|Musical notation}} markers.

    In article-as-unit processing, text contains \x01PAGE:N\x01 markers.
    Each score tag is looked up by its page number and index within that page.
    """
    matches = list(_SCORE_TAG.finditer(text))
    if not matches:
        return text

    # Build page-number map from PAGE markers
    page_markers = list(re.finditer(r"\x01PAGE:(\d+)\x01", text))

    def _page_for_pos(pos):
        """Find which page a position belongs to."""
        current_page = page_number  # default if no markers
        for pm in page_markers:
            if pm.start() <= pos:
                current_page = int(pm.group(1))
            else:
                break
        return current_page

    # Group scores by page for correct indexing
    scores_by_page: dict[int, int] = {}  # page -> count so far
    for i, m in reversed(list(enumerate(matches))):
        pg = _page_for_pos(m.start())
        # Count how many scores on this page come before this one
        idx = sum(1 for j, m2 in enumerate(matches)
                  if j < i and _page_for_pos(m2.start()) == pg)
        url = _SCORE_IMAGES.get((volume, pg, idx))
        if url:
            # Use a pre-rendered marker that won't be re-extracted as an image.
            # The viewer handles {{IMG:...}} at render time; using the full URL
            # prevents the wiki-image extractor from matching it (it expects
            # [[File:...]] or bare filenames, not URLs).
            replacement = f'{{{{IMG:{url}|Musical notation}}}}'
        else:
            replacement = "[Musical notation]"
        text = text[:m.start()] + replacement + text[m.end():]
    return text


def _convert_img_float(text: str) -> str:
    """Convert leaked 'img float|file=...|cap=...' to {{IMG:...}} markers."""
    def _replace(m):
        s = m.group(0)
        file_m = re.search(r"\|file=([^|]+)", s)
        cap_m = re.search(r"\|cap=([^|]+)", s)
        if not file_m:
            return ""  # can't salvage without a filename
        filename = file_m.group(1).strip()
        caption = cap_m.group(1).strip() if cap_m else ""
        if caption:
            return f"{{{{IMG:{filename}|{caption}}}}}"
        return f"{{{{IMG:{filename}}}}}"
    return re.sub(
        r"[Ii]mg float\s*\|[^\n]*",
        _replace, text,
    )


def _clean_leaked_table_markup(text: str) -> str:
    """Remove wiki table markup that wasn't converted during fetch."""
    # Don't touch anything inside {{TABLE:...}TABLE} blocks
    parts = re.split(r"(\{\{TABLE.*?\}TABLE\})", text, flags=re.DOTALL)
    for i in range(0, len(parts), 2):  # only non-table parts
        p = parts[i]
        p = _WIKI_TABLE_OPEN.sub("", p)
        p = _WIKI_TABLE_ROW.sub("", p)
        p = _WIKI_TABLE_CLOSE.sub("", p)
        p = _CELL_ATTR.sub("| ", p)
        parts[i] = p
    return "".join(parts)


def clean_pages(volume: int) -> int:
    session = SessionLocal()
    try:
        pages = session.query(SourcePage).filter(SourcePage.volume == volume).all()

        for page in pages:
            # Apply corrections.json to `wikitext` (which downstream
            # stages read).  raw_text is the unprocessed source; the
            # processed/normalized wikitext is what corrections.json
            # entries are written against (table rewrites match the
            # wikitext format, not raw_text).
            if page.wikitext:
                corrected_wt = _apply_corrections(page.wikitext, volume)
                if corrected_wt != page.wikitext:
                    page.wikitext = corrected_wt

            text = page.raw_text
            # Replace <score> tags before any other processing
            text = _replace_score_tags(text, volume, page.page_number)
            text = normalize_unicode(text)
            text = replace_print_artifacts(text)
            text, _removed_headers = strip_headers(text)
            text, _hyphen_changes = fix_hyphenation(text)
            text = reflow_paragraphs(text)
            text = normalize_whitespace(text)
            text = _STRAY_CONTROL.sub("", text)
            # Strip residual wiki italic markers ('') that survived fetch
            text = text.replace("''", "")
            # Pair images with captions on plate pages
            text = _clean_plate_layout(text)
            # Convert leaked image float markup to IMG markers
            text = _convert_img_float(text)
            # Strip leaked wiki table markup that wasn't converted during fetch
            text = _clean_leaked_table_markup(text)
            # Close any unclosed footnote markers
            text = _fix_unclosed_footnotes(text)
            # Close any unclosed table markers
            text = _fix_unclosed_tables(text)
            page.cleaned_text = text

        session.commit()
        return len(pages)
    finally:
        session.close()
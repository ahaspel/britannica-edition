#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import html
import time
from pathlib import Path
import requests

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
            wait = 60 * (attempt + 1)  # 60s, 120s, 180s
            print(f"  Rate limited, waiting {wait}s for cooldown...")
            time.sleep(wait)
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
        raise ValueError(f"Missing page: {title}")

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
            marker = f"\x00IMG:{img}\x00"
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
        return f"\n\n\x00IMG:{filename}|{caption}\x00\n\n"
    return f"\n\n\x00IMG:{filename}\x00\n\n"


def clean_wikisource_page_text(text: str) -> str:
    # Normalize line endings early
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove noinclude blocks completely
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML comments (e.g. <!-- column 2 --> Wikisource transcription markers).
    # When a comment sits between two newlines (\n<!--...-->\n), collapse to single
    # newline so the surrounding text stays joined as a hard wrap, not a paragraph break.
    text = re.sub(r"\n<!--.*?-->\n", "\n", text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Parse HTML plate tables (these use <table> not {| wiki syntax)
    # Detect by: contains <table> with multiple [[Image: links
    def _maybe_plate_table(m: re.Match) -> str:
        table_html = m.group(0)
        image_count = len(re.findall(r"\[\[(?:Image|File):", table_html, re.I))
        if image_count >= 3:
            parsed = _parse_plate_table(table_html)
            if parsed:
                return "\n\n" + parsed + "\n\n"
        return table_html  # not a plate table, leave for later processing
    text = re.sub(r"<table[^>]*>.*?</table>", _maybe_plate_table, text, flags=re.DOTALL | re.IGNORECASE)

    # Convert ref tags to inline footnote markers (survive template stripping)
    def _ref_to_marker(match: re.Match) -> str:
        content = match.group(1).strip()
        # Clean basic wiki markup from footnote content
        content = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", content)
        content = re.sub(r"\[\[([^\]]+)\]\]", r"\1", content)
        content = content.replace("'''", "").replace("''", "")
        return f"\x01FN:{content}\x01"
    text = re.sub(r"<ref[^>]*>(.*?)</ref>", _ref_to_marker, text, flags=re.DOTALL | re.IGNORECASE)
    # Remove self-closing ref tags (back-references to named notes)
    text = re.sub(r"<ref[^/]*/\s*>", "", text, flags=re.IGNORECASE)

    # Replace file/image links with inline markers BEFORE table stripping
    text = re.sub(
        r"\[\[(?:File|Image):([^\]]+)\]\]",
        _image_to_marker,
        text,
        flags=re.IGNORECASE,
    )

    # Convert cross-reference templates to link markers BEFORE table stripping
    def _lkpl_to_marker(m: re.Match) -> str:
        parts = m.group(1).split("|")
        target = parts[0].strip()
        display = parts[1].strip() if len(parts) > 1 else target
        return f"\x03{target}|{display}\x03"
    text = re.sub(r"\{\{(?:EB1911|DNB)\s+lkpl\|([^{}]+)\}\}", _lkpl_to_marker, text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{1911link\|([^{}|]*)\}\}", lambda m: f"\x03{m.group(1)}|{m.group(1)}\x03", text, flags=re.IGNORECASE)

    # Convert regular wikilinks to link markers (skip File/Image/Author)
    def _wikilink_to_marker(m: re.Match) -> str:
        content = m.group(1)
        if re.match(r"(?i)^(File|Image|Author|Category):", content):
            return ""
        parts = content.split("|")
        target = parts[0].strip()
        display = parts[1].strip() if len(parts) > 1 else target
        return f"\x03{target}|{display}\x03"
    text = re.sub(r"\[\[([^\]]+)\]\]", _wikilink_to_marker, text)

    # Convert wikitable blocks: preserve image markers and extract table content
    def _convert_table(match: re.Match) -> str:
        content = match.group(0)

        # Extract image markers first
        img_markers = re.findall(r"\x00IMG:[^\x00]+\x00", content)

        # Try to extract table rows as simple text
        rows = re.split(r"\|-", content)
        text_rows = []
        for row in rows:
            # Strip all remaining templates from row
            cleaned_row = re.sub(r"\{\{[^{}]*\}\}", "", row)
            # Extract cell values
            cells = re.findall(r"\|([^|\n]+)", cleaned_row)
            cells = [c.strip() for c in cells
                     if c.strip()
                     and not re.match(r"^(?:colspan|rowspan|width|style|align|class|cellpadding)[\s=]", c.strip())
                     and c.strip() not in ("}",)]
            if cells:
                text_rows.append(" | ".join(cells))

        parts = []
        if img_markers:
            parts.extend(img_markers)
        if text_rows:
            # Wrap table content in markers so viewer can render it
            table_text = "\n".join(text_rows)
            parts.append(f"\x02TABLE\n{table_text}\n\x02")

        return "\n\n".join(parts) if parts else ""

    text = re.sub(r"\{\|.*?\|\}", _convert_table, text, flags=re.DOTALL)

    # Preserve content of a few useful one-argument templates
    # {{sc|e.m.f.}} -> e.m.f.
    # {{lang|fr|bonjour}} -> bonjour   (optional but handy)
    # {{sub|3}} -> 3   (preserve subscript digits so formulas stay recognizable)
    # {{sup|2}} -> 2
    text = re.sub(r"\{\{sc\|([^{}|]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{nowrap\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{lang\|[^{}|]*\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{su[bp]\|([^{}|]*)\}\}", r"\1", text, flags=re.IGNORECASE)

    # (lkpl and 1911link already converted to markers above)

    # Remove shoulder headings without leaving paragraph breaks —
    # these are marginal annotations, not text content.
    text = re.sub(
        r"\n\{\{EB1911 Shoulder Heading\w*\|[^}]*\}\}\n",
        "\n", text, flags=re.IGNORECASE,
    )

    # Remove common presentation/layout templates wholesale
    # These are the ones currently leaking figure debris.
    for name in [
        "center", "csc", "fs", "ts", "ditto",
        "eb1911 page heading", "eb1911 fine print/s", "eb1911 fine print/e",
        "eb1911 shoulder headingsmall", "eb1911 shoulder heading",
    ]:
        pattern = r"\{\{\s*" + re.escape(name) + r"\b.*?\}\}"
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)

    # General iterative template stripping.
    # This removes innermost templates first, which helps with nesting.
    previous = None
    while text != previous:
        previous = text
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)

    # Remove orphaned closing braces left by nested template cleanup
    text = re.sub(r"^\s*\}\}+\s*$", "", text, flags=re.MULTILINE)
    # Also strip trailing braces at end of lines (e.g. "...some text. }}")
    text = re.sub(r"\s*\}\}+\s*$", "", text, flags=re.MULTILINE)

    # Remove orphaned wiki table markers that survived table stripping
    text = re.sub(r"^\s*\|\}+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\{\|\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\|-\s*$", "", text, flags=re.MULTILINE)

    # (wikilinks already converted to markers above)

    # Preserve sub/sup content before stripping all tags
    text = re.sub(r"<su[bp][^>]*>(.*?)</su[bp]>", r"\1", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove remaining HTML/XML-like tags
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)

    # Remove wiki bold/italic markup
    text = text.replace("'''", "").replace("''", "")

    # Decode HTML entities like &nbsp; and &emsp;
    text = html.unescape(text)

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

    # Convert image markers from null-byte delimiters to readable format
    text = text.replace("\x00IMG:", "{{IMG:").replace("\x00", "}}")

    # Convert footnote markers to readable format
    text = text.replace("\x01FN:", "\u00abFN:").replace("\x01", "\u00bb")

    # Convert table markers to readable format.
    # Use \x02 as line separators within tables to prevent reflow from joining rows.
    text = text.replace("\x02TABLE\n", "{{TABLE:").replace("\n\x02", "}TABLE}")
    # Convert internal newlines within table blocks to \x02 to protect from reflow
    def _protect_table_newlines(m: re.Match) -> str:
        return m.group(0).replace("\n", "\x02")
    text = re.sub(r"\{\{TABLE:.*?\}TABLE\}", _protect_table_newlines, text, flags=re.DOTALL)

    # Convert link markers to readable format: «LN:Target|Display»
    text = re.sub(
        r"\x03([^|\x03]+)\|([^\x03]+)\x03",
        lambda m: f"\u00abLN:{m.group(1)}|{m.group(2)}\u00bb",
        text,
    )

    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--volume", type=int, required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
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
            print(f"Skipping {outfile.name} (already fetched)")
            continue

        # Preventive cooldown before hitting rate limit.
        # Conservative: 350 pages then 15 min pause, for unattended overnight runs.
        if fetched_this_run > 0 and fetched_this_run % 350 == 0:
            print(f"  Cooldown pause after {fetched_this_run} requests (15 min)...")
            time.sleep(900)

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
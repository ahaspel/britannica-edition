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

    # Remove ref tags
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<ref[^/]*/\s*>", "", text, flags=re.IGNORECASE)

    # Replace file/image links with inline markers BEFORE table stripping
    text = re.sub(
        r"\[\[(?:File|Image):([^\]]+)\]\]",
        _image_to_marker,
        text,
        flags=re.IGNORECASE,
    )

    # Remove wikitable blocks but preserve any image markers inside them
    def _strip_table_keep_images(match: re.Match) -> str:
        content = match.group(0)
        markers = re.findall(r"\x00IMG:[^\x00]+\x00", content)
        return "\n\n".join(markers) if markers else ""
    text = re.sub(r"\{\|.*?\|\}", _strip_table_keep_images, text, flags=re.DOTALL)

    # Preserve content of a few useful one-argument templates
    # {{sc|e.m.f.}} -> e.m.f.
    # {{lang|fr|bonjour}} -> bonjour   (optional but handy)
    # {{sub|3}} -> 3   (preserve subscript digits so formulas stay recognizable)
    # {{sup|2}} -> 2
    text = re.sub(r"\{\{sc\|([^{}|]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{lang\|[^{}|]*\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{su[bp]\|([^{}|]*)\}\}", r"\1", text, flags=re.IGNORECASE)

    # Preserve link text from EB1911 cross-reference templates
    # {{EB1911 lkpl|Peleus}} -> Peleus
    # {{EB1911 lkpl|Alcott, Louisa May|Louisa}} -> Louisa  (display form)
    # {{DNB lkpl|Target|Display}} -> Display
    text = re.sub(r"\{\{(?:EB1911|DNB)\s+lkpl\|[^{}|]*\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{(?:EB1911|DNB)\s+lkpl\|([^{}|]*)\}\}", r"\1", text, flags=re.IGNORECASE)

    # Preserve link text from {{1911link|Target}} templates
    text = re.sub(r"\{\{1911link\|([^{}|]*)\}\}", r"\1", text, flags=re.IGNORECASE)

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

    # Handle wikilinks after template cleanup
    # [[target|label]] -> label
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    # [[target]] -> target
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

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

        # Preventive cooldown before hitting rate limit (~500 req window)
        if fetched_this_run > 0 and fetched_this_run % 450 == 0:
            print(f"  Cooldown pause after {fetched_this_run} requests (6 min)...")
            time.sleep(360)

        raw = fetch_page_wikitext(args.volume, page_number)
        cleaned = clean_wikisource_page_text(raw)
        fetched_this_run += 1
        time.sleep(2)  # polite delay between requests

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
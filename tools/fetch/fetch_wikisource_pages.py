#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import html
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

    print(f"Fetching {title} ...")
    response = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    print(f"HTTP {response.status_code} for {title}")
    response.raise_for_status()

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

def clean_wikisource_page_text(text: str) -> str:
    # Normalize line endings early
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove noinclude blocks completely
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.DOTALL | re.IGNORECASE)

    # Remove ref tags
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<ref[^/]*/\s*>", "", text, flags=re.IGNORECASE)

    # Remove wikitable blocks entirely for now
    text = re.sub(r"\{\|.*?\|\}", "", text, flags=re.DOTALL)

    # Remove file/image links entirely
    text = re.sub(r"\[\[(?:File|Image):[^\]]*\]\]", "", text, flags=re.IGNORECASE)

    # Preserve content of a few useful one-argument templates
    # {{sc|e.m.f.}} -> e.m.f.
    # {{lang|fr|bonjour}} -> bonjour   (optional but handy)
    text = re.sub(r"\{\{sc\|([^{}|]*)\}\}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\{\{lang\|[^{}|]*\|([^{}]*)\}\}", r"\1", text, flags=re.IGNORECASE)

    # Remove common presentation/layout templates wholesale
    # These are the ones currently leaking figure debris.
    for name in [
        "center", "csc", "fs", "ts", "ditto",
        "eb1911 page heading", "eb1911 fine print/s", "eb1911 fine print/e"
    ]:
        pattern = r"\{\{\s*" + re.escape(name) + r"\b.*?\}\}"
        text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)

    # General iterative template stripping.
    # This removes innermost templates first, which helps with nesting.
    previous = None
    while text != previous:
        previous = text
        text = re.sub(r"\{\{[^{}]*\}\}", "", text)

    # Remove any orphaned closing braces left by nested template cleanup
    text = re.sub(r"^\s*\}\}+\s*$", "", text, flags=re.MULTILINE)

    # Handle wikilinks after template cleanup
    # [[target|label]] -> label
    text = re.sub(r"\[\[[^\]|]+\|([^\]]+)\]\]", r"\1", text)
    # [[target]] -> target
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

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

    # Trim each line and drop obviously empty lines
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]

    text = "\n\n".join(lines)

    # Collapse excessive blank lines again just in case
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

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

    for page_number in range(args.start, args.end + 1):
        raw = fetch_page_wikitext(args.volume, page_number)
        cleaned = clean_wikisource_page_text(raw)

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
"""Vision-LLM transcription of vol-29 ancillary pages.

Transcribes the Index Preface (leaves 11-14) and Rules and
Abbreviations (leaves 15-16) using Claude vision.

Output: data/derived/vol29_ancillary.json
  {
    "index_preface": "...",       # leaves 11-14, concatenated
    "rules_and_abbreviations": "..."  # leaves 15-16, concatenated
  }

Env: ANTHROPIC_API_KEY must be set.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import anthropic

SCAN_DIR = Path("data/derived/scans")
OUT = Path("data/derived/vol29_ancillary.json")

MODEL = "claude-opus-4-6"

PROSE_PROMPT = (
    "You are transcribing a page from volume 29 of the 1911 "
    "Encyclopaedia Britannica. This is a prose page (preface or "
    "introductory text), not a columnar index.\n\n"
    "Produce a faithful plain-text transcription that preserves:\n"
    "  - paragraph structure (blank line between paragraphs),\n"
    "  - italic text marked with *italic*,\n"
    "  - section headings in ALL CAPS on their own line,\n"
    "  - marginal notes (shoulder headings) on their own line, "
    "prefixed with '>> ',\n"
    "  - any footnotes at the bottom of the page.\n\n"
    "Use the original wording exactly. If a word is unreadable, "
    "write [?]. Output ONLY the transcription text."
)

ABBREV_PROMPT = (
    "You are transcribing a page from the 'Rules and Abbreviations' "
    "section of volume 29 of the 1911 Encyclopaedia Britannica.\n\n"
    "The page contains:\n"
    "  - Prose rules about the index's conventions (if present),\n"
    "  - A multi-column abbreviation list in the format:\n"
    "    Abbr.    Expansion\n\n"
    "Produce a faithful plain-text transcription:\n"
    "  - For prose sections, preserve paragraph structure.\n"
    "  - For the abbreviation list, render each entry as:\n"
    "    ABBR<tab>EXPANSION\n"
    "    (one per line, tab-separated).\n"
    "  - Section headings in ALL CAPS on their own line.\n"
    "  - Italic text marked with *italic*.\n\n"
    "Use the original wording exactly. Output ONLY the transcription."
)

SECTIONS = [
    {
        "key": "index_preface",
        "label": "Index Preface",
        "leaves": [11, 12, 13, 14],
        "prompt": PROSE_PROMPT,
    },
    {
        "key": "rules_and_abbreviations",
        "label": "Rules and Abbreviations",
        "leaves": [15, 16],
        "prompt": ABBREV_PROMPT,
    },
]


def transcribe_page(client: anthropic.Anthropic, leaf: int,
                     system_prompt: str) -> str:
    scan_path = SCAN_DIR / f"vol29_leaf{leaf:04d}.jpg"
    if not scan_path.exists():
        raise FileNotFoundError(f"No scan: {scan_path}")
    img_b64 = base64.standard_b64encode(scan_path.read_bytes()).decode("ascii")
    with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        system=[{
            "type": "text",
            "text": system_prompt,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": img_b64,
                    },
                },
                {
                    "type": "text",
                    "text": f"Transcribe this page (vol 29, leaf {leaf}).",
                },
            ],
        }],
    ) as stream:
        msg = stream.get_final_message()
    text = "".join(
        b.text for b in msg.content if getattr(b, "type", None) == "text"
    )
    return text.strip()


def main() -> None:
    # Load existing output if resuming.
    data: dict[str, str] = {}
    if OUT.exists():
        data = json.loads(OUT.read_text(encoding="utf-8"))

    client = anthropic.Anthropic()

    for section in SECTIONS:
        key = section["key"]
        if data.get(key):
            print(f"{section['label']}: already transcribed, skipping")
            continue

        print(f"{section['label']}:")
        pages: list[str] = []
        for leaf in section["leaves"]:
            print(f"  leaf {leaf}...", end=" ", flush=True)
            try:
                text = transcribe_page(client, leaf, section["prompt"])
                pages.append(text)
                print(f"{len(text):,} chars")
            except Exception as e:
                print(f"ERROR: {e}")
                continue

        data[key] = "\n\n".join(pages)
        OUT.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(f"\nDone. Written to {OUT}")


if __name__ == "__main__":
    main()

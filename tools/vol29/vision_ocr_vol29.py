"""Vision-LLM transcription of vol-29 classified-TOC body pages.

Tesseract on the IA scans is the bottleneck — Phase A and the LLM
matcher both struggle on its noisy output. This script replaces the
Tesseract OCR for body pages that lack Wikisource transcription with
Claude vision transcription, written back into `vol29_ocr.json`.

Uses Opus 4.6 (the default per Anthropic's coding skill — quality
matters here more than cost; this run is one-time on ~30-40 pages).

Run after the pipeline has produced `vol29_ocr.json`. Resumable —
re-running skips pages already replaced this session via a sentinel
field, so an interrupted run can continue.

Env: `ANTHROPIC_API_KEY` must be set.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import anthropic

WIKISOURCE_DIR = Path("data/raw/wikisource/vol_29")
SCAN_DIR = Path("data/derived/scans")
PER_PAGE_OCR = Path("data/derived/vol29_ocr.json")
LEAF_OFFSET = 6
WS_START = 891
WS_END = 955

# Sentinel marker prefix — the per-page entry starts with this when
# vision-transcribed, so re-runs can detect and skip.
VISION_TAG = "<!-- vision-ocr -->\n"

MODEL = "claude-opus-4-6"

SYSTEM_PROMPT = (
    "You are transcribing a single page from the 'Classified Table of "
    "Contents' at the back of volume 29 of the 1911 Encyclopaedia "
    "Britannica. The page lists article titles grouped under category "
    "and sub-category headers, typically in 3 columns of small print.\n\n"
    "Your job: produce a faithful, plain-text transcription that "
    "preserves\n"
    "  - column reading order (column 1 top-to-bottom, then col 2, "
    "then col 3),\n"
    "  - sub-section headers (set in small caps or italic in the "
    "original),\n"
    "  - article entries in the order they appear in each column,\n"
    "  - comma-separated 'LASTNAME, Firstname' biographical entries "
    "intact,\n"
    "  - any cross-reference notes ('See also …') as a single line.\n\n"
    "Use the original page's exact wording for headers and titles — "
    "do not normalize spelling or expand abbreviations. If a token is "
    "unreadable, write [?]. If a header is set in Blackletter font, "
    "prefix it with '## '. If a sub-section header is set in small "
    "caps, write it in ALL CAPS on its own line. Article entries are "
    "one per line.\n\n"
    "Output ONLY the transcription text — no commentary, no JSON, no "
    "markdown code fences."
)


def needs_vision(ws: int, current_text: str) -> bool:
    """True if this ws page should be vision-transcribed."""
    if current_text.startswith(VISION_TAG):
        return False  # already done in a prior run
    leaf = ws + LEAF_OFFSET
    if not (SCAN_DIR / f"vol29_leaf{leaf:04d}.jpg").exists():
        return False  # no scan to vision against
    return True


def transcribe_page(client: anthropic.Anthropic, ws: int) -> str:
    leaf = ws + LEAF_OFFSET
    scan_path = SCAN_DIR / f"vol29_leaf{leaf:04d}.jpg"
    img_b64 = base64.standard_b64encode(scan_path.read_bytes()).decode("ascii")
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
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
                    "text": (
                        f"Transcribe this page (vol 29, leaf {leaf}, ws {ws}) "
                        "of the Classified Table of Contents."
                    ),
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
    if not PER_PAGE_OCR.exists():
        print(f"[error] {PER_PAGE_OCR} missing — run the pipeline first.")
        return
    ocr_data = json.loads(PER_PAGE_OCR.read_text(encoding="utf-8"))

    targets: list[int] = []
    for ws in range(WS_START, WS_END + 1):
        if needs_vision(ws, ocr_data.get(str(ws), "")):
            targets.append(ws)
    print(f"Pages to vision-transcribe: {len(targets)}")
    if not targets:
        print("Nothing to do.")
        return

    client = anthropic.Anthropic()
    for i, ws in enumerate(targets, 1):
        print(f"  [{i:2d}/{len(targets)}] ws{ws}...", end=" ", flush=True)
        try:
            text = transcribe_page(client, ws)
        except Exception as e:
            print(f"ERROR ({type(e).__name__}): {e}")
            continue
        ocr_data[str(ws)] = VISION_TAG + text
        # Save after each page so an interrupt doesn't lose work.
        PER_PAGE_OCR.write_text(
            json.dumps(ocr_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"{len(text):,} chars")

    print(f"\nDone. Updated {PER_PAGE_OCR}")


if __name__ == "__main__":
    main()

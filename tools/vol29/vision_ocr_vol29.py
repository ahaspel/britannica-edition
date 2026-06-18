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
import sys
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

SYSTEM_PROMPT = """\
You are transcribing one page from the 'Classified Table of Contents' at the \
back of volume 29 of the 1911 Encyclopaedia Britannica. Getting the READING \
ORDER right is the whole task -- read this carefully.

THE PAGE HAS THREE KINDS OF LINE:
  1. CATEGORY header -- large Blackletter (gothic) type, centred across the
     full page width (e.g. "Astronomy", "Biology").
  2. SECTION header -- bold or small-caps, centred OVER the block of columns
     it introduces (e.g. "General", "Constellations and Stars",
     "Biographies", "Pure", "Applied"). It may sit above 2-3 narrow columns;
     the articles it heads are printed in those columns below it.
  3. ARTICLE entry -- ordinary small type, one headword per line, including
     "LASTNAME, Firstname" biographies and cross-reference notes.
A section's first one or few entries may be set in ITALICS: these are the
section's principal articles, printed first even though they fall out of
alphabetical order.

READING ORDER (critical -- this is where naive transcription fails):
  - Work section by section, in top-to-bottom then left-to-right block order.
    For each SECTION header, read EVERY column of articles belonging to that
    section (its left column top-to-bottom, then its next column, ...) before
    moving on to the next section.
  - NEVER read straight down a physical column that passes through more than
    one section -- that interleaves unrelated sections. Stay inside the
    current section's block.
  - A short category often splits across the page: one section fills the left
    half while other sections stack in the right half. Treat each block on its
    own; do not read across the halves.

ALPHABETICAL SELF-CHECK (use it to fix your own column order):
  - Within one section, after the italic principal articles, the headwords are
    in STRICT alphabetical order, no exceptions (letter-by-letter, ignoring
    spaces, punctuation and honorifics; Mc = Mac, St = Saint).
  - If a section's non-italic entries come out non-alphabetical, you mis-read
    the column order -- re-read that block until they are alphabetical.

OUTPUT FORMAT:
  - Prefix a CATEGORY (Blackletter) header with "## ".
  - Prefix a SECTION header with "### ", exact printed wording
    (e.g. "### Constellations and Stars"); keep a printed "(cont.)".
  - Wrap an ITALIC principal article in *asterisks* (e.g. "*Astronomy*").
  - Every other article on its own line, exact printed wording -- do not
    normalize spelling, expand abbreviations, or reorder. Keep
    "LASTNAME, Firstname" intact. Render a cross-reference ("See also ...",
    "For X see under Y") as one line as printed. Unreadable token -> [?].

Output ONLY the transcription text -- no commentary, no JSON, no code fences.
"""


def needs_vision(ws: int, current_text: str, force: bool = False) -> bool:
    """True if this ws page should be vision-transcribed."""
    if current_text.startswith(VISION_TAG) and not force:
        return False  # already done in a prior run (pass --force to redo)
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

    # CLI: "--force" re-transcribes pages already done; bare integers limit the
    # run to those ws pages (e.g. `... --force 896` to test Astronomy first).
    force = "--force" in sys.argv[1:]
    only = {int(a) for a in sys.argv[1:] if a.isdigit()}

    targets: list[int] = []
    for ws in range(WS_START, WS_END + 1):
        if only and ws not in only:
            continue
        if needs_vision(ws, ocr_data.get(str(ws), ""), force):
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

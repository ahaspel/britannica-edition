"""Vision-LLM transcription of vol-29's master Index of Contributors.

Pages 956-982 of vol 29 carry a complete alphabetised list of every
signed-article contributor with their distinguishing initials and
the principal articles each wrote.  Roughly a third of the pages
are proofread on Wikisource (carry `[[Author:...]]` links, clean
markup); the rest are level-1 OCR pages where Tesseract / IA's
OCR pass dropped the bold formatting and produced unreadably noisy
text — many entries appear without their leading bold name token,
asterisks fall off the initials, and surnames pick up digit-for-
letter substitutions.

This script replaces that lossy OCR with Claude vision
transcription, written to a fresh
`data/derived/vol29_contributors_ocr.json` — a flat
`{ws_page_number: clean_transcription}` mapping that the
contributor-table builder can read alongside the wikitext.

Uses Opus 4.6 for transcription quality (one-time run, ~27 pages
total).  Resumable via the same sentinel-tag pattern as
`vision_ocr_vol29.py` — re-running skips pages already done.

Env: `ANTHROPIC_API_KEY` must be set.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

import anthropic

WIKISOURCE_DIR = Path("data/raw/wikisource/vol_29")
SCAN_DIR = Path("data/derived/scans")
PER_PAGE_OCR = Path("data/derived/vol29_contributors_ocr.json")
# Vol 29 contributor index runs ws 956 → leaf 963 through ws 982 →
# leaf 989.  The offset here (+7) differs from vision_ocr_vol29.py's
# +6 for the classified-TOC range — there's an extra unnumbered
# leaf in the IA scan between the TOC and the contributor index
# section.
LEAF_OFFSET = 7
WS_START = 956
WS_END = 982

# Sentinel marker prefix — the per-page entry starts with this when
# vision-transcribed, so re-runs can detect and skip.
VISION_TAG = "<!-- vision-ocr -->\n"

MODEL = "claude-opus-4-6"

SYSTEM_PROMPT = (
    "You are transcribing a single page from the master 'Contributors "
    "to the Encyclopaedia Britannica (11th Edition) and the Principal "
    "Articles Signed by Them' index at the back of volume 29 of the "
    "1911 Encyclopaedia Britannica.  Each entry on the page has this "
    "shape:\n\n"
    "  SURNAME, FIRSTNAMES, CREDENTIALS. (Initials.)\n"
    "      Article Title; Other Article Title; ...\n\n"
    "Sometimes a single contributor's articles span multiple lines; "
    "they are always semicolon-separated and follow immediately after "
    "the contributor's header line.\n\n"
    "Your job: produce a faithful, plain-text transcription that "
    "preserves\n"
    "  - one contributor entry per blank-line-separated block\n"
    "  - the SURNAME, FIRSTNAMES, CREDENTIALS portion EXACTLY as "
    "printed (all caps for surname, mixed case for given names, comma-"
    "separated credentials)\n"
    "  - the parenthesised initials EXACTLY — preserve every period, "
    "asterisk, hyphen, subscript letter, and case distinction.  An "
    "asterisk is the print's disambiguation marker between two "
    "contributors who would otherwise share the same initials, so "
    "`(E. B.*)` and `(E. B.)` are DIFFERENT signatures and must be "
    "kept distinct.  When initials use a small-cap subscript letter "
    "(e.g. `W. B<small>A</small>.`), write it as `W. Ba.` with the "
    "subscript letter lower-case to mark it.\n"
    "  - the article list, one per line after a leading colon, in "
    "the exact order printed\n"
    "  - italicized notes such as '(in part)' or '(cont.)' attached "
    "to article titles\n\n"
    "Output format, one block per contributor:\n\n"
    "  SURNAME, FIRSTNAMES, CREDS. (Init.)\n"
    "  : Article 1; Article 2; Article 3.\n"
    "  : Article 4; Article 5.\n\n"
    "  NEXT SURNAME, ...\n"
    "  : ...\n\n"
    "Do not normalize spelling, expand abbreviations, or fix typos in "
    "the print.  If a token is unreadable, write [?].  Skip running "
    "headers, page numbers, and column rules.\n\n"
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
                        "of the master Index of Contributors."
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
    # Load existing OCR output (if any) so the run is resumable.
    if PER_PAGE_OCR.exists():
        ocr_data = json.loads(PER_PAGE_OCR.read_text(encoding="utf-8"))
    else:
        ocr_data = {}

    targets: list[int] = []
    for ws in range(WS_START, WS_END + 1):
        if needs_vision(ws, ocr_data.get(str(ws), "")):
            targets.append(ws)
    print(f"Pages to vision-transcribe: {len(targets)} of "
          f"{WS_END - WS_START + 1}")
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

    print(f"\nDone. Wrote {PER_PAGE_OCR}")


if __name__ == "__main__":
    main()

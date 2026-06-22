"""WHOLE-PAGE (six-column) CONTENT reads of the vol-29 classified-list spreads.

The half-page reads put the columns in order but SHRED the full-width band
banners; the whole-spread read keeps the banners whole and in order (the columns
between them scramble, but we take column order from the halves). So every spread
gets one whole read here -- the authority for the band skeleton -- saved to
data/derived/vol29_whole_<ws>.txt.

Resumable: a spread already on disk is skipped unless --force, so a long run that
dies just picks up where it left off.

Env: ANTHROPIC_API_KEY.
Run:
  python tools/vol29/ocr_whole.py            # all spreads, skip ones already done
  python tools/vol29/ocr_whole.py 912        # one spread (or several: 912 913 ...)
  python tools/vol29/ocr_whole.py --force     # redo everything
"""
from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

import anthropic
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vision_ocr_vol29 import SCAN_DIR, LEAF_OFFSET, MODEL, WS_START, WS_END

OUT_DIR = Path("data/derived")

WHOLE_PROMPT = """\
You are looking at a COMPLETE two-page spread of the 'Classified List of \
Articles' from the back of volume 29 of the 1911 Encyclopaedia Britannica. Each \
page carries THREE columns of small type -- SIX columns across the spread -- \
with a vertical rule down the centre between the two pages.

The spread is divided horizontally into BANDS by FULL-WIDTH banners: headings \
centred across the WHOLE spread, crossing the central rule. These are the large \
Blackletter CATEGORY names (e.g. "Art", "Archaeology and Antiquities") and the \
continent / section banners beneath them. A full-width banner starts a new band; \
that band's articles fill the columns BELOW it until the next full-width banner.

Transcribe the spread BAND BY BAND, top to bottom. WITHIN each band, read its \
columns in order: the LEFT page's three columns first (column 1 straight down to \
the foot of this band, then column 2, then column 3), THEN the RIGHT page's three \
columns (1, 2, 3) -- each column read only as far as the foot of THIS band. Never \
read across columns, and never let one band's columns run on into the next band. \
Keep every entry; do not alphabetize, merge, or rearrange.

Mark each line as you go:
  - A full-width banner spanning the whole spread (category, or continent / \
section): a line beginning "## ".
  - A header sitting over ONE page's columns only (e.g. "Subjects", \
"Biographies", "General", "Pure"; keep any printed "(cont.)"): a line beginning \
"### ".
  - An entry printed in ITALICS -- a section's principal articles, set first \
though out of alphabetical order: wrap it in *asterisks* (e.g. *Art*).
  - Any other entry, including "LASTNAME, Firstname" biographies and \
"(see also ...)" cross-reference notes: the headword on its own line.

SELF-CHECK: within a section, after any italic principals, the headwords run in \
STRICT alphabetical order (letter-by-letter; Mc = Mac, St = Saint). If yours come \
out non-alphabetical, you mis-ordered the columns of that band -- re-read it.

Output ONLY the transcription -- exact printed wording, no commentary, no code \
fences. Unreadable token -> [?].
"""


def read_one(client: anthropic.Anthropic, ws: int, force: bool) -> str:
    out = OUT_DIR / f"vol29_whole_{ws}.txt"
    if out.exists() and not force:
        return "cached"
    leaf = ws + LEAF_OFFSET
    scan = SCAN_DIR / f"vol29_leaf{leaf:04d}.jpg"
    if not scan.exists():
        return f"scan missing ({scan.name})"
    im = Image.open(scan).convert("RGB")              # whole spread, uncropped
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=90)
    b64 = base64.standard_b64encode(buf.getvalue()).decode("ascii")
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        system=[{
            "type": "text",
            "text": WHOLE_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64", "media_type": "image/jpeg", "data": b64}},
                {"type": "text", "text": (
                    f"Transcribe this whole spread (vol 29, leaf {leaf}, ws "
                    f"{ws}) band by band, the six columns in order within each "
                    f"band.")},
            ],
        }],
    ) as stream:
        msg = stream.get_final_message()
    text = "".join(
        b.text for b in msg.content if getattr(b, "type", None) == "text"
    ).strip()
    out.write_text(text, encoding="utf-8")
    return f"wrote {len(text):,} chars"


def main() -> None:
    args = sys.argv[1:]
    force = "--force" in args
    nums = [int(a) for a in args if a.isdigit()]
    targets = list(nums) if nums else list(range(WS_START, WS_END + 1))
    client = anthropic.Anthropic()
    total = len(targets)
    for i, ws in enumerate(targets, 1):
        print(f"[{i}/{total}] ws{ws}: ", end="", flush=True)
        try:
            print(read_one(client, ws, force), flush=True)
        except Exception as e:                         # keep the batch going
            print(f"ERROR {type(e).__name__}: {e}", flush=True)


if __name__ == "__main__":
    main()

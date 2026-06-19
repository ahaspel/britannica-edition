"""Vision-LLM transcription of vol-29 classified-TOC body pages.

Each scan is a TWO-PAGE spread: a vertical rule down the centre splits it into
two independent three-column pages, and ONLY the full-width category banner
crosses that rule.  Reading the spread as one page makes the model guess a
path across the divider, which scrambles column order and misfiles or drops
whole columns.  So we don't: we crop each scan at the centre, transcribe the
left page and the right page as separate images, and concatenate left-then-
right.  A banner clipped by the crop is reconciled against the known category
list (the one thing we don't need pixel-perfect -- the set of category names
is small and fixed).

Run after the pipeline has produced `vol29_ocr.json`.  Resumable -- re-running
skips pages already replaced this session via a sentinel field.

Env: `ANTHROPIC_API_KEY` must be set.
"""
from __future__ import annotations

import base64
import io
import json
import re
import sys
from pathlib import Path

import anthropic
from PIL import Image

SCAN_DIR = Path("data/derived/scans")
PER_PAGE_OCR = Path("data/derived/vol29_ocr.json")
LEAF_OFFSET = 6
WS_START = 891
WS_END = 955

# Sentinel marking a SPLIT-SCAN transcription -- distinct from the old
# whole-spread "<!-- vision-ocr -->" tag, so a plain (non --force) run re-does
# every page still on the old single-image read and skips ones already redone
# this way.  This makes the rollout resumable: it writes after each page, and a
# re-run picks up where an interrupt left off.
VISION_TAG = "<!-- split-scan -->\n"

MODEL = "claude-opus-4-6"

SYSTEM_PROMPT = """\
You are transcribing ONE three-column page from the 'Classified List of \
Articles' at the back of volume 29 of the 1911 Encyclopaedia Britannica.  This \
image is HALF of a scanned spread, cropped at the central rule -- treat it as a \
single standalone page.

READING ORDER (this is the whole task): read straight DOWN column 1 to its \
foot, then column 2 top-to-foot, then column 3.  Never read across columns \
mid-list.  Headers appear in the order you reach them descending each column.

THREE KINDS OF LINE:
  1. CATEGORY banner -- large Blackletter, centred, spanning the full page \
width.  Because the spread was cut down the middle, the banner is probably \
CLIPPED at one edge: transcribe only the legible part, do NOT guess the rest. \
Prefix with "## ".
  2. SECTION header -- bold or small-caps over its columns (e.g. "General", \
"Finance and Currency", "Biographies", "Pure", "Applied"); keep a printed \
"(cont.)".  Prefix with "### ".
  3. ARTICLE entry -- ordinary small type, one headword per line, including \
"LASTNAME, Firstname" biographies and cross-reference notes ("See also ...").

A section's first one or few entries may be set in ITALICS -- its principal \
articles, printed first though they fall out of alphabetical order.  Wrap each \
in *asterisks* (e.g. "*Athletic Sports*").

ALPHABETICAL SELF-CHECK: after the italic principals, a section's headwords \
run in STRICT alphabetical order (letter-by-letter, ignoring spaces, \
punctuation and honorifics; Mc = Mac, St = Saint).  If yours come out \
non-alphabetical, you mis-ordered the columns -- re-read.

Output ONLY the transcription text -- no commentary, no JSON, no code fences. \
Exact printed wording; do not normalize spelling, expand abbreviations, or \
reorder.  Unreadable token -> [?].
"""


def needs_vision(ws: int, current_text: str, force: bool = False) -> bool:
    """True if this ws page should be vision-transcribed."""
    if current_text.startswith(VISION_TAG) and not force:
        return False  # already done in a prior run (pass --force to redo)
    leaf = ws + LEAF_OFFSET
    if not (SCAN_DIR / f"vol29_leaf{leaf:04d}.jpg").exists():
        return False  # no scan to vision against
    return True


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _best_category_match(frag: str, cats: list[str]) -> str | None:
    """A clipped banner fragment -> full category name.  The fragment is a
    contiguous (prefix or suffix) slice of the centred banner, so match it as a
    substring of exactly one known category.  Unique-only; never guesses."""
    fn = _norm(frag)
    if len(fn) < 3:
        return None  # a 1-2 char clip is too ambiguous to seat
    hits = [c for c in cats if fn and fn in _norm(c)]
    return hits[0] if len(hits) == 1 else None


def _ocr_half(client: anthropic.Anthropic, img_b64: str, ws: int,
              leaf: int, side: str) -> str:
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
                {"type": "image", "source": {
                    "type": "base64", "media_type": "image/jpeg",
                    "data": img_b64}},
                {"type": "text", "text": (
                    f"Transcribe this {side} page of the classified-TOC spread "
                    f"(vol 29, leaf {leaf}, ws {ws}).")},
            ],
        }],
    ) as stream:
        msg = stream.get_final_message()
    return "".join(
        b.text for b in msg.content if getattr(b, "type", None) == "text"
    ).strip()


def _bands(part: str, cats: list[str]) -> list[list]:
    """Split one half-page into [banner_or_None, [lines]] bands.  The full-width
    category banner is the one element that crosses the gutter, so it cuts the
    half into horizontal bands; the first band (above any banner) has None."""
    segs: list[list] = [[None, []]]
    for line in part.split("\n"):
        if line.startswith("## "):
            full = _best_category_match(line[3:], cats)
            segs.append([f"## {full}" if full else line, []])
        else:
            segs[-1][1].append(line)
    return segs


def _assemble(parts: list[str], cats: list[str]) -> str:
    """Read the spread BAND-BY-BAND, not page-by-page.  Because the full-width
    banner cuts both half-pages into the same horizontal bands (the previous
    category's tail above it, the new category below), band i of the left page
    and band i of the right page are the same category.  So we emit, per band:
    the banner once, then the left page's lines, then the right page's -- which
    keeps a tail spanning both pages (Chemistry's biographies above the
    Economics banner) together instead of stranding the right half after the
    new category."""
    left = _bands(parts[0], cats)
    right = _bands(parts[1], cats)
    out: list[str] = []
    for i in range(max(len(left), len(right))):
        banner = (left[i][0] if i < len(left) and left[i][0]
                  else right[i][0] if i < len(right) and right[i][0] else None)
        if banner:
            out.append(banner)
        if i < len(left):
            out.extend(left[i][1])
        if i < len(right):
            out.extend(right[i][1])
    return "\n".join(out)


def transcribe_page(client: anthropic.Anthropic, ws: int,
                    cats: list[str]) -> str:
    leaf = ws + LEAF_OFFSET
    scan_path = SCAN_DIR / f"vol29_leaf{leaf:04d}.jpg"
    im = Image.open(scan_path).convert("RGB")
    w, h = im.size
    mid = w // 2  # the centre rule that separates the two pages
    parts = []
    for side, box in (("left", (0, 0, mid, h)), ("right", (mid, 0, w, h))):
        buf = io.BytesIO()
        im.crop(box).save(buf, format="JPEG", quality=90)
        b64 = base64.standard_b64encode(buf.getvalue()).decode("ascii")
        parts.append(_ocr_half(client, b64, ws, leaf, side))
    return _assemble(parts, cats)


def _known_categories() -> list[str]:
    """The 24 authoritative top-level classified-TOC category names, from the
    parser's meta-TOC loader -- used to reconcile banners clipped by the centre
    crop.  Sourced from the parser so there is ONE definition of the category
    set, not a copy, and no noise: harvesting `##` lines out of the OCR also
    picks up section headers the model mis-stamped (e.g. `Comparative Religion
    and Folklore`), which would make a clipped `Religion and...` ambiguous."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from parse_classified_toc import load_meta_toc_categories
    return [c["name"] for c in load_meta_toc_categories()]


def main() -> None:
    if not PER_PAGE_OCR.exists():
        print(f"[error] {PER_PAGE_OCR} missing -- run the pipeline first.")
        return
    ocr_data = json.loads(PER_PAGE_OCR.read_text(encoding="utf-8"))
    cats = _known_categories()

    # CLI: "--force" re-transcribes pages already done; bare integers limit the
    # run to those ws pages (e.g. `... --force 901` to test Economics first).
    force = "--force" in sys.argv[1:]
    only = {int(a) for a in sys.argv[1:] if a.isdigit()}

    targets: list[int] = []
    for ws in range(WS_START, WS_END + 1):
        if only and ws not in only:
            continue
        if needs_vision(ws, ocr_data.get(str(ws), ""), force):
            targets.append(ws)
    print(f"Pages to vision-transcribe (split-scan): {len(targets)}")
    if not targets:
        print("Nothing to do.")
        return

    client = anthropic.Anthropic()
    for i, ws in enumerate(targets, 1):
        print(f"  [{i:2d}/{len(targets)}] ws{ws}...", end=" ", flush=True)
        try:
            text = transcribe_page(client, ws, cats)
        except Exception as e:
            print(f"ERROR ({type(e).__name__}): {e}")
            continue
        ocr_data[str(ws)] = VISION_TAG + text
        # Save after each page so an interrupt doesn't lose work.
        PER_PAGE_OCR.write_text(
            json.dumps(ocr_data, indent=2, ensure_ascii=False),
            encoding="utf-8")
        print(f"{len(text):,} chars")

    print(f"\nDone. Updated {PER_PAGE_OCR}")


if __name__ == "__main__":
    main()

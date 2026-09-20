"""Does the line resuming after a display block sit FLUSH, or is it INDENTED?

    uv run python tools/diagnostics/para_indent.py --validate
    uv run python tools/diagnostics/para_indent.py --page 1:334
    uv run python tools/diagnostics/para_indent.py --sites sites.json --out verdicts.json

THE QUESTION, AND WHY ONLY THE SCAN CAN ANSWER IT.  A paragraph interrupted by a
display block resumes FLUSH; a genuinely new paragraph after one is INDENTED.
The EB1911 transcription does not record which -- measured, not assumed.
Wikisource renders EB1911 with zero `text-indent`, so a transcriber got no
feedback that would make them encode the difference, and the blank line that
might have carried it is noise: after `{{center|...}}` a blank line precedes a
continuation 26% of the time and a single newline 41% of the time, both buckets
mixtures.  Our pipeline reads a blank line as a paragraph break and is right to;
the SOURCE is silent.  So the book is the only witness -- and a legible one,
because the indent is about 1em of white space.

INK, NOT OCR.  The obvious approach, tesseract word boxes, cannot do this job.
It drops low-confidence leading characters ("o the circuital" for "also the
circuital"), so flush lines report left edges scattered over 15..88px on a page
whose indent is 20px: the error is larger than the signal.  The leftmost dark
pixel of a line is not ambiguous.  OCR is used ONLY to say which line is ours,
never to measure it.

THREE THINGS THE FIRST VERSION GOT WRONG, each found by reading scans first and
running the detector second -- which is the only order in which KNOWN is a test:

  * SCAN ARTIFACTS PIN THE EDGE.  A gutter shadow or a dark page border puts ink
    at the same x on every line, so every line measured as flush (v28 ws824: all
    37 lines of a column reported left=6).  A vertical streak is dark down a
    large fraction of the page; text never is.  Those columns are removed before
    anything is measured.
  * FULL-WIDTH LINES ARE NOT COLUMN LINES.  A paragraph below a table spans the
    gutter, and measuring it against one column's margin compares it with
    whatever that column happens to hold -- at v11 ws716 a table whose
    sub-column begins well right of the body margin, which made an indented line
    read as flush.  Bands are classified left / right / full-width by their own
    ink extent, and full-width lines share the LEFT margin, because that is the
    same physical page margin.
  * A TABLE IS NOT A MARGIN.  Fitting the margin through everything lets an
    indented block vote.  The fit runs through the flush population only.

SELF-CALIBRATING, because resolution and margins vary across 29 volumes.  A
page's indent step is recovered from that page's own indented lines, and a
verdict is a fraction of that step rather than a pixel constant.  A page that
cannot supply a step falls back to absolute bounds and readily says `unclear`.

SELF-LOCATING, which is the safety property that matters.  A site is addressed
by a prose anchor; if the anchor is not found the site is reported `not-found`
and never measured at a guessed position, so a wrong page cannot silently yield
a confident verdict.

OUT OF SCOPE: `div[indent]` and `div[hanging]`.  A taxonomic or glossary list
sets its first line at the margin and indents the runovers, so "is this line
indented" is not the same question there and a verdict would not mean what it
means in running prose (GASTROPODA v11 ws544 is the specimen).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from britannica.export.pages import leaf_for_ws            # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
# The kind vocabulary and the anchor word rule belong to `para_sites`, which
# makes the kinds and writes the anchors; re-spelling either here made two
# implementations of one thing, and they could drift apart silently.
from para_sites import LIST_KINDS as OUT_OF_SCOPE, WORD as _WORD  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCANS = ROOT / "data/derived/scans"
TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# Read by eye off the scans BEFORE the detector existed.  (vol, ws_page, anchor,
# verdict).  Chosen to span volumes and interrupter kinds, and to include both
# directions of error, so a change that trades one for the other cannot pass.
KNOWN = [
    (1, 334, "also the circuital relations here reduce to", "flush"),
    (1, 334, "giving, on substitution for", "flush"),
    (1, 334, "For a simple wave-train", "indent"),
    (1, 334, "For the simplest case of polarized waves", "indent"),
    (10, 338, "But he certainly made friends among", "flush"),
    (8, 257, "as representing the distribution of light", "flush"),
    (8, 787, "may also be expressed as a homogeneous", "flush"),
    (5, 274, "The expression for the superficial tension", "indent"),
    (21, 917, "Marvellously subtle as is this speech", "indent"),
    (17, 1012, "where a b c are positive", "flush"),
    (3, 956, "In the sense of a weapon", "indent"),
    (28, 824, "The perfection of simple wood engraving", "indent"),
    (11, 716, "These constructions prove when rightly interpreted", "indent"),
]



def scan_path(vol: int, ws_page: int) -> Path:
    return SCANS / ("vol%02d_leaf%04d.jpg" % (vol, leaf_for_ws(vol, ws_page)))


def _binary(a: np.ndarray, rule_frac: float = 0.80, trim: float = 0.012) -> np.ndarray:
    """Ink mask with vertical rules, gutter shadow and page borders removed."""
    b = a < 128
    h, w = b.shape
    dark_frac = b.sum(axis=0) / float(h)
    b[:, dark_frac > rule_frac] = False
    mx, my = int(w * trim), int(h * trim)
    if mx:
        b[:, :mx] = False
        b[:, -mx:] = False
    if my:
        b[:my, :] = False
        b[-my:, :] = False
    return b


def _gutter(b: np.ndarray, frac: float = 0.30):
    """The gutter x, and whether the page actually HAS one.

    Some EB1911 pages are set full measure (wide mathematics, big tables).  The
    minimum-ink column exists on those too -- it just falls in the middle of a
    line -- so splitting on it silently invents two columns and two margins out
    of one.  A real gutter is a corridor: near-zero ink where a text column has
    plenty.  v17 ws1012 is the specimen.
    """
    ink = b.sum(axis=0)
    w = len(ink)
    lo, hi = int(w * (0.5 - frac / 2)), int(w * (0.5 + frac / 2))
    cut = lo + int(np.argmin(ink[lo:hi]))
    body = ink[ink > 0]
    typical = float(np.median(body)) if len(body) else 0.0
    return cut, bool(ink[cut] < max(3.0, typical * 0.15))


def _rule_columns(b: np.ndarray, x0: int, x1: int, bands) -> np.ndarray:
    """Columns carrying ink on virtually EVERY line -- a rule, not a margin.

    The binding shadow beside the gutter is mottled, so it never trips a
    page-height darkness test, yet it puts ink at the same x on every line and
    pins every measured left edge to it (v28 ws824: 23 right-column bands, all
    reporting left=6, indented lines included).  Text never occupies one x on
    every line of a column; a rule or a shadow does.
    """
    mask = np.zeros(x1 - x0, bool)
    if len(bands) < 8:
        return mask
    hits = np.zeros(x1 - x0, int)
    for top, bot in bands:
        hits += (b[top:bot, x0:x1].sum(axis=0) > 0).astype(int)
    mask[hits >= len(bands) * 0.9] = True
    return mask


def _corridor(b: np.ndarray, gut: int):
    """The white corridor between the columns, as a page-level fact.

    Deciding "does this line span the gutter" per row does not work: measured as
    the widest white run it needs a threshold, and a threshold wide enough to
    reject a word space is wider than some scans' actual gutter (v28 ws824's is
    16px), so every row reads as spanning.  The corridor is the same columns on
    every line, so find it ONCE from the whole page's ink, then a row spans iff
    it puts ink inside it.
    """
    ink = b.sum(axis=0)
    w = len(ink)
    body = ink[ink > 0]
    typical = float(np.median(body)) if len(body) else 0.0
    # Generous threshold and the WIDEST run, not a walk outward from the
    # minimum: a binding shadow beside the gutter carries real ink, and walking
    # out from the minimum stops dead against it, yielding a 1-2px "corridor"
    # that then marks ordinary column rows as spanning the page.
    thresh = max(3.0, typical * 0.25)
    lo, hi = int(w * 0.35), int(w * 0.65)
    best = (0, gut, gut + 1)
    run = None
    for x in range(lo, hi):
        if ink[x] <= thresh:
            run = x if run is None else run
            if x - run + 1 > best[0]:
                best = (x - run + 1, run, x + 1)
        else:
            run = None
    return (best[1], best[2]) if best[0] >= 6 else (gut, gut + 1)


def _rows(b: np.ndarray, min_ink: int = 3, min_h: int = 6):
    on = b.sum(axis=1) > min_ink
    out, start = [], None
    for y, v in enumerate(on):
        if v and start is None:
            start = y
        elif not v and start is not None:
            if y - start >= min_h:
                out.append((start, y))
            start = None
    if start is not None and len(on) - start >= min_h:
        out.append((start, len(on)))
    return out


def _extent(b: np.ndarray, top: int, bot: int):
    cols = b[top:bot].sum(axis=0)
    nz = np.nonzero(cols >= 1)[0]
    return (int(nz[0]), int(nz[-1])) if len(nz) else (None, None)


def _fit(ys: np.ndarray, lefts: np.ndarray):
    """Margin as a function of y, fitted through the flush population only."""
    if len(lefts) < 6:
        return None
    base = np.percentile(lefts, 10)
    flushish = lefts <= base + 12
    if int(flushish.sum()) >= 6:
        m, c = np.polyfit(ys[flushish], lefts[flushish], 1)
        return lambda y: m * y + c
    return lambda y: base


def page_profile(vol: int, ws_page: int) -> dict:
    p = scan_path(vol, ws_page)
    if not p.is_file():
        return {"error": "scan missing: " + p.name}
    a = np.asarray(Image.open(p).convert("L"))
    b = _binary(a)
    w = b.shape[1]
    gut, two_col = _gutter(b)

    def measure(x0, x1, rows, group):
        """Left edge of each row in a region, with that region's rules removed."""
        rules = _rule_columns(b, x0, x1, rows)
        out = []
        for top, bot in rows:
            cols = b[top:bot, x0:x1].sum(axis=0).copy()
            cols[rules] = 0
            nz = np.nonzero(cols >= 1)[0]
            if len(nz):
                out.append({"top": top, "bottom": bot, "left": int(nz[0]),
                            "group": group})
        return out

    bands = []
    if not two_col:
        bands = measure(0, w, _rows(b), "F")
    else:
        # Rows are found PER COLUMN: scanning the whole width finds one giant
        # band instead of lines, because the columns interleave vertically and
        # almost every y carries ink somewhere on the page.
        cx0, cx1 = _corridor(b, gut)
        spanning, plain = [], []
        for top, bot in _rows(b[:, :gut]):
            # Full width means ink INSIDE the corridor.  A point test on the
            # gutter x is luck -- at v11 ws716 a word space fell exactly there
            # and a full-measure paragraph read as column text.
            spans = int(b[top:bot, cx0:cx1].sum()) > 0
            (spanning if spans else plain).append((top, bot))
        bands += measure(0, gut, plain, "L")
        bands += measure(0, w, spanning, "F")
        right_rows = [(t0, b0) for t0, b0 in _rows(b[:, gut:])
                      if not any(not (b0 <= ft or t0 >= fb) for ft, fb in spanning)]
        bands += measure(gut, w, right_rows, "R")
    if not bands:
        return {"error": "no text bands"}
    bands.sort(key=lambda x: x["top"])

    # A full-width line shares the LEFT column's margin: it is the same physical
    # page margin, so they are fitted together.
    for groups in (("L", "F"), ("R",)):
        sel = [x for x in bands if x["group"] in groups]
        if not sel:
            continue
        ys = np.array([(x["top"] + x["bottom"]) / 2.0 for x in sel])
        lefts = np.array([float(x["left"]) for x in sel])
        f = _fit(ys, lefts)
        for x, y, l in zip(sel, ys, lefts):
            x["delta"] = float(l - f(y)) if f else 0.0

    deltas = np.array([x.get("delta", 0.0) for x in bands])
    ind = deltas[(deltas > 7) & (deltas < 55)]
    step = float(np.median(ind)) if len(ind) >= 3 else None
    return {"path": str(p), "width": int(a.shape[1]), "height": int(a.shape[0]),
            "gutter": gut, "step": step, "bands": bands}


def verdict_for(delta: float, step: float | None) -> str:
    if step is None:
        if delta < 9:
            return "flush"
        return "indent" if delta > 14 else "unclear"
    if delta > step * 2.5:
        return "display"
    if delta < step * 0.45:
        return "flush"
    if delta > step * 0.62:
        return "indent"
    return "unclear"


def _ocr_lines(path: Path, x0: int, x1: int):
    """OCR one column, as (top, bottom, text).  Locates only; never measures."""
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT
    im = Image.open(path).convert("L")
    crop = im.crop((x0, 0, x1, im.size[1]))
    d = pytesseract.image_to_data(crop, config="--psm 4",
                                  output_type=pytesseract.Output.DICT)
    agg: dict = {}
    for i, w in enumerate(d["text"]):
        if not (w or "").strip():
            continue
        k = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
        e = agg.setdefault(k, {"top": 10 ** 9, "bottom": 0, "words": []})
        e["top"] = min(e["top"], d["top"][i])
        e["bottom"] = max(e["bottom"], d["top"][i] + d["height"][i])
        e["words"].append(w)
    return [(e["top"], e["bottom"], " ".join(e["words"])) for e in agg.values()]


def locate(vol: int, ws_page: int, anchor: str, prof: dict | None = None) -> dict:
    """Measure the line that starts `anchor`, or say why it could not be found."""
    prof = prof if prof is not None else page_profile(vol, ws_page)
    if "error" in prof:
        return {"verdict": "error", "why": prof["error"]}
    want = [w.lower() for w in _WORD.findall(anchor)][:5]
    if len(want) < 2:
        return {"verdict": "error", "why": "anchor too short"}
    path, gut = Path(prof["path"]), prof["gutter"]
    best = None
    for side, (x0, x1) in (("L", (0, gut)), ("R", (gut, prof["width"]))):
        for top, bot, text in _ocr_lines(path, x0, x1):
            got = [w.lower() for w in _WORD.findall(text)]
            if not got:
                continue
            head = got[:len(want) + 3]
            score = max(sum(1 for a_, b_ in zip(want, got) if a_ == b_),
                        sum(1 for w in want if w in head))
            if best is None or score > best[0]:
                best = (score, top, bot, text, side)
    need = max(2, len(want) - 1)
    if best is None or best[0] < need:
        return {"verdict": "not-found",
                "why": "anchor %r not matched (best %d, need %d)"
                       % (want, best[0] if best else 0, need)}
    score, top, bot, text, side = best
    mid = (top + bot) / 2.0
    # The band must come from the column the OCR matched in.  Nearest-by-y over
    # ALL bands picks the other column about half the time -- the two columns
    # carry lines at the same heights -- and that one mistake moves the verdict
    # between flush and indent at random, which is what made every threshold
    # change look like it half worked.
    cands = [x for x in prof["bands"] if x["group"] in (side, "F")]
    if not cands:
        return {"verdict": "not-found", "why": "no bands in column " + side}
    band = min(cands, key=lambda x: abs((x["top"] + x["bottom"]) / 2.0 - mid))
    if abs((band["top"] + band["bottom"]) / 2.0 - mid) > 40:
        return {"verdict": "not-found", "why": "no ink line under the OCR match"}
    return {"verdict": verdict_for(band.get("delta", 0.0), prof["step"]),
            "delta": round(band.get("delta", 0.0), 1),
            "step": round(prof["step"], 1) if prof["step"] else None,
            "left": band["left"], "y": band["top"], "group": band["group"],
            "ocr": text[:70], "score": score}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true", help="run against KNOWN")
    ap.add_argument("--page", help="VOL:WSPAGE -- dump the line profile")
    ap.add_argument("--sites", help="JSON list of {vol, ws_page, anchor}")
    ap.add_argument("--out", help="write verdicts here")
    args = ap.parse_args()

    if args.page:
        v, p = (int(x) for x in args.page.split(":"))
        prof = page_profile(v, p)
        if "error" in prof:
            print(prof["error"])
            return 1
        print("gutter=%d step=%s bands=%d"
              % (prof["gutter"], prof["step"], len(prof["bands"])))
        for x in prof["bands"]:
            print("   %s y=%5d left=%4d d=%+6.1f %s"
                  % (x["group"], x["top"], x["left"], x.get("delta", 0.0),
                     verdict_for(x.get("delta", 0.0), prof["step"])))
        return 0

    if args.validate:
        cache: dict = {}
        ok = bad = 0
        for vol, ws, anchor, want in KNOWN:
            key = (vol, ws)
            if key not in cache:
                cache[key] = page_profile(vol, ws)
            got = locate(vol, ws, anchor, cache[key])
            hit = got.get("verdict") == want
            ok, bad = ok + int(hit), bad + int(not hit)
            print("  %s  v%-2d ws%-4d want=%-7s got=%-9s d=%-7s step=%-6s %r"
                  % ("OK  " if hit else "FAIL", vol, ws, want, got.get("verdict"),
                     got.get("delta"), got.get("step"), anchor[:34]))
            if not hit and got.get("why"):
                print("          why: " + got["why"])
        print("\n%d/%d agree with the eye" % (ok, ok + bad))
        return 0 if bad == 0 else 1

    if args.sites:
        sites = json.loads(Path(args.sites).read_text(encoding="utf-8"))
        cache: dict = {}
        out = []
        for s in sites:
            if s.get("kind") in OUT_OF_SCOPE:
                out.append({**s, "verdict": "out-of-scope"})
                continue
            key = (s["vol"], s["ws_page"])
            if key not in cache:
                cache[key] = page_profile(*key)
            out.append({**s, **locate(s["vol"], s["ws_page"], s["anchor"], cache[key])})
        txt = json.dumps(out, ensure_ascii=False, indent=1)
        if args.out:
            Path(args.out).write_text(txt, encoding="utf-8")
            print("wrote %d verdicts to %s" % (len(out), args.out))
        else:
            print(txt)
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

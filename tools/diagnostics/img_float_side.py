"""Which side of its column does each `{{img float}}` actually sit on in the scan?

`{{img float}}` defaults to `align=right` (the template is `{{{align|right}}}`);
our producer defaults to LEFT.  227 of the 412 instances state no align at all,
so the side we render is a DEFAULT, not the source's instruction -- and the two
defaults disagree, which means the side is decided by whichever renderer you
happen to use.  The book decides it properly, so read the book.

Method.  The caption is printed directly beneath the cut and is set to the
figure's own width, so the caption's horizontal extent locates the figure box
inside its column.  OCR the page for word boxes, find the caption's most
distinctive words, and compare the caption's centre with the centre of the
column it falls in.

This is a MEASUREMENT, so it has to be checkable: `--validate` runs it against
the eight pages already judged by eye and reports agreement.  Nothing here is
trusted until those agree.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytesseract
from PIL import Image

from britannica.export.pages import leaf_for_ws
from britannica.source_pages import load_pages
from britannica.util.strings import strip_html_tags

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

SCANS = Path("data/derived/scans")

_OPEN = re.compile(r"\{\{\s*img float\b", re.I)
_TMPL = re.compile(r"\{\{[^{}]*\}\}")
_ALIGN = re.compile(r"\|\s*align\s*=\s*([A-Za-z]+)")

# Eight pages read by eye in the session that opened this question.  `side` is
# what the SCAN shows.  ALLOYS carries one figure on each side, so it is marked
# ambiguous and only checked for "did we find a caption at all".
KNOWN = [
    (22, 355, "right"),   # PRIMULACEAE Fig. 2
    (1, 37, "left"),      # ABACUS Fig. 2, Chinese Swan-Pan
    (7, 128, "left"),     # COPPER-PYRITES Figs 1-2
    (3, 648, "left"),     # BEE Fig. 8
    (16, 706, "right"),   # LILIENCRON Fig. 7
    (21, 588, "left"),    # PIANOFORTE Fig. 7
    (1, 931, "left"),     # AMPEREMETER Fig. 2
    (1, 749, None),       # ALLOYS - one figure each side
]


def _template_bodies(text: str):
    """Yield each `{{img float ...}}` body, brace-matched."""
    for m in _OPEN.finditer(text):
        depth, j = 0, m.start()
        while j < len(text):
            if text.startswith("{{", j):
                depth += 1
                j += 2
                continue
            if text.startswith("}}", j):
                depth -= 1
                j += 2
                if depth == 0:
                    break
                continue
            j += 1
        yield text[m.start():j]


def _caption_words(body: str) -> list[str]:
    """Distinctive words from the template's `cap=`, for finding it on the page.

    Template calls inside the caption ({{sc|Fig}}, {{Fs|92%|...}}) are unwrapped
    to their last argument, which is the text that actually prints.
    """
    m = re.search(r"\|\s*cap\s*=(.*?)(?=\|\s*(?:file|width|style|align|alt|class|above|capalign|polygon)\s*=|$)",
                  body, re.S | re.I)
    if not m:
        return []
    cap = m.group(1)
    for _ in range(6):                       # unwrap nested templates, innermost first
        new = _TMPL.sub(lambda t: t.group(0)[2:-2].split("|")[-1], cap)
        if new == cap:
            break
        cap = new
    cap = strip_html_tags(cap, " ")
    cap = re.sub(r"&[a-z]+;", " ", cap)
    words = re.findall(r"[A-Za-z][A-Za-z'-]{4,}", cap)
    # "Fig"/"Plate" appear on every figure; they cannot single one out.
    drop = {"Plate", "Figure", "illustration"}
    return [w for w in words if w not in drop][:6]


def _caption_number(body: str) -> str | None:
    """The figure's printed number, for captions that read only "Fig. 1.".

    Those carry no distinctive word at all, so the number is the only handle on
    which cut the caption belongs to.
    """
    m = re.search(r"\|\s*cap\s*=(.*)$", body, re.S | re.I)
    cap = m.group(1) if m else body
    n = re.search(r"[Ff][Ii][Gg][^A-Za-z0-9]{0,4}(\d{1,3})", cap)
    return n.group(1) if n else None


def _find_caption_line(boxes, words, number):
    """Boxes making up the caption line, by distinctive word or by "Fig. N"."""
    if words:
        hits = [b for b in boxes if any(w.lower().strip("-'") in b[0].lower() for w in words)]
        if hits:
            return hits, "words"
    if number:
        # a "Fig"-ish token immediately followed by the figure's number
        hits = []
        for i, b in enumerate(boxes):
            t = b[0].lower().strip(".,")
            if len(t) > 4 or not t.startswith("fi"):
                continue
            for nxt in boxes[i + 1:i + 3]:
                if re.match(rf"^{number}\b", nxt[0].strip(".,—-")):
                    hits.extend([b, nxt])
                    break
        if hits:
            return hits, f"fig-{number}"
    return [], "none"


def _page_boxes(img_path: Path):
    """OCR one page -> list of (text, x0, x1, y0, y1), confident words only."""
    img = Image.open(img_path)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    out = []
    for i, txt in enumerate(data["text"]):
        txt = (txt or "").strip()
        if not txt or int(data["conf"][i]) < 40:
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        out.append((txt, x, x + w, y, y + h))
    return out, img.size


def _columns(boxes, width):
    """Split the page into its two printed columns.

    EB1911 is set in two columns; the gutter is the x-band the fewest words
    cross, searched in the middle of the page.  Requiring a band NO word crosses
    fails on every real page -- OCR merges a line across the gutter now and
    again, and one stray box is enough -- so this takes the MINIMUM of the
    coverage profile rather than zero, and the widest run at that minimum.
    """
    cov = [0] * (width + 1)
    for _, x0, x1, _, _ in boxes:
        for x in range(max(0, x0), min(width, x1) + 1):
            cov[x] += 1
    lo, hi = int(width * 0.30), int(width * 0.70)
    if hi <= lo:
        return None
    floor = min(cov[lo:hi])
    best_run, best, start = 0, None, None
    for x in range(lo, hi + 1):
        if x < hi and cov[x] <= floor:
            if start is None:
                start = x
        elif start is not None:
            if x - start > best_run:
                best_run, best = x - start, (start, x)
            start = None
    if best is None or best_run < width * 0.005:
        return None
    return best


def _lines(boxes, gutter):
    """Group word boxes into printed lines, split by column.

    -> {"L": [(y, min_x, max_x), ...], "R": [...]}, each sorted by y.
    """
    gl, gr = gutter
    cols = {"L": [], "R": []}
    for b in boxes:
        cx = (b[1] + b[2]) / 2
        if cx < gl:
            cols["L"].append(b)
        elif cx > gr:
            cols["R"].append(b)
    out = {}
    for k, bs in cols.items():
        bs.sort(key=lambda b: b[3])
        lines, cur, cur_y = [], [], None
        for b in bs:
            if cur_y is None or abs(b[3] - cur_y) <= 8:
                cur.append(b)
                cur_y = b[3] if cur_y is None else cur_y
            else:
                lines.append(cur)
                cur, cur_y = [b], b[3]
        if cur:
            lines.append(cur)
        out[k] = [(min(x[3] for x in ln), min(x[1] for x in ln), max(x[2] for x in ln))
                  for ln in lines if len(ln) >= 2]
    return out


def _smooth(tags, half=2, need=2):
    """Majority-filter the per-line tags.

    Two things fragment a raw run.  A line that happens to set long leaves no
    notch, and the CAPTION line -- which sits under the cut, inside its
    horizontal span -- reads as a notch on the OPPOSITE side (a caption under a
    right-floated figure is indented from the column's left, exactly like prose
    beside a left float).  Both are single lines against a band of eight or
    more, so a local majority outvotes them.
    """
    out = []
    for i in range(len(tags)):
        window = [t for t in tags[max(0, i - half): i + half + 1] if t]
        if not window:
            out.append(None)
            continue
        c = Counter(window).most_common(1)[0]
        out.append(c[0] if c[1] >= need else None)
    return out


def _notches(lines, min_run=3, frac=0.18):
    """Bands of consecutive lines cut short on one side -> a float sits there.

    A floated cut displaces the PROSE, and prose OCRs well even where the
    caption (small italic type) does not.  So read the float off the text it
    pushes aside rather than off its own caption.
    """
    if len(lines) < 6:
        return []
    lefts = sorted(l[1] for l in lines)
    rights = sorted(l[2] for l in lines)
    L = lefts[len(lefts) // 2]
    R = rights[len(rights) // 2]
    span = max(1, R - L)
    raw = []
    for (y, x0, x1) in lines:
        if x0 - L > span * frac:
            raw.append("left")                # something occupies the LEFT
        elif R - x1 > span * frac:
            raw.append("right")
        else:
            raw.append(None)
    tagged = list(zip((l[0] for l in lines), _smooth(raw)))
    bands, run, kind = [], [], None
    for (y, t) in tagged:
        if t is not None and t == kind:
            run.append(y)
        else:
            if kind and len(run) >= min_run:
                bands.append((kind, run[0], run[-1], len(run)))
            run, kind = ([y] if t else []), t
    if kind and len(run) >= min_run:
        bands.append((kind, run[0], run[-1], len(run)))
    return bands


def bands_for_page(vol: int, ws_page: int):
    """Every float band the page's prose reveals, in reading order."""
    leaf = leaf_for_ws(vol, ws_page)
    img_path = SCANS / f"vol{vol:02d}_leaf{leaf:04d}.jpg"
    if not img_path.exists():
        return None, _no_scan(img_path)
    boxes, (width, _h) = _page_boxes(img_path)
    gutter = _columns(boxes, width)
    if gutter is None:
        return None, "no column gutter found"
    cols = _lines(boxes, gutter)
    out = []
    for which in ("L", "R"):
        for (kind, y0, y1, n) in _notches(cols[which]):
            out.append({"col": which, "side": kind, "y0": y0, "y1": y1, "lines": n})
    out.sort(key=lambda b: (b["col"], b["y0"]))
    return out, f"{len(out)} band(s)"


def side_for_page(vol: int, ws_page: int, specs: list[dict]):
    """-> list of (spec, side, detail) for each figure requested on this page."""
    leaf = leaf_for_ws(vol, ws_page)
    img_path = SCANS / f"vol{vol:02d}_leaf{leaf:04d}.jpg"
    if not img_path.exists():
        return [(s, None, _no_scan(img_path)) for s in specs]
    boxes, (width, _height) = _page_boxes(img_path)
    gutter = _columns(boxes, width)
    results = []
    for spec in specs:
        words, number = spec.get("words") or [], spec.get("number")
        hits, how = _find_caption_line(boxes, words, number)
        if not hits:
            results.append((spec, None, "caption not found by OCR"))
            continue
        # The caption line: the y-band holding the most hits.
        ys = Counter(h[3] // 20 for h in hits)
        band = ys.most_common(1)[0][0]
        line = [h for h in hits if h[3] // 20 == band]
        cx = sum((h[1] + h[2]) / 2 for h in line) / len(line)
        if gutter is None:
            results.append((spec, None, "no column gutter found"))
            continue
        gl, gr = gutter
        if cx < gl:
            col_lo, col_hi, which = min((b[1] for b in boxes if b[2] <= gl), default=0), gl, "L"
        elif cx > gr:
            col_lo, col_hi, which = gr, max((b[2] for b in boxes if b[1] >= gr), default=width), "R"
        else:
            results.append((spec, None, "caption sits in the gutter"))
            continue
        mid = (col_lo + col_hi) / 2
        side = "left" if cx < mid else "right"
        off = (cx - mid) / max(1, (col_hi - col_lo))
        # A caption centred in its column is a FULL-WIDTH figure, not a float;
        # only a decisive offset is evidence of a side.
        if abs(off) < 0.08:
            results.append((spec, "full-width", f"col{which} off={off:+.2f} via {how}"))
            continue
        results.append((spec, side, f"col{which} centre={cx:.0f} mid={mid:.0f} off={off:+.2f} via {how}"))
    return results


def collect(only_alignless: bool = True):
    """Every {{img float}} in the raw corpus -> rows to survey."""
    rows = []
    # Through `load_pages`, the ONE reader for raw pages: it applies the
    # corrections the pipeline applies (so an `align=` we have already supplied
    # is visible here, and `only_alignless` stops re-offering it), and it RAISES
    # on a page it cannot read.  The `except Exception: continue` this replaces
    # turned an unreadable page into a page the survey said nothing about, which
    # for a survey of "every {{img float}}" is a false CLEAN.
    pages, failures = load_pages()
    if failures:
        raise SystemExit(
            "unreadable source pages: %d (first: %s — %s)"
            % (len(failures), failures[0][0], failures[0][1]))
    for page in pages:
        txt, vol, ws = page.text, page.volume, page.page
        for body in _template_bodies(txt):
            am = _ALIGN.search(body)
            if only_alignless and am:
                continue
            fm = re.search(r"\|\s*file\s*=\s*([^|}\n]+)", body, re.I)
            rows.append({
                "vol": vol, "ws_page": ws, "leaf": leaf_for_ws(vol, ws),
                "file": (fm.group(1).strip() if fm else ""),
                "stated_align": (am.group(1).lower() if am else None),
                "cap_words": _caption_words(body),
                "cap_number": _caption_number(body),
                "body": body,
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--validate", action="store_true",
                    help="run against the eight hand-judged pages and report agreement")
    ap.add_argument("--bands", action="store_true",
                    help="run the text-notch detector over every page holding an align-less float")
    ap.add_argument("--out", help="write the full survey as JSON")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    rows = collect()
    by_page = {}
    for r in rows:
        by_page.setdefault((r["vol"], r["ws_page"]), []).append(r)

    if args.validate:
        agree = disagree = unknown = 0
        for vol, ws, expect in KNOWN:
            rs = by_page.get((vol, ws))
            if not rs:
                print(f"  vol{vol}:{ws}  NO align-less img float found")
                continue
            res = side_for_page(vol, ws, [{"words": r["cap_words"], "number": r["cap_number"]} for r in rs])
            for (spec, side, detail) in res:
                words = spec["words"] or [f'Fig.{spec["number"]}']
                mark = "?"
                if expect is None:
                    mark = "(ambiguous page)"
                elif side == expect:
                    mark = "AGREE"; agree += 1
                elif side is None:
                    mark = "NO READ"; unknown += 1
                else:
                    mark = "DISAGREE"; disagree += 1
                print(f"  vol{vol}:{ws}  eye={expect}  ocr={side}  {mark}  [{detail}]  {words[:3]}")
        print(f"\nagree={agree} disagree={disagree} no-read={unknown}")
        return 0

    if args.bands:
        all_rows = collect(only_alignless=False)
        floats_on_page = {}
        for r in all_rows:
            floats_on_page.setdefault((r["vol"], r["ws_page"]), []).append(r)
        out = []
        pages = sorted(by_page)
        if args.limit:
            pages = pages[:args.limit]
        for n, (vol, ws) in enumerate(pages, 1):
            bands, detail = bands_for_page(vol, ws)
            rec = {
                "vol": vol, "ws_page": ws, "leaf": leaf_for_ws(vol, ws),
                "alignless": [{"file": r["file"], "cap_words": r["cap_words"],
                               "cap_number": r["cap_number"]} for r in by_page[(vol, ws)]],
                "img_floats_on_page": len(floats_on_page.get((vol, ws), [])),
                "bands": bands, "detail": detail,
            }
            out.append(rec)
            print(f"[{n}/{len(pages)}] vol{vol}:{ws} floats={rec['img_floats_on_page']} "
                  f"bands={[(b['col'], b['side'], b['lines']) for b in (bands or [])]}", flush=True)
        if args.out:
            Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"wrote {args.out} ({len(out)} pages)")
        return 0

    out = []
    pages = sorted(by_page)
    if args.limit:
        pages = pages[:args.limit]
    for n, key in enumerate(pages, 1):
        vol, ws = key
        rs = by_page[key]
        res = side_for_page(vol, ws, [{"words": r["cap_words"], "number": r["cap_number"]} for r in rs])
        for r, (_spec, side, detail) in zip(rs, res):
            r.pop("body", None)
            r["scan_side"] = side
            r["detail"] = detail
            out.append(r)
        print(f"[{n}/{len(pages)}] vol{vol}:{ws} -> {[o['scan_side'] for o in out[-len(rs):]]}", flush=True)
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {args.out} ({len(out)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

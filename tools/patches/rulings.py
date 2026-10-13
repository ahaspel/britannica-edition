"""The current disputes (disputes.json) with the judge's verdicts
(judge.json), matched by the site's exact text and context; and two
kinds of site that are not disputes at all, set aside before any ruling:

  moved   the same words on opposite sides of two sites of one page: a block
          assembly moved to its sentence's end (vol 18 p296's table), seen by
          the alignment as a deletion and an insertion
  margin  Wikisource's running text holding the words of one of OUR margin
          headings, garbled into its lines ("triangula", "pnoto t opo",
          "deter triangula mining" for our "determining"): the margin heading
          is checked against the margin by the markup judge

Per page the rulings, and sites with no verdict yet.  Writes
rulings.json {page: {site index: ruling}}.
Usage: rulings.py  (book root)"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from paths import ANSWERS, DISPUTES, RULINGS, reading
from patterns import WORD
sys.stdout.reconfigure(encoding="utf-8")
from judge import ruling

dis = json.loads(DISPUTES.read_text(encoding="utf-8"))
judged = json.loads(ANSWERS.read_text(encoding="utf-8"))
SHOULDER = re.compile(r"\{\{EB1911 Shoulder Heading\|([^{}]*)\}\}")


def ours_raw(page):
    v = int(page[3:5])
    src = reading(page)
    return json.loads(src.read_text(encoding="utf-8"))["raw_text"]


def margin_words(page):
    return {w.lower() for h in SHOULDER.findall(ours_raw(page)) for w in WORD.findall(h)}


def _garbles(t, words):
    """`t` could be a piece of one of the margin heading's words, as OCR
    leaves it: inside one, or most of it ("oeography" for "geography")."""
    import difflib
    return len(t) >= 2 and any(t in w or difflib.SequenceMatcher(None, t, w).ratio() >= 0.75
                               or difflib.SequenceMatcher(None, t, w[:len(t)]).ratio() >= 0.75 for w in words)


def is_margin(site, words):
    """Some of Wikisource's tokens here are our margin heading's words, garbled
    into its line, and what remains of its side, joined, is exactly ours
    (nothing, or "deter" + "mining" = "determining")."""
    toks = site["ws"].split()
    if not words or not toks or len(toks) > 10:
        return False
    target = site["ours"].replace(" ", "")
    for mask in range(1, 1 << len(toks)):
        out = [t for i, t in enumerate(toks) if mask >> i & 1]
        if all(_garbles(t, words) for t in out) and \
                "".join(t for i, t in enumerate(toks) if not mask >> i & 1) == target:
            return True
    return False


CAPTION = re.compile(r"^fig \d+\b")


def _norm(t):
    import unicodedata
    return " ".join(re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", t).lower()))


def is_caption(site, ours_norm):
    """One side alone has a figure's label or caption ("fig 3 composite
    joint", "fig 4"): printed under its figure, set by each text where it
    sets the figure — placement, not a reading.  Ours alone: it is set by our
    figure.  Wikisource's alone: only if every "fig N …" piece of it is on our
    page too — else it may hold text we lack ("fig 32 excite its second mode
    …": vol 25 p469), and is judged as any site."""
    if site["ws"].strip() and site["ours"].strip():
        return False
    if site["ours"].strip():
        return bool(CAPTION.match(site["ours"].strip()))
    ws = site["ws"].strip()
    if not CAPTION.match(ws):
        return False
    pieces = [p.strip() for p in re.split(r"(?=\bfig \d+)", ws) if p.strip()]
    return all(_norm(p) in ours_norm for p in pieces)


sig = {}
for key, sites in judged.items():
    for s in sites:
        if not s["truth"]:
            sig[(key.split(":")[0], s["ws"], s["ours"], s["before"], s["after"])] = ruling(s)
out, tot = {}, Counter()
per = defaultdict(Counter)
for page, r in dis.items():
    out[page] = {}
    sites = r["sites"]
    words = margin_words(page)
    ours_norm = _norm(ours_raw(page))
    ws_sides = Counter(s["ws"] for s in sites if s["ws"] and not s["ours"])
    our_sides = Counter(s["ours"] for s in sites if s["ours"] and not s["ws"])
    for n, s in enumerate(sites):
        k = (page, s["ws"], s["ours"], s["before"], s["after"])
        if (not s["ours"] and our_sides[s["ws"]]) or (not s["ws"] and ws_sides[s["ours"]]):
            v = "moved"
        elif is_caption(s, ours_norm):
            v = "caption"
        elif is_margin(s, words):
            v = "margin"
        elif k in sig:
            v = sig[k]
        else:
            v = "NOT JUDGED"
        out[page][n] = v
        per[page][v] += 1
RULINGS.write_text(json.dumps(out, indent=1), encoding="utf-8")
for c in per.values():
    tot.update(c)
print("sites:", dict(tot))
g = Counter("CLEAN" if not c["ws"] and not c["unsure"] and not c["NOT JUDGED"] else
            "OUR ERRORS" if c["ws"] else "UNSURE/UNJUDGED" for c in per.values())
print("pages:", dict(g), "of", len(per))

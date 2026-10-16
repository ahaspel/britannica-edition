"""Is every supplied page fit to stand in for the page it replaces?  THE gate
for `data/supplied/`: the rebuild runs it before anything else (Phase 0) and
stops on a failure.

    uv run python tools/diagnostics/supplied_gate.py [-v]

WHAT IT GATES is what the door lets in.  `wikikit.source_pages.prefer` decides
which of a fetched page and a supplied page the book reads; a supplied page the
door holds back changes nothing, so it is listed (HELD), never failed.  A page
the door lets in must pass every check below.  Each check caught a real fault:

  complete  no text item the model refused or left unread, unchecked — and the
            page's own `pagequality` says so, because that is what the door
            reads.  Fifteen holed pages replaced complete Wikisource pages and
            shipped ~3,300 words short (2026-10-10).
  words     no run of MISSING_RUN of the fetched page's words absent from ours
            (a strip not read), and >= 60% of its distinct words shared (a
            wrong page).  Both sides are walked by the pipeline and reduced to
            words by `countable_word_list` — the shipped word-count policy —
            never by stripping wikitext here.
  leaf      read from the leaf the site's viewer shows (vol 20's Bengal copy;
            vol 6's splice)
  printed   the number read off the leaf = production's number for the page;
            a page production gives no number is not supplied at all
  sections  every section the fetched page opens, ours opens, in order, and not
            empty where the fetched one has text (SEWER/SEWERAGE, TARTAN)
  head      the running head read, and in the header, never the body (vol 28
            p487)
  lines     where the fetched page keeps lines (<poem>), ours keeps them in
            some block (vol 25 p539)
  images    every image the fetched page sets (a wiki-store file, an editor's
            region of the scan) stands on ours, unless a recorded decision
            says why not: 335 figures had been replaced by our own crops
  assembled raw_text is what the page's readings assemble to now — never
            edited on its own, never stale against the fetched page
  carry     the fetched page's tables and links carried onto ours, nothing
            left unplaced (`wikikit.scan.carry`)
  lacks     no element the fetched page has — formula, figure, table, cell,
            footnote, link, margin heading, poem, contributor's initials —
            missing from ours, unless
            the page records why (`lacks_decided`).  Whole pages lost 26
            footnotes from SPECTROSCOPY and 12 margin headings from SURVEYING
            to checks that compared words (2026-10-12)

Production's printed numbers come from the live site.  Read-only.  Exit 1 on
any failure.

Promoted 2026-10-10 from a session scratch file that had rotted unnoticed (it
imported a helper since renamed and a module since deleted): a gate that is
not run by the build is not a gate.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from eb1911.scans import ARCHIVE_SHIFT, NotATextPage, page_leaf
from wikikit.db.models import SourcePage
from wikikit.markers import countable_word_list
from wikikit.pipeline.stages.elements import ElementContext, process_elements
from wikikit.pipeline.stages.preprocess import stream_with_keys
from wikikit.scan import carry, images, supplied
from wikikit.source_pages import fetched_text, page_level, prefer

ROOT = Path(__file__).resolve().parents[2]
SUPPLIED = ROOT / "data" / "supplied"
LIVE_PRINTED = "https://britannica11.org/data/printed_pages.json"

#: OCR garbles a formula or a word here and there: a run this long of the
#: fetched page's words absent from ours is text we did not read.
MISSING_RUN = 30
#: Below this share of the fetched page's distinct words, ours is another page.
MIN_SHARE = 0.6

#: A section is its begin tag to the next section tag or the page's end: the
#: pipeline reads the begin tag alone (`detect_boundaries`), and the
#: transcriber writes no end tag — a gate demanding one failed 52 good pages
#: (2026-10-12)
_SECTION = re.compile(r'<section\s+begin\s*=\s*"?([^"/>]+?)"?\s*/>([\s\S]*?)(?=<section\b|\Z)')
_HEADER = re.compile(r"\{\{RunningHeader\|([^}]*)\}\}")


def walked(v: int, p: int, text: str) -> str:
    """The page as the pipeline walks it: corrections, preprocessing, the walk."""
    stream, _, _ = stream_with_keys([SourcePage(volume=v, page_number=p, wikitext=text)], v)
    return process_elements(stream, ElementContext(volume=v))


def words(v: int, p: int, text: str) -> list[str]:
    return [w.lower() for w in countable_word_list(walked(v, p, text))]


def _prose(ws: list[str]) -> list[str]:
    """The words of four letters or more.  Wikisource's raw OCR reads a formula
    as letter salad (`sinh y i cos x iy …`, 66 tokens on vol 27 p295) where we
    read `<math>`, which counts no words; the salad is mostly short tokens, and
    a strip of prose we failed to read is long runs of these."""
    return [w for w in ws if len(w) >= 4 and w.isalpha()]


def missing_run(theirs: list[str], ours: list[str]) -> int:
    """The longest run of the fetched page's prose words, in order, that ours
    does not have — each of ours matched once."""
    theirs, ours = _prose(theirs), _prose(ours)
    have = Counter(ours)
    run = best = 0
    for w in theirs:
        if have[w] > 0:
            have[w] -= 1
            run = 0
        else:
            run += 1
            best = max(best, run)
    return best


def source_leaf(v: int, scan: str) -> int | None:
    """The SITE leaf a transcription names as its source (page_scan_url's
    three forms: Wikisource's vol 20 djvu page, a site scan file, an archive
    leaf — vol 6's past its splice shifted back to the site's numbering)."""
    if m := re.search(r"Volume_20\.djvu/(\d+)", scan):
        return int(m.group(1)) + 1
    if m := re.search(r"leaf(\d+)\.jpg", scan):
        return int(m.group(1))
    if m := re.search(r"/page/n(\d+)", scan):
        n = int(m.group(1))
        start, shift = ARCHIVE_SHIFT.get(v, (None, 0))
        return n - shift if start is not None and n - shift >= start else n
    return None


def checks(d: dict, ws: str | None, live: dict):
    v, p, raw, pv = d["volume"], d["page_number"], d["raw_text"], d["provenance"]
    ws = ws or ""
    if supplied.level(d) == 2 or page_level(raw) == 2:
        yield "complete", ("text not read: " + ", ".join(
            [*pv.get("refused", []), *pv.get("unread", {})]))
    if (supplied.level(d) == 2) != (page_level(raw) == 2):
        yield "complete", (f"the readings make it level {supplied.level(d)}, its pagequality "
                           f"says {page_level(raw)}: the door reads the pagequality")

    want = live.get(str(v), {}).get(str(p))
    if want is None:
        yield "printed", "production gives this page no number: a plate or a blank is not supplied"
        return
    should = None
    try:
        should = page_leaf(v, p)
    except NotATextPage as e:
        yield "leaf", str(e)
    read_from = source_leaf(v, pv["scan"])
    if should is not None and read_from != should:
        yield "leaf", f"read from leaf {read_from}; the page is leaf {should}"

    header, _, body = raw.partition("</noinclude>")
    m = _HEADER.search(header)
    nums = [int(x) for x in re.findall(r"\b(\d{1,4})\b", m.group(1))] if m else []
    if len(nums) == 1 and nums[0] != want:
        yield "printed", f"the leaf prints p. {nums[0]}, production's page is p. {want}"
    if not (m and m.group(1).strip("|")):
        yield "head", "no running head read"
    if "{{RunningHeader" in body:
        yield "head", "a running head in the body"

    theirs_w, ours_w = words(v, p, ws), words(v, p, raw)
    vocab = {w for w in theirs_w if len(w) >= 5 and w.isalpha()}
    if len(vocab) >= 40:
        share = len(vocab & set(ours_w)) / len(vocab)
        if share < MIN_SHARE:
            yield "words", f"shares {share:.0%} of the fetched page's words"
        if not nums and share < 0.9:
            yield "printed", "no page number read, and the words do not vouch for the page"
    run = missing_run(theirs_w, ours_w)
    if run >= MISSING_RUN:
        yield "words", f"{run} of the fetched page's words in a row are not on ours (text lost)"

    theirs_s, ours_l = _SECTION.findall(ws), _SECTION.findall(raw)
    ours_s = dict(ours_l)
    names, ours_names = [n for n, _ in theirs_s], [n for n, _ in ours_l]
    if [n for n in ours_names if n in names] != names:
        yield "sections", f"sections {ours_names}, the fetched page's {names}"
    for name, text in theirs_s:
        if name in ours_s and words(v, p, text) and not words(v, p, ours_s[name]):
            yield "sections", f"section {name} empty"

    # Wikisource's <poem> keeps lines — verse, a list, but also a column of a
    # table faked line by line (vol 25 p120), a run of formulas (vol 27 p288), a
    # caption (vol 27 p191): ours must keep them in some block — a <poem>, a
    # table, displayed formulas, centred lines — not run them into paragraphs
    if "<poem" in ws and not re.search(r"<poem|\{\||\{\{block center\|<math>|\{\{c\|", raw):
        yield "lines", "the fetched page keeps lines (<poem>); ours keeps none in any block"
    big = max((m.group(1).count("\n") for m in re.finditer(r"<poem>([\s\S]*?)</poem>", ws)), default=0)
    if big >= 30 and not re.search(r"<poem|\{\|", raw):
        yield "lines", f"the fetched page keeps a list of {big} lines; ours has no <poem> or table"

    # a supplied page replaces the TEXT; the images are source.  Every image
    # the fetched page sets — a wiki-store file, an editor's region of the
    # scan — stands on ours, as written (`wikikit.scan.images`): 335 figures
    # on 152 pages had been replaced by our own crops and shipped
    # (2026-10-09).  Leaving one out is a recorded decision (`images_decided`:
    # a formula or table ours transcribes as text), never silent.
    if pv.get("images_unplaced"):
        yield "images", "; ".join(pv["images_unplaced"])
    # the same image however ours sets it: floated beside its type, captioned
    on_ours = images.identities_on(raw)
    left = [s["markup"] for s in images.source_images(ws) if images.identity(s["markup"]) not in on_ours]
    if left and not pv.get("images_decided"):
        yield "images", (f"{len(left)} of the fetched page's images not on ours: "
                         + "; ".join(m.replace("\n", " ")[:60] for m in left))

    # the page as the engine assembles it now — readings, images, regions, the
    # carry against the fetched page as filed: `raw_text` is never edited on
    # its own, and a fetched page refetched since moves what the carry lays
    again = supplied.reassemble(copy.deepcopy(d), fetched=ws)["raw_text"]
    if again != raw:
        yield "assembled", "raw_text is not what its readings assemble to now: reassemble the page"

    # what a person built on Wikisource's page — its tables and links — is
    # carried onto ours (`wikikit.scan.carry`); a table ours sets better
    # (formulas, figures, lines, a table Wikisource left unfinished) is kept,
    # by rule, and recorded
    if (carry.tables(ws) or carry.links(ws)) and "carried" not in pv:
        yield "carry", "the fetched page's tables and links are not carried (supplied.carry_markup)"
    for u in pv.get("carried", {}).get("unplaced", []):
        yield "carry", u

    # a page entering whole lacks nothing the fetched page has, element by
    # element as the pipeline walks them (2026-10-12: SPECTROSCOPY lost 26
    # footnotes, SURVEYING 12 margin headings, to whole pages) — unless the
    # page records why (`lacks_decided`: kind -> reason)
    ours_n, theirs_n = elements(v, p, raw), elements(v, p, compared(ws, pv))
    decided = pv.get("lacks_decided", {})
    for kind, n in theirs_n.items():
        if n - ours_n[kind] >= SLACK.get(kind, 1) and kind not in decided:
            yield "lacks", f"{n - ours_n[kind]} {kind} the fetched page has"


#: What `elements` counts, as the walker marks it.  An .svg is a glyph (⟨).
ELEMENTS = {
    "formulas": r"«MATH",
    "figures": r"\{\{IMG:(?![^|}]*\.svg)|«IMG",
    "tables": r"«TABLE",
    "cells": r"«T[DH][\[»]",
    "footnotes": r"«FN|«REF",
    "links": r"«LN:",
    "margin headings": r"«SH:",
    "poems": r"«POEM",
    # a contributor's initials closing an article ({{EB1911 footer initials}}):
    # the attribution binds from them, so a whole page may not drop them
    # (6,953 fetched pages carry them; markup_census.py, 2026-10-15)
    "signatures": r"«SPAN\[style:float:right\]»\([^«»()]{1,40}\)«/SPAN»",
}
#: Below these a difference is how cells were split, no loss.
SLACK = {"cells": 2}


def elements(v: int, p: int, text: str) -> Counter:
    w = walked(v, p, text)
    return Counter({k: len(re.findall(pat, w)) for k, pat in ELEMENTS.items()})


def compared(ws: str, pv: dict) -> str:
    """The fetched page as ours answers for it: without the tables the carry
    keeps ours for (their spans recorded in the fetched page), and without a
    picture standing in for a missing table (`images.source_images`)."""
    kept = sorted((s for v in pv.get("carried", {}).get("tables kept", {}).values() for s in v),
                  reverse=True)
    for a, b in kept:
        ws = ws[:a] + ws[b:]
    return images.without_table_pictures(ws)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true", help="list the held pages' gaps too")
    args = ap.parse_args()
    req = urllib.request.Request(LIVE_PRINTED, headers={"User-Agent": "supplied_gate"})
    live = json.loads(urllib.request.urlopen(req, timeout=60).read())

    fails, held, pages, entered = {}, [], 0, 0
    for f in sorted(SUPPLIED.glob("vol_*/*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        pages += 1
        ws = fetched_text(d["volume"], d["page_number"])
        if prefer({"raw_text": ws} if ws is not None else None, d) is not d:
            held.append((f.name, list(checks(d, ws, live))))
            continue
        entered += 1
        found = list(checks(d, ws, live))
        if found:
            fails[f.name] = found
    # patched pages: every patch at its place, the fetched page's structure
    # unchanged (`wikikit.scan.patches.check`), and no supplied page ENTERING
    # for a patched one (the patches would never be read).  A supplied page the
    # door holds — waiting to be proofread at the desk — replaces nothing, and
    # the patched page stands meanwhile.
    from wikikit.scan.patches import check as check_patches, load_patches
    patched = n_patches = 0
    for key, ps in load_patches().items():
        v, p = (int(x) for x in key.split(":"))
        name = f"patches {key}"
        sup = SUPPLIED / f"vol_{v:02d}" / f"vol{v:02d}-page{p:04d}.json"
        if sup.exists():
            d = json.loads(sup.read_text(encoding="utf-8"))
            ws = fetched_text(v, p)
            if prefer({"raw_text": ws} if ws is not None else None, d) is d:
                fails[name] = [("patches", "a supplied page enters for this page: its patches are "
                                            "never read — drop them (install.py) as it enters")]
                continue
        bad = check_patches(fetched_text(v, p) or "", ps)
        if bad:
            fails[name] = [("patches", "; ".join(bad))]
        patched += 1
        n_patches += len(ps)
    for name, why in fails.items():
        print(f"  FAIL {name}: " + "; ".join(f"{kind}: {reason}" for kind, reason in why))
    print(f"{patched} patched pages, {n_patches} patches checked")
    for name, why in held:
        gaps = "; ".join(w for k, w in why if k == "complete") or "the fetched page stands"
        print(f"  HELD {name}: {gaps}" if args.verbose else f"  HELD {name}")
    print(f"{pages} supplied pages: {entered} enter, {len(held)} held back by the door; "
          f"{len(fails)} fail" + ("" if fails else " — GATE PASSES"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

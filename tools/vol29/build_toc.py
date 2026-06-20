"""Build the vol-29 'Classified List of Articles' division from the raw scans.

ONE job: turn the split-scan OCR into 24 clean, in-order category chunks.

This is the basis for everything downstream, so it owns the WHOLE transform and
reads the raw half-page transcriptions -- not the lossy pre-assembled stream:

  decruft each half  ->  band at the surviving major banners  ->  zip the two
  halves (left page, then right)  ->  divide into the 24 categories.

The governing fact (user-confirmed, zero exceptions): the ONLY header that
crosses the gutter we want to keep is a major category's FIRST banner.  Every
other thing that crosses a page or half boundary is cruft -- the running page
header, a major category's running-header REPEAT on its later pages, a section
reprinted with `(cont.)` -- and is removed BEFORE any banding.  Strip the cruft
and the order fixes itself: a one-sided running header used to split a phantom
band that shoved one half's content past the other's; with it gone, the two
halves band in step and read left-then-right.

The 24 print in a fixed, KNOWN order, so a wall is pinned by SEQUENCE: a banner
only ever opens the NEXT category.  That single rule disambiguates a gutter-clip
("logy" is Bio- or Geo-logy in the abstract, but after Astronomy it can only be
Biology) and rejects a coincidence (Zoology's "Natural History" -> History, a
clipped "Geo" after Geography -> the running header, never the Geology wall).

Self-contained: stdlib only.  Primary input is the saved half-transcriptions
(data/derived/vol29_halves_debug.json); pages without saved halves fall back to
the pre-assembled stream (data/derived/vol29_ocr.json), decrufted in place --
a bridge until every page's halves exist.  Output is the 24 chunks
(data/derived/toc_category_chunks.json), each a name + all its bytes, in order.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HALVES = Path("data/derived/vol29_halves_debug.json")
OCR = Path("data/derived/vol29_ocr.json")
OUT = Path("data/derived/toc_category_chunks.json")
WS_START, WS_END = 891, 955

# A section reprinted where it spilled across a page/half break carries a
# "(cont.)" / "(*cont.*)" marker -- the tell that it is a repeat, not a new head.
_CONT_RE = re.compile(r"\(\s*\*?\s*cont\.?\s*\*?\s*\)", re.I)

# Words that make up the gutter-split PAGE RUNNING HEADERS (the category /
# continent / section label reprinted atop every page).  A header whose edge
# token is a strict fragment of one of these was cut mid-word by the gutter --
# a clip, not a whole subcategory header (which uses the whole word).
_RH_VOCAB = ["EUROPE", "ASIA", "AFRICA", "AMERICA", "AUSTRALASIA", "OCEANIC",
             "PHYSICAL", "FEATURES", "COUNTRIES", "DIVISIONS", "TOWNS", "ISLANDS",
             "CONTINENTAL", "GENERAL", "MOUNTAINS", "RIVERS", "LAKES", "ANCIENT",
             "MISCELLANEOUS", "HISTORY", "GEOGRAPHY", "GREAT", "BRITAIN"]

# Bare section-type words.  At MAJOR-header level (`## `) a header of only these
# -- no place, no topic -- is a gutter-split running-header label ("DIVISIONS AND
# TOWNS", "...—COUNTRIES"); a real section-type header is `### ` (### General).
_SECTION_TYPES = frozenset(
    {"DIVISIONS", "TOWNS", "COUNTRIES", "AND", "PHYSICAL", "FEATURES"})


def _is_clip_header(s: str) -> bool:
    """True if `s` is a CLIPPED page-running-header fragment, not a whole
    subcategory header.  Only header lines (`#`/`**`) qualify -- a link or a
    marginal note is never one.  A clip is INCOMPLETE: it starts mid-word, ends
    on a dash, leaves a paren unclosed, or its first/last token is a strict
    fragment of the continent/section vocabulary.  A whole header uses the whole
    word, so it never trips these."""
    if not (s.startswith("#") or s.startswith("**")):
        return False
    body = re.sub(r"^#+\s*", "", s).strip().strip("*").strip()
    if not body:
        return True                              # an empty header is furniture
    if body[0].islower() or not body[0].isalnum():
        return True                              # starts mid-word or on punctuation
    if body.rstrip(").").endswith(("-", "—")):
        return True                              # ends on a dash -- cut mid-phrase
    if body.count("(") != body.count(")"):
        return True                              # an unbalanced paren -- cut across it
    if "—" in body:
        tail = re.sub(r"[^A-Za-z]", "", body.rsplit("—", 1)[1])
        if 0 < len(tail) <= 2:
            return True                          # a dash + 1-2 char stub -- cut mid-word
    toks = re.findall(r"[A-Za-z]+", body)
    if toks:
        last, first = toks[-1].upper(), toks[0].upper()
        for w in _RH_VOCAB:
            if len(last) >= 2 and last != w and w.startswith(last):
                return True                      # last token a clipped head of a RH word
            if len(first) >= 2 and first != w and w.endswith(first):
                return True                      # first token a clipped tail of a RH word
        if s.startswith("## ") and all(t.upper() in _SECTION_TYPES for t in toks):
            return True                          # bare section-type at major level
    return False

# The 24 major categories, in printed order.
CATEGORIES = [
    "Anthropology and Ethnology", "Archaeology and Antiquities", "Art",
    "Astronomy", "Biology", "Chemistry", "Economics and Social Science",
    "Education", "Engineering", "Geography", "Geology", "History",
    "Industries, Manufactures and Occupations", "Language and Writing",
    "Law and Political Science", "Literature", "Mathematics",
    "Medical Science", "Military and Naval", "Philosophy and Psychology",
    "Physics", "Religion and Theology", "Sports and Pastimes", "Miscellaneous",
]

# Art prints no full-width banner of its own -- it is a group of sub-arts -- so
# it opens on the first of THESE sub-art section banners.  Its decrufted boundary
# is normalized to "## Art", so "art" is an opener too (matched downstream).
ART_OPENERS = ["Architecture", "Music", "Painting and Engraving",
               "Sculpture", "Minor Arts", "Stage and Dancing"]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _banner_token(line: str) -> str:
    """A `## ` banner line -> its category-name part, normalized.  Drop any
    `: Subjects` / `*...*` section tail the model appended to the banner."""
    return _norm(re.sub(r"[*:].*$", "", line.strip()[3:]))


def category_openers() -> list[tuple[str, list[str]]]:
    """In printed order, each category and the banner tokens that open it: its
    own name, except Art, which opens on its sub-art banners (plus "art", the
    name its decrufted boundary normalizes to)."""
    openers: list[tuple[str, list[str]]] = []
    for c in CATEGORIES:
        toks = ([_norm(t) for t in ART_OPENERS] + ["art"]) if c == "Art" \
            else [_norm(c)]
        openers.append((c, toks))
    return openers


def _opens(banner: str, tokens: list[str]) -> bool:
    """A banner opens a category if its (possibly gutter-clipped) name token is a
    prefix/suffix of one of the category's opener tokens, or vice versa.  A clip
    shorter than 3 chars is too ambiguous to seat a wall."""
    for t in tokens:
        if not t or len(banner) < 3:
            continue
        if (t == banner or t.startswith(banner) or t.endswith(banner)
                or banner.startswith(t) or banner.endswith(t)):
            return True
    return False


def _advance(bt: str, openers: list[tuple[str, list[str]]], cur: int) -> int | None:
    """One step of the known-order walk: if this banner token opens the NEXT
    category (and is not just a repeat of the current one), return cur+1, else
    None.  "Geo" after Geography opens Geology AND Geography, so the `not
    current` clause keeps it a repeat; "Geol" opens only Geology, so it walls."""
    nxt = cur + 1
    if (nxt < len(openers) and _opens(bt, openers[nxt][1])
            and not (cur >= 0 and _opens(bt, openers[cur][1]))):
        return nxt
    return None


def _decruft(lines: list[str], openers: list[tuple[str, list[str]]],
             cur: int) -> tuple[list[str], int]:
    """Strip page furniture and continuation repeats from one half's lines,
    returning the clean lines and the final known-order category index.

    Removed: the running page header (`CLASSIFIED LIST OF ARTICLES` + clips);
    HTML-comment furniture (the split-scan tag); a `(cont.)` continuation header;
    and the running-header REPEAT of the current major category.  KEPT: content,
    section headers (a continent, a country), and the FIRST banner of each major
    category -- normalized to its full name so the band split is unambiguous."""
    out: list[str] = []
    for line in lines:
        s = line.strip()
        if not s:
            continue  # blank line -- spacing furniture, neither header nor link
        n = _norm(s.lstrip("# "))
        if len(n) >= 5 and n in "classifiedlistofarticles":
            continue  # running page header -- furniture
        if s.startswith("<!--"):
            continue  # html-comment furniture (e.g. the split-scan tag)
        if _CONT_RE.search(s):
            continue  # a `(cont.)` marker -- a section reprinted across the break
            # (any prefix: `### `, `**bold**`, or none -- the model is inconsistent)
        if s.startswith("## "):
            bt = _banner_token(line)
            nxt = _advance(bt, openers, cur)
            if nxt is not None:
                cur = nxt
                out.append(f"## {openers[cur][0]}")  # first appearance -- kept
                continue
            if cur >= 0 and _opens(bt, [_norm(openers[cur][0])]):
                continue  # running-header repeat of the current major category
        if _is_clip_header(s):
            continue  # a clipped page-running-header fragment, not a whole header
        out.append(line)
    return out, cur


def _bands(lines: list[str],
           openers: list[tuple[str, list[str]]]) -> list[list]:
    """Split decrufted lines into [banner_or_None, [lines]] bands at each
    surviving major banner -- now guaranteed a real, first-appearance boundary,
    so both halves split in step.  The first band (None) holds the incoming
    category's content."""
    cat_norms = {_norm(c) for c, _ in openers}
    segs: list[list] = [[None, []]]
    for line in lines:
        s = line.strip()
        if s.startswith("## ") and _norm(s[3:]) in cat_norms:
            segs.append([s, []])
        else:
            segs[-1][1].append(line)
    return segs


def _align_bands(left: list[list], right: list[list],
                 openers: list[tuple[str, list[str]]]
                 ) -> tuple[list[list], list[list]]:
    """Align the two halves' major-category bands so they zip in step.  A banner
    one half clipped away entirely leaves that half short a band; insert an EMPTY
    placeholder for it (never drop the banner -- dropping shoves the other half's
    content past it, into the wrong category)."""
    order = {_norm(c): i for i, (c, _) in enumerate(openers)}

    def cat(b):
        return _norm(b[0][3:]) if b[0] else None

    merged = sorted({cat(b) for b in left[1:]} | {cat(b) for b in right[1:]},
                    key=lambda c: order.get(c, len(order)))

    def rebuild(bands):
        by = {cat(b): b for b in bands[1:]}
        return [bands[0]] + [by.get(c, [None, []]) for c in merged]

    return rebuild(left), rebuild(right)


def assemble_spread(left_text: str, right_text: str,
                    openers: list[tuple[str, list[str]]],
                    incoming: int) -> tuple[str, int]:
    """Decruft both halves from the same incoming category, then read the spread
    BAND-BY-BAND: the surviving major banners cut both halves into the same
    bands, so per band we emit the banner once, then the left page's lines, then
    the right's -- a category spanning the gutter stays together and in reading
    order.  Returns the assembled text and the outgoing category index."""
    llines, lcur = _decruft(left_text.split("\n"), openers, incoming)
    rlines, rcur = _decruft(right_text.split("\n"), openers, incoming)
    left, right = _align_bands(_bands(llines, openers),
                               _bands(rlines, openers), openers)
    out: list[str] = []
    for i in range(max(len(left), len(right))):
        banner = ((left[i][0] if i < len(left) else None)
                  or (right[i][0] if i < len(right) else None))
        if banner:
            out.append(banner)
        if i < len(left):
            out.extend(left[i][1])
        if i < len(right):
            out.extend(right[i][1])
    return "\n".join(out), max(lcur, rcur)


def assemble_sequence(openers: list[tuple[str, list[str]]]
                      ) -> list[tuple[int, int, str]]:
    """The whole list, page by page in order, decrufted and assembled -> [(ws,
    idx, line)].  A page with saved halves is assembled clean from them; one
    without falls back to its pre-assembled stream text, decrufted in place (no
    re-band -- a bridge until its halves exist).  The known-order category index
    threads across pages, so each page's incoming category is just what flowed
    out of the last."""
    halves = json.loads(HALVES.read_text(encoding="utf-8")) if HALVES.exists() \
        else {}
    ocr = json.loads(OCR.read_text(encoding="utf-8")) if OCR.exists() else {}
    cur = -1
    seq: list[tuple[int, int, str]] = []
    for ws in range(WS_START, WS_END + 1):
        key = str(ws)
        if key in halves:
            text, cur = assemble_spread(
                halves[key]["left"], halves[key]["right"], openers, cur)
        elif ocr.get(key):
            lines, cur = _decruft(ocr[key].split("\n"), openers, cur)
            text = "\n".join(lines)
        else:
            continue
        seq.extend((ws, i, ln) for i, ln in enumerate(text.split("\n")))
    return seq


def build_category_chunks(seq, openers):
    """Slice the assembled stream into (category, lines) chunks: every line from
    a category's wall up to the next category's wall.  Advance ONLY when a banner
    opens the next category; everything else stays in the current chunk.  Each
    line belongs to exactly one category, so the chunks partition the stream --
    nothing dropped, nothing shared.  `preamble` holds anything before wall 1."""
    preamble: list[tuple[int, int, str]] = []
    chunks: list[list] = []
    cur = -1
    for ws, idx, line in seq:
        s = line.strip()
        if s.startswith("## "):
            nxt = _advance(_banner_token(line), openers, cur)
            if nxt is not None:
                cur = nxt
                chunks.append([openers[cur][0], []])
        (chunks[cur][1] if cur >= 0 else preamble).append((ws, idx, line))
    return preamble, chunks


def main() -> None:
    openers = category_openers()
    seq = assemble_sequence(openers)
    preamble, chunks = build_category_chunks(seq, openers)

    def asc(x: str) -> str:
        return x.encode("ascii", "backslashreplace").decode()

    def nbytes(lines) -> int:
        return sum(len(l) for _, _, l in lines)

    print(f"assembled {len(seq):,} lines / {nbytes(seq):,} bytes "
          f"from pages {WS_START}-{WS_END}\n")
    print(f"{len(chunks)} category chunks  (name + every byte inside):")
    for i, (cat, lines) in enumerate(chunks, 1):
        ws0, idx0, _ = lines[0]
        print(f"  {i:2d}. {asc(cat):34s} ws{ws0}:{idx0:<3d}  "
              f"{len(lines):5,d} lines  {nbytes(lines):7,d} bytes")

    total, accounted = nbytes(seq), nbytes(preamble) + sum(
        nbytes(l) for _, l in chunks)
    print(f"\npreamble before first wall: {nbytes(preamble)} bytes")
    print(f"bytes conserved: {accounted:,} / {total:,}  "
          f"({'all accounted for' if accounted == total else 'LOSS'})")
    print(f"all 24, in printed order: {[c for c, _ in chunks] == CATEGORIES}")

    OUT.write_text(json.dumps(
        [{"name": c, "text": "\n".join(l for _, _, l in ls)} for c, ls in chunks],
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

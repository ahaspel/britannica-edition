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
TREE = Path("data/derived/toc_tree.json")
CLASSIFIED = Path("data/derived/classified_toc.json")
WS_START, WS_END = 891, 955

# The printed Classified-TOC index (pp.881-2 = ws 889-890): a marker-tagged
# wikitable that carries the AUTHORITATIVE upper structure of every category --
# levels 1-3 (sometimes 4), but no article links.  We graft the body's flat
# sections beneath these nodes; we never add a top-level sibling the index lacks.
INDEX_DIR = Path("data/raw/wikisource/vol_29")
INDEX_PAGES = (889, 890)

# A marginal note is a cross-reference instruction, not a link: it opens with a
# parenthesis and/or "For"/"See" (a word boundary keeps "Forster" a real link).
_NOTE_RE = re.compile(r"^\(?\s*\*?\s*(For|See)\b", re.I)

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
            # A token that is ITSELF a complete RH word (e.g. "Asia") is a real
            # word, never a clip -- even though it is a tail of a longer one
            # ("Australasia").  Only a strict fragment counts as a clip.
            if (last not in _RH_VOCAB and len(last) >= 2 and last != w
                    and w.startswith(last)):
                return True                      # last token a clipped head of a RH word
            if (first not in _RH_VOCAB and len(first) >= 2 and first != w
                    and w.endswith(first)):
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

# The page running header is the work title set in blackletter; the OCR reads the
# Gothic "History" as "Dis" + "story" across the gutter (the "Hi" ligature scans
# as "Dis").  "Hist"/"story"/"History" already match "history" as a prefix/suffix
# and are stripped as the running-header repeat -- but "Dis" matches nothing, so
# it leaks and step 3 builds it into a bogus node.  Name it here as the History
# header it actually is, so the same repeat-strip catches it.
_RH_MISOCR = {"History": ("dis",)}


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


def _is_caps_banner(s: str) -> bool:
    """A `## ` / `**` line whose text is mostly capitals -- a full-width section/
    continent banner, not a mixed-case country header (those are `### ` or
    `**Name**`)."""
    if not (s.startswith("## ") or s.startswith("**")):
        return False
    body = re.sub(r"\(.*?\)", "", re.sub(r"[#*]", "", s)).strip()
    letters = [c for c in body if c.isalpha()]
    return bool(letters) and sum(c.isupper() for c in letters) / len(letters) > 0.7


_CONT_CACHE: dict | None = None


def _cat_continents() -> dict:
    """{category -> [(subcat name, [section child names])]} from the index -- the
    known continent/section banners to recognise inside each category."""
    global _CONT_CACHE
    if _CONT_CACHE is None:
        _CONT_CACHE = {
            cat: [(s["name"], [c["name"] for c in s.get("children", [])])
                  for s in subs]
            for cat, subs in parse_index().items()}
    return _CONT_CACHE


def _banner_words(s: str) -> list[str]:
    t = re.sub(r"\(.*?cont.*?\)", "", s, flags=re.I)
    return [_norm(w) for w in re.split(r"[—–\-\s]+", re.sub(r"[#*]", "", t))
            if _norm(w)]


def _is_subcat_banner(s: str, cat_name: str) -> bool:
    """True if `s` is a full-width banner naming one of `cat_name`'s index subcats
    (a continent or section) -- a real subcat to KEEP -- as opposed to a page
    running-header repeat of the category name itself (Geo / graphy) -- to strip.
    Clip-tolerant: each banner word may be a prefix/suffix of a target word."""
    if not _is_caps_banner(s):
        return False
    conts = _cat_continents().get(cat_name)
    if not conts:
        return False
    words = [w for w in _banner_words(s) if len(w) >= 3]
    if not words:
        return False

    def hit(frag, targets):
        return any(t.startswith(frag) or frag.startswith(t)
                   or t.endswith(frag) or frag.endswith(t) for t in targets)

    cat_words = {_norm(w) for w in cat_name.split()} | {_norm(cat_name)}
    cat_words = {t for t in cat_words if len(t) >= 3}
    if all(hit(w, cat_words) for w in words):
        return False                      # a fragment of the category name
    targets: set[str] = set()
    for nm, secs in conts:
        targets |= {_norm(x) for x in nm.split()} | {_norm(nm)}
        for sc in secs:
            targets |= {_norm(x) for x in sc.split()} | {_norm(sc)}
    targets = {t for t in targets if len(t) >= 3}
    return any(hit(w, targets) for w in words)


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
            if cur >= 0 and (_opens(bt, [_norm(openers[cur][0])])
                             or bt in _RH_MISOCR.get(openers[cur][0], ())):
                continue  # running-header repeat of the current major (incl. blackletter mis-OCR)
            if cur >= 0 and len(bt) == 2 and any(
                    _fw(c).startswith(bt) or _fw(c).endswith(bt)
                    for c, _ in _cat_continents().get(openers[cur][0], [])):
                out.append(line)   # a 2-letter gutter-split continent banner half
                continue           # ("AS"|"IA" of ASIA) -- KEEP for band recovery
        if cur >= 0 and _is_subcat_banner(s, openers[cur][0]):
            out.append(line)  # a continent/section banner -- a real subcat, KEEP
            continue
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


# --- Cross-gutter band recovery (Geography & History only) -----------------
# A full-width subcategory banner (CONTINENT -- SECTION) prints across the whole
# spread, so the half-page crop CUTS IT IN TWO: the left page OCRs the head, the
# right page the tail, each clipped.  Reading either half literally fails -- but
# the legal sub-dividers are a small fixed set (the index), so we RECONCILE each
# clipped fragment against it by known order, exactly as the 24 majors reconcile
# against CATEGORIES.  The recovered band then splits BOTH halves at its row:
# everything above it (both pages) precedes it, everything below (both pages)
# follows -- a content-preserving reorder, never a stitch, so no link is dropped
# or moved between buckets.  Scoped to the two categories whose continent/section
# structure actually carries these bands; every other category keeps the plain
# left-then-right zip untouched.
_CROSSING_CATS = frozenset({"Geography", "History"})
_SUBSPINE_CACHE: dict | None = None


def _subdivider_spine(cat: str) -> list[tuple[str, str | None]]:
    """A category's full-width `## ` banner targets, in index order: each
    continent paired with each of its section children (Physical features,
    Countries, ...), or the bare continent when it has none."""
    global _SUBSPINE_CACHE
    if _SUBSPINE_CACHE is None:
        _SUBSPINE_CACHE = {}
        for c, tops in parse_index().items():
            sp: list[tuple[str, str | None]] = []
            for top in tops:
                kids = top.get("children", [])
                # Only a real continent (one with section children) carries a
                # cross-gutter banner.  A childless top-level node (General,
                # Physical features and Oceanography, Meteorology, Biographies)
                # is a plain bucket -- excluded so a body word like "physical"
                # can't collide with its name during reconciliation.
                if kids:
                    sp.extend((top["name"], ch["name"]) for ch in kids)
            _SUBSPINE_CACHE[c] = sp
    return _SUBSPINE_CACHE.get(cat, [])


def _fw(s: str) -> str:
    """First word of a name, normalized."""
    parts = s.split()
    return _norm(parts[0]) if parts else ""


def _fuzz(a: str, b: str) -> bool:
    """Clip-tolerant token match: one a prefix of the other (>=3 chars)."""
    if not a or not b:
        return False
    if len(a) < 3 or len(b) < 3:
        return a == b
    return a.startswith(b) or b.startswith(a)


def _recon_sub(frag: str, spine: list[tuple[str, str | None]],
               cur: int) -> int | None:
    """A clipped `## ` banner fragment -> the spine index it names, or None.
    Splits on the em-dash gutter: head = continent, tail = section.  A continent-
    only fragment naming the CURRENT continent is a running-header repeat (-> cur,
    so the caller sees it as not-new); naming a new continent enters its first
    section.  A section-only tail (continent half clipped off) takes the next
    matching section ahead of the cursor."""
    t = re.sub(r"\(.*?cont.*?\)", "", frag, flags=re.I)
    t = re.sub(r"[#*():,.]", " ", t)
    fwords = [w for w in (_norm(x) for x in t.split()) if len(w) >= 2]
    if not fwords:
        return None

    def cont_hit(name: str) -> bool:
        cw = _fw(name)
        return any(_fuzz(w, cw) for w in fwords)

    def sec_hits(sec: str | None) -> int:
        if not sec:
            return 0
        return sum(1 for x in (_norm(y) for y in sec.split())
                   if len(x) >= 3 and any(_fuzz(w, x) for w in fwords))

    has_cont = any(cont_hit(c) for c, _ in spine)
    has_sec = any(sec_hits(s) for _, s in spine)
    cur_cont = spine[cur][0] if 0 <= cur < len(spine) else None
    if has_cont and not has_sec:                      # continent-only banner
        if cur_cont and cont_hit(cur_cont):
            return cur                                # repeat of current continent
        for j, (c, _) in enumerate(spine):            # entering a new continent
            if cont_hit(c):
                return j
        return None
    if not has_sec:
        return None
    best = best_key = None
    for j, (c, s) in enumerate(spine):                # score section coverage
        sc = sec_hits(s)
        if sc == 0 or (has_cont and not cont_hit(c)):
            continue
        key = (j > cur, sc + (1 if cont_hit(c) else 0), -abs(j - cur))
        if best_key is None or key > best_key:
            best, best_key = j, key
    return best


def _is_crossing_frag(s: str, spine: list[tuple[str, str | None]]) -> bool:
    """True if a `## ` banner is a candidate clipped half of a gutter-crossing
    band (to be paired with its other half).  Only a COMPLETE continent+section
    banner (the whole `CONTINENT -- SECTION` printed on one page) is ruled out; a
    bare continent IS a candidate -- whether it's a clipped head (`EUROPE` with
    its section sliced onto the other page) or History's real bare name "Europe".
    The pairing then decides: a continent banner with an actual tail crosses; one
    with no tail goes unpaired and stays in place, the OCR already ordering it."""
    b = _norm(s.lstrip("#").strip())
    if not b:
        return False
    for cont, sec in spine:
        if sec and b == _norm(cont) + _norm(sec):
            return False
    return True


def _zip_halves(llines: list[str], rlines: list[str],
                spine: list[tuple[str, str | None]], sub_cur: int
                ) -> tuple[list[str], int]:
    """Reorder one spread's two halves around the cross-gutter bands they share.

    A crossing band's banner is sliced by the gutter into a HEAD on A (carrying
    the continent) and a TAIL on B (carrying the section); either half may be
    `## ` or `**`-marked and clipped.  We don't pair by position (brittle when a
    spread stacks several bands or a running-header repeat sits among them) --
    instead, walking the index's KNOWN ORDER from the cursor, for each band the
    index expects next we look for a left head (continent matches, section not
    contradicted) AND a right tail (section matches, continent not contradicted).
    A band found that way is split as one unit: lead(A+B), banner, A-portion +
    B-portion.  Heads with no tail (running-header repeats, one-side banners) and
    everything unmatched stay in place -- the OCR already orders them right."""
    def words(t: str) -> list[str]:
        t = re.sub(r"\(.*?cont.*?\)", "", t, flags=re.I)
        t = re.sub(r"[#*():,.]", " ", t)
        return [w for w in (_norm(x) for x in t.split()) if len(w) >= 2]

    def cont_hit(frag: str, cont: str) -> bool:
        cw = _fw(cont)
        return any(_fuzz(w, cw) for w in words(frag))

    def sec_hit(frag: str, sec: str | None) -> bool:
        sw = [_norm(x) for x in (sec or "").split() if len(_norm(x)) >= 3]
        return bool(sw) and any(_fuzz(w, x) for w in words(frag) for x in sw)

    def has_cont(frag: str) -> bool:
        return any(cont_hit(frag, c) for c, _ in spine)

    _leads = [_fw(s) for _, s in spine if s]

    def unique_sec(sec: str | None) -> bool:
        # a section type that belongs to only ONE continent (e.g. UK's "Division
        # and Towns"); "Physical features"/"Countries" repeat, so a section-only
        # head of those can't be placed without its continent.
        return bool(sec) and _leads.count(_fw(sec)) == 1

    def head_conflicts(frag: str, sec: str | None) -> bool:
        # the head names a section OTHER than `sec` and not `sec` itself
        return any(s and _norm(s) != _norm(sec) and sec_hit(frag, s)
                   for _, s in spine) and not sec_hit(frag, sec)

    def caps_frags(lines: list[str]) -> list[tuple[int, str]]:
        out = []
        for i, l in enumerate(lines):
            s = l.strip()
            if ((s.startswith("## ") or s.startswith("**"))
                    and _is_caps_banner(s) and _is_crossing_frag(s, spine)):
                out.append((i, s))
        return out

    lf, rf = caps_frags(llines), caps_frags(rlines)
    cur = sub_cur
    real: list[tuple[int, int, int]] = []            # (A-row, B-row, spine node)
    usedL: set[int] = set()
    usedR: set[int] = set()
    for j in range(max(cur + 1, 0), len(spine)):
        cont, sec = spine[j]
        if not sec:
            continue
        lh = next((li for li, lt in lf if li not in usedL
                   and (cont_hit(lt, cont) or (sec_hit(lt, sec) and unique_sec(sec)))
                   and not head_conflicts(lt, sec)), None)
        rt = next((ri for ri, rtxt in rf if ri not in usedR and sec_hit(rtxt, sec)
                   and (not has_cont(rtxt) or cont_hit(rtxt, cont))), None)
        if lh is None and rt is None and (j == 0 or spine[j - 1][0] != cont):
            # The continent's OWN name straddles the gutter (e.g. "AS"|"IA" =
            # ASIA): neither half carries it whole, so pair a left fragment that
            # PREFIXES the continent with a right fragment that COMPLETES it.
            # Only at a continent entry (its first band).
            cn = _fw(cont)
            for li, lt in lf:
                if li in usedL:
                    continue
                lw = "".join(words(lt))
                if not lw or lw == cn or not cn.startswith(lw):
                    continue
                ri = next((r for r, rtxt in rf if r not in usedR
                           and lw + "".join(words(rtxt)) == cn), None)
                if ri is not None:
                    lh, rt = li, ri
                    break
        if lh is not None and rt is not None:
            real.append((lh, rt, j))
            usedL.add(lh)
            usedR.add(rt)
            cur = j

    def advance_complete(c: int) -> int:             # one-side banners, no pairing
        for l in list(llines) + list(rlines):
            s = l.strip()
            if s.startswith("## "):
                j = _recon_sub(s, spine, c)
                if j is not None and j > c:
                    c = j
        return c

    if not real:                                     # nothing to interleave
        return list(llines) + list(rlines), advance_complete(sub_cur)

    real.sort(key=lambda r: r[0])

    def carve_at(lines: list[str],
                 realpos: list[int]) -> tuple[list[str], list[list[str]]]:
        realset = set(realpos)
        lead: list[str] = []
        segs: list[list[str]] = []
        seg = lead
        for i, l in enumerate(lines):
            if i in realset:                         # the matched banner opens a
                segs.append([])                      # segment; its line is dropped
                seg = segs[-1]                       # (replaced by the emitted band)
                continue
            seg.append(l)                            # unused one-side banners stay
        return lead, segs                            # so step 3 still reads them

    llead, lsegs = carve_at(llines, [r[0] for r in real])
    rlead, rsegs = carve_at(rlines, [r[1] for r in real])
    out: list[str] = list(llead) + list(rlead)
    for k, (_, _, j) in enumerate(real):
        cont, sec = spine[j]
        # ALL-CAPS so step 3's caps-banner recognizer resolves it and moves its
        # cursor (consumed there, never shown).
        out.append(f"## {cont.upper()} — {sec.upper()}" if sec
                   else f"## {cont.upper()}")
        out.extend(lsegs[k])
        out.extend(rsegs[k])
    return out, cur


def assemble_spread(left_text: str, right_text: str,
                    openers: list[tuple[str, list[str]]],
                    incoming: int, sub_cur: int) -> tuple[str, int, int]:
    """Decruft both halves from the same incoming category, then read the spread
    BAND-BY-BAND at the surviving MAJOR banners.  Within a Geography/History
    band, `_zip_halves` recovers the cross-gutter sub-dividers and reorders the
    two halves above/below them; every other category keeps the plain left-then-
    right zip.  Returns the assembled text, the outgoing major index, and the
    outgoing sub-divider cursor (threaded across spreads of the same category)."""
    llines, lcur = _decruft(left_text.split("\n"), openers, incoming)
    rlines, rcur = _decruft(right_text.split("\n"), openers, incoming)
    left, right = _align_bands(_bands(llines, openers),
                               _bands(rlines, openers), openers)
    cat_norms = {_norm(c): i for i, (c, _) in enumerate(openers)}
    out: list[str] = []
    cat_idx = incoming
    for i in range(max(len(left), len(right))):
        banner = ((left[i][0] if i < len(left) else None)
                  or (right[i][0] if i < len(right) else None))
        if banner:
            out.append(banner)
            nb = cat_norms.get(_norm(banner[3:].strip()))
            if nb is not None and nb != cat_idx:      # a new major -> reset subs
                cat_idx, sub_cur = nb, -1
        ll = left[i][1] if i < len(left) else []
        rl = right[i][1] if i < len(right) else []
        cat_name = openers[cat_idx][0] if 0 <= cat_idx < len(openers) else None
        if cat_name in _CROSSING_CATS:
            zl, sub_cur = _zip_halves(ll, rl, _subdivider_spine(cat_name), sub_cur)
            out.extend(zl)
        else:
            out.extend(ll)
            out.extend(rl)
    return "\n".join(out), max(lcur, rcur), sub_cur


def assemble_sequence(openers: list[tuple[str, list[str]]]
                      ) -> list[tuple[int, int, str]]:
    """The whole list, spread by spread in order -> [(ws, idx, line)].  Each
    spread is BANDED from its whole-spread read and WALKED from its two halves
    (`spread_combine.combine`): the banner is read where it is whole (the spread),
    the columns where they are in order (the halves).  Nothing is reconstructed --
    the band names are read, not rebuilt from slivers.  Downstream the category
    and continent cursors thread continuations across the spread boundaries."""
    from spread_combine import combine
    halves = json.loads(HALVES.read_text(encoding="utf-8")) if HALVES.exists() \
        else {}
    seq: list[tuple[int, int, str]] = []
    for ws in range(WS_START, WS_END + 1):
        h = halves.get(str(ws))
        if not h or not h.get("spread"):
            continue  # every body spread now has all three reads
        text = "\n".join(combine(h["spread"], h["left"], h["right"]))
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


def _header_level(s: str) -> int:
    """A header line's depth: `#`=1, `## `=2, `### `=3; a `**bold**` country
    header sits at sub-section depth (3); anything else (a link, a note) is 0."""
    if s.startswith("### "):
        return 3
    if s.startswith("## "):
        return 2
    if s.startswith("# "):
        return 1
    if s.startswith("**"):
        return 3
    return 0


def build_sections(name: str, line_tuples) -> list[dict]:
    """ONE walk down a category: each subcategory header opens a section, and the
    links (and marginal notes) that follow drop into it, until the next header.
    The category's own `## name` wall is the title, not a section.  Anything
    before the first header (a top-of-category cross-reference) is the lead
    section (header None).  The stream is already clean -- header / link / link
    / header -- so the walk needs no lookahead."""
    lines = [l for _, _, l in line_tuples]
    # Drop the category title wall AND every running-header repeat of it: the
    # whole-spread band read re-emits "## {name}" atop each of the category's
    # pages, and a mixed-case title is not a caps banner, so left in it would be
    # mistaken for a stray section header downstream.
    lines = [l for l in lines
             if not (l.strip().startswith("## ")
                     and _norm(re.sub(r"[#*]", "", l)) == _norm(name))]
    sections: list[dict] = []
    cur = {"header": None, "level": 0, "items": []}
    for l in lines:
        s = l.strip()
        if not s:
            continue
        lvl = _header_level(s)
        if lvl:
            if cur["header"] is not None or cur["items"]:
                sections.append(cur)
            cur = {"header": s, "level": lvl, "items": []}
        else:
            cur["items"].append(s)            # a link or a marginal note
    if cur["header"] is not None or cur["items"]:
        sections.append(cur)
    return sections


def _clean_header(h: str) -> str:
    """A header line -> a plain subsection name: drop the `#`/`**` markers and the
    `*...*` emphasis, collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[*#]+", "", h)).strip()


def _parse_item(s: str):
    """One stream line -> ("note", text) for a marginal cross-reference, or
    ("article", {display, target, emphasized}) for a link.  An italic principal
    (`*Map*`, a section's chief article printed out of alphabetical order) carries
    emphasized=True.  `target` is the link text to resolve to an article later."""
    if _NOTE_RE.match(s):
        return "note", re.sub(r"\*+", "", s).strip()
    emphasized = s.startswith("*") and s.endswith("*") and not s.startswith("**")
    display = re.sub(r"\*+", "", s).strip()
    return "article", {"display": display, "target": display,
                       "emphasized": emphasized}


def _split_header(name: str) -> tuple[str, str | None]:
    """A subsection nests by its NAME, not the model's noisy `##`/`###` level:
    "Country: Section" -> (Country, Section), so "Germany: Subjects" and
    "Germany: Biographies" gather under Germany even when one was stamped `##` and
    the other `###`.  No colon -> a standalone section: (name, None)."""
    if ":" in name:
        parent, child = name.split(":", 1)
        return parent.strip(), child.strip()
    return name, None


def _index_rows() -> list[str]:
    """The index pages, concatenated and split into wikitable rows.  Both pages
    read as one stream so a category whose subtree straddles the 889/890 break
    keeps its running parent context."""
    text = ""
    for ws in INDEX_PAGES:
        p = INDEX_DIR / f"vol29-page{ws:04d}.json"
        if p.exists():
            text += json.loads(p.read_text(encoding="utf-8")).get("raw_text", "")
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.DOTALL)
    return re.split(r"^\|-\s*$", text, flags=re.MULTILINE)


def _index_entries() -> list[tuple[int, str, int]]:
    """Each index row -> (level, name, page), in printed order.  The marker cell
    sets depth: `'''I.'''`=1, `1.`=2, `(''a'')`=3, `(1)`=4; a deeper marker
    co-located in the same row (`1. (''a'')`) wins.  The name is the first cell
    after the marker that isn't a 3-digit page; the page is the trailing 3-digit
    cell.  A row with no marker, no name, or no page is furniture -- skipped."""
    entries: list[tuple[int, str, int]] = []
    for row in _index_rows():
        flat = " ".join(row.split())
        flat = re.sub(r"\{\{ts\|[^}]*\}\}", "", flat)
        flat = re.sub(r"colspan=\d+", "", flat)
        cells = [c.strip() for c in flat.split("|") if c.strip()]
        level, start = 0, -1
        for i, c in enumerate(cells):
            if re.match(r"^(?:''')?[IVXLC]+\.(?:''')?$", c):
                level, start = 1, i + 1
                break
            if re.match(r"^\d+\.$", c):
                level, start = 2, i + 1
                if start < len(cells) and re.match(
                        r"^\((?:'')?[a-z](?:'')?\)$", cells[start]):
                    level, start = 3, start + 1
                elif start < len(cells) and re.match(r"^\(\d+\)$", cells[start]):
                    level, start = 4, start + 1
                break
            if re.match(r"^\((?:'')?[a-z](?:'')?\)$", c):
                level, start = 3, i + 1
                if start < len(cells) and re.match(r"^\(\d+\)$", cells[start]):
                    level, start = 4, start + 1
                break
            if re.match(r"^\(\d+\)$", c):
                level, start = 4, i + 1
                break
        if not level:
            continue
        name = ""
        for j in range(start, len(cells)):
            cj = re.sub(r"'''", "", cells[j]).strip()
            if cj and not re.match(r"^\d{3}$", cj):
                name = cj
                break
        page = 0
        for c in reversed(cells):
            m = re.match(r"^(\d{3})\b", c)
            if m:
                page = int(m.group(1))
                break
        name = re.sub(r"''", "", name).strip()
        name = re.sub(r"\s*\((?:for|see) .*", "", name, flags=re.I).strip()
        name = re.sub(r"\s*\(to \{\{.*", "", name).strip().rstrip(".")
        if name and page:
            entries.append((level, name, page))
    return entries


def parse_index() -> dict[str, list[dict]]:
    """The authoritative skeleton: {category name -> [nested subcat nodes]}.
    A node is {name, printed_page, articles, notes, children}; `_index` marks it
    as index-born (vs body-grafted) for the post-merge invariant check.  Nesting
    follows the marker level via a running parent-at-each-depth map."""
    cats: dict[str, list[dict]] = {}
    subs: list[dict] | None = None
    parent_at: dict[int, dict] = {}
    for level, name, page in _index_entries():
        if level == 1:
            subs = cats.setdefault(name, [])
            parent_at = {}
            continue
        if subs is None:
            continue
        node = {"name": name, "printed_page": page, "articles": [],
                "notes": [], "children": [], "_index": True}
        if level == 2:
            subs.append(node)
        else:
            parent = None
            for pl in range(level - 1, 1, -1):
                if pl in parent_at:
                    parent = parent_at[pl]
                    break
            (parent["children"] if parent else subs).append(node)
        parent_at[level] = node
        for d in [k for k in parent_at if k > level]:
            del parent_at[d]
    # 'Ancient geography' is numbered as the last country in each continent's
    # list, so it lands under Countries; but it spans the whole continent.  Lift
    # it to a continent-level sibling of Countries (fixing the 'goography' typo)
    # -- this matches the printed body's '### Europe: Ancient Geography'.
    for subs in cats.values():
        for continent in subs:
            for container in list(continent.get("children", [])):
                promoted = [k for k in container.get("children", [])
                            if _norm(k["name"]) in
                            ("ancientgeography", "ancientgoography")]
                for node in promoted:
                    container["children"].remove(node)
                    node["name"] = "Ancient geography"
                    continent["children"].append(node)
    # The index labels Law & Political Science's general subcat with the category
    # word "Law"; the body (and sense) call it "General".  Rename so they agree.
    for node in cats.get("Law and Political Science", []):
        if _norm(node["name"]) == "law":
            node["name"] = "General"
            break
    # The index prints the UK's "Division and Towns" singular; it should be plural.
    for cont in cats.get("Geography", []):
        if _norm(cont["name"]).startswith("unitedkingdom"):
            for ch in cont.get("children", []):
                if _norm(ch["name"]) == "divisionandtowns":
                    ch["name"] = "Divisions and Towns"
    return cats


def _items(sec: dict) -> tuple[list, list]:
    """A section's lines -> (article links, cross-reference notes)."""
    arts, notes = [], []
    for it in sec["items"]:
        kind, val = _parse_item(it)
        (notes if kind == "note" else arts).append(val)
    return arts, notes


def _strip_parens(s: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", s).strip()


# Body section names the index spells differently (OCR garble / house style).
# A small CLOSED set -- a known name variation, never a fuzzy guess.
_NAME_VARIANTS = {
    "servia": "serbia",
    "indochinafrench": "indochlnafrench",
    "mediterraneanislandsetc": "mediterraneanislandsc",
    "ancientnames": "ancientgeography",
    "holland": "netherlands",
    "belize": "britishhonduras",
    "australasia": "australia",            # History lists it as Australia
    "divisionsandtowns": "divisionandtowns",
    "churchhistorytocounciloftrent": "churchhistorytothecounciloftrent",
    "classics": "classicalgreekandlatin",
    "finance": "financeandcurrency",
    "critics": "biographiesofcritics",
    "scholars": "classicalscholars",
}

# Section-type leaves the index omits but the body carries: each names a
# physical feature (not a place), so it fills the continent's "Physical
# features" slot -- Miscellaneous included (user-confirmed: it sits there beside
# Lakes / Mountains / Rivers).
_PHYS_TYPES = frozenset({
    "lakes", "mountains", "rivers", "mountainsandhills", "deserts",
    "islands", "miscellaneous", "physicalfeatures",
})


def _index_lookup(skeleton: list[dict]) -> tuple[dict, dict]:
    """For one category's skeleton: {norm name -> [nodes]} and {id(node)->parent}.
    A node registers under its full name, its parens-stripped name, and a
    parent+child compound (so a country resolves within its own continent)."""
    lookup: dict[str, list[dict]] = {}
    parent_map: dict[int, dict | None] = {}

    def reg(name: str, node: dict):
        n = _norm(name)
        if n:
            lookup.setdefault(n, []).append(node)

    def walk(nodes: list[dict], parent: dict | None):
        for n in nodes:
            parent_map[id(n)] = parent
            reg(n["name"], n)
            reg(_strip_parens(n["name"]), n)
            if parent is not None:
                comp = (_norm(_strip_parens(parent["name"]))
                        + _norm(_strip_parens(n["name"])))
                if comp:
                    lookup.setdefault(comp, []).append(n)
            walk(n["children"], n)

    walk(skeleton, None)
    return lookup, parent_map


def _prefer(cands: list[dict], parent_map: dict, cursor: dict | None) -> dict:
    """Among same-named nodes, the one whose parent is on cursor's ancestor chain
    -- keeps a repeated name (General list, a continent's Physical features) in
    the continent we are walking."""
    if len(cands) == 1 or cursor is None:
        return cands[0]
    anc: set[int] = set()
    nd = cursor
    while nd is not None:
        anc.add(id(nd))
        nd = parent_map.get(id(nd))
    for c in cands:
        if id(parent_map.get(id(c))) in anc:
            return c
    return cands[0]


def _resolve(lookup: dict, parent_map: dict, name: str,
             cursor: dict | None) -> dict | None:
    """A body name -> the index node it denotes, absorbing name variations:
    exact, variant alias, parens-stripped, singular/plural."""
    n = _norm(name)
    keys = [n, _NAME_VARIANTS.get(n), _norm(_strip_parens(name)), n + "s"]
    if n.endswith("s") and len(n) > 3:
        keys.append(n[:-1])
    for key in keys:
        if key and key in lookup:
            return _prefer(lookup[key], parent_map, cursor)
    return None


def _match(lookup: dict, parent_map: dict, name: str,
           cursor: dict | None) -> tuple[dict | None, str | None]:
    """A header -> (index node, suffix-to-graft).  The whole name first; then a
    "Parent: Child" split, returning Parent + the Child to build beneath it."""
    hit = _resolve(lookup, parent_map, name, cursor)
    if hit is not None:
        return hit, None
    if ":" in name:
        x, y = (p.strip() for p in name.split(":", 1))
        px = _resolve(lookup, parent_map, x, cursor)
        if px is not None:
            return px, y
    return None, None


def _graft(parent: dict, name: str, parent_map: dict) -> dict:
    """Find or create a child of `parent` named `name`.  Matches on the FULL
    name (parens kept) so Italy's "Towns, etc. (ancient names)" stays distinct
    from "(modern names)" -- the parenthetical is the discriminator, not noise."""
    target = _norm(name)
    for ch in parent["children"]:
        if _norm(ch["name"]) == target:
            return ch
    node = {"name": name, "articles": [], "notes": [], "children": []}
    parent["children"].append(node)
    parent_map[id(node)] = parent
    return node


def _node_path(node: dict, parent_map: dict) -> str:
    parts: list[str] = []
    nd: dict | None = node
    while nd is not None:
        parts.append(nd["name"])
        nd = parent_map.get(id(nd))
    return " > ".join(reversed(parts))


def _phys_slot(cont: dict | None) -> dict | None:
    """The "Physical features" node the index hangs under a continent (or the
    continent itself when it IS the physical-features section).  The index
    answers where Physical Features lives -- we never invent it."""
    if cont is None:
        return None
    for ch in cont.get("children", []):
        if _norm(ch["name"]) == "physicalfeatures":
            return ch
    if _norm(cont["name"]).startswith("physicalfeatures"):
        return cont
    return None


def _resolve_banner(line: str, skeleton: list[dict],
                    cur_cont: dict | None) -> tuple[dict | None, dict | None]:
    """A full-width banner -> (continent node, section node) it names.  A pure
    continent banner (joined norm is a prefix of a continent name) returns just
    the continent; a "Continent-Section" banner returns both; a continent-less
    section fragment (AL FEATURES) takes the continent we are standing in."""
    t = re.sub(r"\(.*?cont.*?\)", "", line, flags=re.I)
    t = re.sub(r"[#*]", "", t).strip()
    parts = [p.strip() for p in re.split(r"[—–\-]", t) if p.strip()]
    joined = _norm(t)
    for s in skeleton:                                  # pure continent banner
        cn = _norm(s["name"])
        if joined and len(joined) >= 3 and cn.startswith(joined):
            return s, None
    cont = None
    if parts:
        cf = _norm(parts[0])
        for s in skeleton:
            cn = _norm(s["name"])
            if cf and len(cf) >= 3 and (cn.startswith(cf) or cn.endswith(cf)):
                cont = s
                break
    use = cont if cont is not None else cur_cont
    sec = None
    if use is not None and parts:
        sf = _norm(parts[-1])
        if len(sf) >= 3:
            for ch in use.get("children", []):
                scn = _norm(ch["name"])
                lead = _norm(ch["name"].split()[0])
                if (scn.startswith(sf) or scn.endswith(sf)
                        or sf.startswith(lead) or lead.startswith(sf)):
                    sec = ch
                    break
    return cont, sec


def _general_child(node: dict) -> dict:
    """The 'general list' descendant a continent's lead content belongs to (BFS),
    else the node itself -- so the run of articles right under a continent banner
    lands on its general list, not piled on the continent node."""
    queue = [node]
    while queue:
        n = queue.pop(0)
        if "general" in _norm(n.get("name", "")):
            return n
        queue.extend(n.get("children", []))
    return node


def _merge_structured(name: str, skeleton: list[dict],
                      sections: list[dict]) -> tuple[dict, list]:
    """Graft the body's flat sections onto the index trunk for one category.

    A KNOWN-ORDER WALK: a full-width banner that ADVANCES the continent/section
    moves the cursor there; a banner that repeats the current one is a running
    header -- the cursor stays put and its trailing content continues the current
    subcat (the same dedup build_toc already does for the 24 major banners).  A
    normal header is a subcat matched into the trunk by NAME (a name match never
    moves the continent -- only banners do), or, when the index never carried it,
    built beneath the current continent (a physical-feature leaf fills that
    continent's Physical features slot).

    INVARIANT: the skeleton's top-level nodes are the ONLY top-level subsections;
    everything is built BENEATH them via _graft, and no item is ever dropped."""
    lookup, parent_map = _index_lookup(skeleton)
    cat = {"name": name, "notes": [], "subsections": skeleton}
    created: list[str] = []

    cur_cont: dict | None = None         # current continent (moved only by banners)
    cur_sec: dict | None = None          # current section within the continent
    phys_home = next(                    # where loose physical-feature leaves land
        (s for s in skeleton if _norm(s["name"]).startswith("physicalfeatures")),
        None)
    cursor: dict | None = None           # last subcat -- holds continuing content

    for sec in sections:
        arts, notes = _items(sec)
        if sec["header"] is None:                 # lead matter heads the cat
            cat["notes"].extend(notes)
            if arts and skeleton:
                skeleton[0]["articles"].extend(arts)
            continue
        raw = sec["header"]
        if _is_caps_banner(raw):                  # a continent/section delimiter
            cont, secnode = _resolve_banner(raw, skeleton, cur_cont)
            if cont is not None and cont is not cur_cont:        # new continent
                cur_cont, cur_sec = cont, secnode
                phys_home = _phys_slot(cont) or phys_home
                cursor = secnode or _general_child(cont)
            elif secnode is not None and secnode is not cur_sec:  # new section
                cur_sec, cursor = secnode, secnode
            # else: a running-header repeat -- cursor unchanged, content continues
            target = cursor or cur_sec or cur_cont or (skeleton[0] if skeleton
                                                       else None)
            if target is not None:
                target["articles"].extend(arts)
                target["notes"].extend(notes)
            continue
        hname = _clean_header(raw)
        node, suffix = _match(lookup, parent_map, hname, cursor)
        if node is not None:
            target = _graft(node, suffix, parent_map) if suffix else node
            cursor = target                       # a NAME match does not move cont
        else:
            if _norm(hname) in _PHYS_TYPES:
                home = phys_home or cur_cont or skeleton[0]
            else:                                 # a place the index missed
                home = cur_cont or skeleton[0]
            target = _graft(home, hname, parent_map)
            cursor = target
            created.append(_node_path(target, parent_map))
        target["articles"].extend(arts)
        target["notes"].extend(notes)

    return cat, created


def _merge_flat(name: str, sections: list[dict]) -> dict:
    """An index-flat category: the body's headers ARE the subcats, a flat list
    (these categories do not nest)."""
    cat = {"name": name, "notes": [], "subsections": []}
    for sec in sections:
        arts, notes = _items(sec)
        if sec["header"] is None:
            cat["notes"].extend(notes)
            if arts:
                cat["subsections"].append(
                    {"name": name, "articles": arts, "notes": [],
                     "children": []})
            continue
        cat["subsections"].append(
            {"name": _clean_header(sec["header"]), "articles": arts,
             "notes": notes, "children": []})
    return cat


def _strip_index_flags(nodes: list[dict]):
    for n in nodes:
        n.pop("_index", None)
        n.pop("printed_page", None)
        _strip_index_flags(n.get("children", []))


def build_classified_toc(tree: list[dict]) -> tuple[dict, list]:
    """Build the nested classified TOC.  A category with an index trunk gets the
    body's sections grafted beneath that trunk by name (the authoritative shape
    plus the body's leaves + links); an index-flat category takes the body's
    headers as a flat subcat list.  Returns (tree, per-cat report of grafted
    nodes -- the sections the index did not already carry)."""
    index = parse_index()
    cats: list[dict] = []
    report: list[tuple[str, list]] = []
    for t in tree:
        skeleton = index.get(t["name"])
        if skeleton:
            cat, created = _merge_structured(t["name"], skeleton, t["sections"])
            report.append((t["name"], created))
        else:
            cat = _merge_flat(t["name"], t["sections"])
        cats.append(cat)
    _strip_index_flags([s for c in cats for s in c["subsections"]])
    return {"categories": cats}, report


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

    tree = [{"name": c, "sections": build_sections(c, ls)} for c, ls in chunks]
    n_sec = sum(len(t["sections"]) for t in tree)
    n_hdr = sum(1 for t in tree for s in t["sections"] if s["header"])
    n_item = sum(len(s["items"]) for t in tree for s in t["sections"])
    body = sum(len(ls) - 1 for _, ls in chunks)  # each chunk's lines minus its wall
    print(f"\ntree: {n_sec:,} sections ({n_hdr:,} headed), {n_item:,} links/notes")
    print(f"every body line placed: {n_hdr + n_item == body}  ({n_hdr + n_item:,}/{body:,})")
    TREE.write_text(json.dumps(tree, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    print(f"wrote {TREE}")

    classified, merge_report = build_classified_toc(tree)
    def _arts(n):
        return len(n["articles"]) + sum(_arts(ch) for ch in n["children"])

    def _notes(n):
        return len(n["notes"]) + sum(_notes(ch) for ch in n["children"])

    cc = classified["categories"]
    n_sub = sum(len(c["subsections"]) for c in cc)
    n_art = sum(_arts(s) for c in cc for s in c["subsections"])
    n_note = sum(len(c["notes"]) for c in cc) + sum(
        _notes(s) for c in cc for s in c["subsections"])
    print(f"\nclassified_toc: {n_sub:,} subsections, {n_art:,} article links, "
          f"{n_note:,} notes")
    print(f"links + notes = items: {n_art + n_note == n_item}  "
          f"({n_art + n_note:,}/{n_item:,})")

    # INVARIANT: a structured category's top-level subcats are EXACTLY the index's
    # -- everything the body adds was grafted beneath, never beside.
    index = parse_index()
    by_name = {c["name"]: c for c in cc}
    bad = []
    for cat, skel in index.items():
        if not skel:
            continue
        want = [_norm(s["name"]) for s in skel]
        got = [_norm(s["name"]) for s in by_name[cat]["subsections"]]
        if want != got:
            bad.append(cat)
    print(f"top-level invariant holds for all structured cats: {not bad}"
          + (f"  VIOLATED: {bad}" if bad else ""))
    grafted = sum(len(c) for _, c in merge_report)
    print(f"grafted {grafted:,} body sections beneath the index trunk")
    CLASSIFIED.write_text(json.dumps(classified, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    print(f"wrote {CLASSIFIED}")


if __name__ == "__main__":
    main()

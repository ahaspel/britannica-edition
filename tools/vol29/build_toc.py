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


_CAT_NORMS = frozenset(_norm(c) for c in CATEGORIES)

# The 40 BANDS, per the source (read off the classified-list pages).  Every major cat
# is one band; ONLY Geography and History carry sub-bands.  These name the Geo/History
# sub-bands so the spread's full-width banners can be told from the buckets that leak
# into it (Oceans, Biographies, Asia: Ancient Names) -- no name-stitching, a lookup.
GEO_BANDS = [
    "Europe Physical Features", "Europe Countries",
    "United Kingdom of Great Britain and Ireland", "Divisions and Towns",
    "Asia Physical Features", "Asia Countries",
    "Africa Physical Features", "Africa Countries",
    "America Physical Features", "America Countries", "America Australasia etc",
]
HIST_BANDS = ["Europe General", "Europe", "Asia", "Africa", "America", "Australasia"]

# A History continent's general run is headerless -- its ONLY marker on the half is
# the continent's own chief article, set whole-italic (`*Asia*`), where the gutter ate
# the "## ASIA" banner.  These norms let _mark_bands read that principal as the band
# opener (Europe excluded: EUROPE--GENERAL keeps its own banner, and *Europe* recurs
# inside it).
_HIST_CONT_NORMS = {_norm(x) for x in ("Asia", "Africa", "America", "Australasia")}

# One band wears two banners: Europe--General and its (cont.) "Europe" are the SAME
# History band (splitting them breaks the General bucket); the UK band runs two lines
# (its "(cont.)" reads as a bare "United Kingdom").  Fold each to one key.
_BAND_ALIASES = {"europegeneral": "europe",
                 "unitedkingdom": "unitedkingdomofgreatbritainandireland"}
_BAND_NORMS = (set(_CAT_NORMS) | {_norm(b) for b in GEO_BANDS}
               | {_norm(b) for b in HIST_BANDS})


def _band_key(s: str) -> str:
    """A banner's canonical band norm: parens/markers off, then fold the two aliased
    banners onto their band.  A norm not in _BAND_NORMS is not a band (a phantom)."""
    nm = _norm(re.sub(r"\(.*?\)", "", s).strip().strip("*"))
    return _BAND_ALIASES.get(nm, nm)


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


_CLA = "classifiedlistofarticles"


def _furniture(s: str) -> bool:
    """The running page-head `CLASSIFIED LIST OF ARTICLES`, with any `[CATEGORY]`
    tag and however the gutter clipped it -- furniture, dropped.  The `[CATEGORY]`
    tag also survives ALONE where the gutter cut the head's text away
    (`GEOGRAPHY]`, `[HISTORY`, `LAW]`): a bracketed all-caps clip of one of the
    24 category names."""
    n = _norm(s.lstrip("#* "))
    if len(n) >= 5 and n in _CLA:
        return True
    if any(_CLA[i:i + 10] in n for i in range(len(_CLA) - 9)):
        return True
    if "[" in s or "]" in s:
        core = s.lstrip("#* ").strip("[]").strip()
        if core.isupper() and len(core) >= 3:
            cn = _norm(core)
            return any(_norm(c).startswith(cn) or _norm(c).endswith(cn)
                       for c in CATEGORIES)
    return False


def band_structure() -> tuple[list[str], list[str], dict[int, list[int]]]:
    """The BANDS -- the full-width divisions -- straight off the `spread` field: a
    separate OCR pass of ONLY the banners that cross the gutter, whole (no fragments to
    stitch).  A spread banner is a band iff its `_band_key` is one of the 40 (majors +
    Geo/History sub-bands); the rest are buckets that leaked into the spread (Oceans,
    Biographies, and -- since no other major cat carries a band -- Denmark, Crime and
    Punishment, ...).  Returns (band walls, their norms, per-page the bands that open)."""
    H = json.loads(HALVES.read_text(encoding="utf-8")) if HALVES.exists() else {}
    name2band: dict[str, int] = {}
    walls: list[str] = []
    norms: list[str] = []
    page_bands: dict[int, list[int]] = {}
    for ws in range(WS_START, WS_END + 1):
        page_bands[ws] = []
        for line in H.get(str(ws), {}).get("spread", "").split("\n"):
            s = line.strip()
            if not s.startswith("## ") or _furniture(s):
                continue
            key = _band_key(s[3:])
            if key not in _BAND_NORMS:           # a bucket that leaked into the spread
                continue
            if key not in name2band:
                name2band[key] = len(walls)
                walls.append("## " + re.sub(r"\(.*?\)", "", s[3:]).strip().strip("*").strip())
                norms.append(key)
            bi = name2band[key]
            if not page_bands[ws] or page_bands[ws][-1] != bi:
                page_bands[ws].append(bi)
    return walls, norms, page_bands


def whole_tracks(norms: list[str]) -> dict[int, list[tuple[bool, str, int]]]:
    """Per page, the whole read's ordered HEADER TRACK -- every band banner and
    bucket header in read order, each tagged with the band it falls under.  A band
    banner (a `## ` whose norm is a known band) advances the open band; every other
    header (a `## ` bucket the gutter did not slice, or a `### `) inherits it.  The
    open band carries ACROSS pages, so a page that continues a band starts under it.
    This track is what marks the halves: a bucket names its band even where the
    band's own banner was lost in the scan."""
    band_id = {nm: i for i, nm in enumerate(norms)}
    tracks: dict[int, list[tuple[bool, str, int]]] = {}
    cur = -1
    for ws in range(WS_START, WS_END + 1):
        tracks[ws] = []
        p = Path(f"data/derived/vol29_whole_{ws}.txt")
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").split("\n"):
            s = line.strip()
            if not s.startswith("#") or _furniture(s) or s[3:].startswith("["):
                continue
            if s.startswith("## ") and not s.startswith("### "):
                nm = _band_key(s[3:])
                if nm in band_id:
                    if band_id[nm] > cur:              # bands only ever advance, so a
                        cur = band_id[nm]              # HIGHER id is a real new band;
                        tracks[ws].append((True, nm, cur))
                    continue                           # a <= id is a running head/(cont.)
                    #                                    -- furniture, never a bucket
            bn = _norm(re.sub(r"\(.*?\)", "", s.lstrip("#* ")))
            tracks[ws].append((False, bn, cur))
    return tracks


def _caps_frag(s: str) -> bool:
    """A dressed, mostly-caps fragment -- how the OCR renders a gutter-clipped
    full-width banner on a half, whatever markup it guessed (`**UNITED KINGDOM
    OF GRE**`, `*PHYSICAL*`, `### UNTRIES (cont.)`)."""
    if not s.startswith(("*", "#")):
        return False
    body = re.sub(r"\(.*?\)", "", re.sub(r"[#*]", "", s)).strip()
    letters = [c for c in body if c.isalpha()]
    return bool(letters) and sum(c.isupper() for c in letters) / len(letters) > 0.7


def _promote_isolated(raw: list[str]) -> list[str]:
    """The source delimits some bucket headers -- the compact country lists -- by a BLANK
    line above AND below, not a `### ` (every `### ` header is blank-isolated too; the OCR
    merely also marked those).  The blank-drop in the band walk would erase that boundary,
    merging the headerless countries into the one above (`Nicaragua` swallowing Panama..
    Chile), so a content line alone between two blanks becomes a `### ` header first."""
    out: list[str] = []
    n = len(raw)

    def run_after(i: int) -> int:
        """Length of the contiguous non-blank run that begins at the next non-blank
        line after i.  A country header is followed by a solid block of towns; a
        merely blank-SEPARATED list (Military terms, a continent's lakes) has a blank
        between every item, so its 'run' is length 1 -- not a header."""
        j = i + 1
        while j < n and not raw[j].strip():
            j += 1
        k = j
        while k < n and raw[k].strip():
            k += 1
        return k - j

    for i, line in enumerate(raw):
        s = line.strip()
        if (s and not s.startswith(("#", "*", "(")) and not _NOTE_RE.match(s)
                and s.count(")") <= s.count("(")          # not a split note/header tail
                and (i == 0 or not raw[i - 1].strip())
                and (i == n - 1 or not raw[i + 1].strip())
                and run_after(i) >= 2):
            out.append("### " + s)
        else:
            out.append(line)
    return out


def _mark_bands(walls, norms, page_bands, H) -> list[tuple[int, int, int, str]]:
    """MARK the bands onto each half by ALIGNING it to the whole read's header order.
    Each half column is a subsequence of that page's whole-read track (its headers, in
    order, each tagged with its band).  Walk the column; for each header find its next
    match forward in the track -- a band banner by clip (it was gutter-sliced), a bucket
    by exact norm -- and take that entry's band; a band banner is consumed, a bucket is
    kept.  A clipped banner is matched by TEXT, not dressing: the OCR renders the
    gutter-cut fragment as `## `, `### `, `**bold**` or `*italic*` unpredictably, so
    any dressed mostly-caps fragment is tried against the track; one that instead
    names the OPEN band (or an earlier one) is that band's running head -- furniture.
    So a band whose own banner dropped on this half is still opened by its first
    bucket, which names the band in the whole read.  The open band carries onto the
    next page.  Returns every half line tagged (band, ws, side, line)."""
    tracks = whole_tracks(norms)
    # A band's clip must also match the banner's FULL text, not only its
    # canonical key: EUROPE--GENERAL keys to "europe" (one band with Europe),
    # so its right-half clip "-GENERAL" can match nothing but the full name.
    fulls = [_norm(re.sub(r"[#*]", "", w)) for w in walls]
    # The History continent bands (europe + Asia/Africa/America/Australasia): a
    # continent principal advances the band ONLY when we already stand in this
    # region, so a Geography `*Asia*` never leaps forward into History.
    hist_ids = {i for i, nm in enumerate(norms)
                if nm in ({"europe"} | _HIST_CONT_NORMS)}
    # Per band, the bucket norms the whole reads gave it -- so a bucket a half
    # column continues at its TOP can be recognized as the carried band's, even
    # where THIS page's whole read never covered that continuation (a band that
    # ends mid-column: Biology's `Biographies` runs off the foot of ws899 into
    # the top of ws900, whose whole read starts fresh at Chemistry).
    band_buckets: dict[int, set[str]] = {}
    for tr in tracks.values():
        for is_band, nm, bd in tr:
            if not is_band:
                band_buckets.setdefault(bd, set()).add(nm)

    def clip_match(clip: str, band: str) -> bool:
        return len(clip) >= 3 and (band.startswith(clip) or band.endswith(clip)
                                   or clip.startswith(band) or clip.endswith(band))

    tagged: list[tuple[int, int, int, str]] = []      # (band, ws, side, line)
    carry = -1
    for ws in range(WS_START, WS_END + 1):
        h = H.get(str(ws))
        if not h:
            continue
        track = tracks.get(ws, [])
        for side, key in enumerate(("left", "right")):
            cur, ptr = carry, 0
            for line in _promote_isolated(h.get(key, "").split("\n")):
                s = line.strip()
                if not s or _furniture(s):
                    continue
                capsish = _caps_frag(s)
                # A whole-italic continent principal opens its History band even where
                # the "## ASIA" banner was lost on this half -- advance to that band by
                # its norm and re-seat the track pointer; keep the line (it is a link).
                if (s.startswith("*") and s.endswith("*") and s.count("*") == 2
                        and _norm(s.strip("*")) in _HIST_CONT_NORMS
                        and cur in hist_ids):
                    tgt = next((i for i, nm in enumerate(norms)
                                if nm == _norm(s.strip("*"))), None)
                    if tgt is not None and tgt > cur:
                        cur = tgt
                        ptr = next((j for j in range(len(track))
                                    if track[j][2] >= tgt), len(track))
                    tagged.append((cur, ws, side, line))
                    continue
                if s.startswith("#") or capsish:
                    banner = (s.startswith("## ") and not s.startswith("### ")) \
                        or capsish
                    clip = _norm(re.sub(r"\(.*?\)", "", s.lstrip("#* ")))
                    # A cont-marked caps fragment naming a band ALREADY OPEN is
                    # that band's running head ("## L FEATURES (*cont.*)" atop a
                    # page whose band carries on).  It must be recognized BEFORE
                    # the forward search: its clip can also suffix-match a LATER
                    # band (…PHYSICAL FEATURES recurs per continent), and a
                    # forward hit there would misband the whole half below it.
                    if (capsish and _CONT_RE.search(s) and len(clip) >= 3
                            and any(clip in norms[b] or clip in fulls[b]
                                    for b in range(cur + 1))):
                        continue
                    # A cont-marked BUCKET at a column top, before this half has
                    # advanced past the band it carried in (cur == carry), that
                    # names a bucket of that carry band: it continues the band
                    # that ran off the previous page's foot, NOT the identically-
                    # named bucket of the NEXT band the forward search would hit
                    # (ws900's Biology `Biographies (cont.)` vs Chemistry's own
                    # `Biographies`).  Fold to carry; leave ptr so the real band
                    # banner below still seats its buckets.
                    if (not banner and _CONT_RE.search(s) and cur == carry
                            and carry >= 0 and clip in band_buckets.get(carry, ())):
                        tagged.append((cur, ws, side, line))
                        continue
                    hit = None
                    for j in range(ptr, len(track)):
                        is_band, nm, bd = track[j]
                        if is_band:
                            # ONLY a real banner (a `## ` line or a gutter-clipped caps
                            # fragment) may match a BAND entry.  A `### Africa: Biographies`
                            # bucket header must NOT be eaten as the AFRICA band just
                            # because its clip starts with the band name -- that drops the
                            # header and merges the bucket into the band's general run.
                            if banner and (clip_match(clip, nm)
                                           or clip_match(clip, fulls[bd])):
                                hit = j
                                break
                        elif nm == clip:
                            hit = j
                            break
                    if hit is not None:
                        cur, ptr = track[hit][2], hit + 1
                        if track[hit][0]:              # a band banner is not content
                            continue
                    elif capsish and len(clip) >= 3 and any(
                            clip in norms[b] or clip in fulls[b]
                            for b in range(cur + 1)):
                        continue          # a running-head repeat of an open/past band
                    elif banner:
                        continue                       # an unmatched banner = furniture
                tagged.append((cur, ws, side, line))
        if page_bands.get(ws):
            carry = page_bands[ws][-1]                 # the page's last band carries on
    return tagged


def band_check(walls, norms, page_bands, H) -> list[tuple[str, str]]:
    """The user's self-check, made exact: the bands are read properly iff the
    half marks agree with the whole-read STRUCTURE (band order + each band's
    start page) on three counts.  The whole read gives structure; the halves
    give content; these are how the two must reconcile.

      1. LEFT and RIGHT halves of a page carry the SAME bands.  A full-width
         banner is centred over the gutter, so it cuts BOTH pages at one height
         -- neither half can hold a band the other lacks.
      2. A page's bands are CONTIGUOUS in band order.  A page spans an unbroken
         run of adjacent bands; a gap (bands 4 and 6 without 5) means a band
         vanished mid-page.
      3. Each band is marked on a CONTIGUOUS page range that BEGINS at the whole
         read's start page for it.  A band appears exactly where its banner is
         and runs unbroken; its tail may SPILL one page past the next band's
         banner (band 4's biographies run onto the page where band 5 opens), and
         that one-page overlap is the only sharing between adjacent bands -- it
         needs no banner, because the whole read fixes the band's start and the
         half supplies the spilled content.

    NB: comparing each half against `{whole-read bands on this page}` is WRONG --
    a carried band that spills onto a page has NO banner there, so it is absent
    from that page's whole-read track though its content (and mark) is present.
    That is a property of the STRUCTURE (the band carries), not a missed mark.
    Returns (scope, detail) violations; empty == the read is sound."""
    tracks = whole_tracks(norms)
    tagged = _mark_bands(walls, norms, page_bands, H)
    start: dict[int, int] = {}
    for ws in range(WS_START, WS_END + 1):
        for _isb, _nm, bd in tracks.get(ws, []):
            start.setdefault(bd, ws)
    half: dict[tuple[int, int], set] = {}
    bandpages: dict[int, set] = {}
    for band, ws, side, _ in tagged:
        half.setdefault((ws, side), set()).add(band)
        bandpages.setdefault(band, set()).add(ws)
    out: list[tuple[str, str]] = []
    for ws in range(WS_START, WS_END + 1):
        l, r = half.get((ws, 0), set()), half.get((ws, 1), set())
        if not l and not r:
            continue
        if l != r:                                   # (1) halves disagree
            out.append((f"ws{ws}", f"left {sorted(l)} != right {sorted(r)}"))
        s = sorted(l | r)
        if s != list(range(s[0], s[-1] + 1)):        # (2) band gap on the page
            out.append((f"ws{ws}", f"bands not contiguous: {s}"))
    for b in sorted(bandpages):                      # (3) each band's page range
        pgs = sorted(bandpages[b])
        if pgs != list(range(pgs[0], pgs[-1] + 1)):
            out.append((f"band {b} {norms[b]}", f"pages not contiguous: {pgs}"))
        elif pgs[0] != start.get(b):
            out.append((f"band {b} {norms[b]}",
                        f"first marked ws{pgs[0]} != whole-read start "
                        f"ws{start.get(b)}"))
    return out


def assemble_sequence(openers) -> list[tuple[int, int, str]]:
    """READ BY BAND.  The whole read MARKS the bands onto each half: a page's band
    sequence (from that page's whole read) is walked down each half, opening a band
    where the half's clipped banner matches the next expected one; the page's last
    band carries onto the next page.  Then a band's two halves reunite: group by band,
    emit in whole-read order, reading order within (page by page, left then right).
    Majors fall out for free -- a major cat is merely a band."""
    walls, norms, page_bands = band_structure()
    H = json.loads(HALVES.read_text(encoding="utf-8")) if HALVES.exists() else {}
    tagged = _mark_bands(walls, norms, page_bands, H)
    by: dict[int, list[tuple[int, int, str]]] = {}
    for band, ws, side, line in tagged:
        by.setdefault(band, []).append((ws, side, line))
    seq: list[tuple[int, int, str]] = []
    idx = 0
    for band in sorted(by):                           # bands in whole-read order
        if band < 0:
            continue
        seq.append((0, idx, walls[band]))
        idx += 1
        for ws, side, line in by[band]:               # reading order within the band
            seq.append((ws, idx, line))
            idx += 1
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


def _principal_of(heading: str, header: str | None) -> bool:
    """A heading line that is really the open bucket's PRINCIPAL link, not a new
    bucket: its words are all drawn from the bucket's own title, so it is a chief
    article named at the section head (`### Painting`, `### Engraving` under
    `## Painting and Engraving: *Subjects*`) -- an emphasized link the source
    prints out of alphabetical order.  A well-set principal is whole-italic
    (`*Geography*`) and reads as a link already; this catches only the ones the
    OCR bolded into a heading, which would otherwise masquerade as a bucket."""
    if not header:
        return False

    def words(t: str) -> set:
        return {w for w in (_norm(x) for x in
                re.split(r"[\s:—–-]+", re.sub(r"[#*]", "", t))) if w}

    hw = words(heading)
    return bool(hw) and hw <= words(header)


def _italic_principal(s: str) -> str | None:
    """A header that is a whole-italic-wrapped link the OCR bolded into a heading
    (`### *Literature*`, `*Map*`) -> its inner text; else None.  A real bucket header
    keeps its NAME un-italic (`### Spain : *Subjects*`), so it is never caught here."""
    t = re.sub(r"^#+\s*", "", s).strip()
    if len(t) > 2 and t.startswith("*") and t.endswith("*") and t.count("*") == 2:
        return t.strip("*").strip()
    return None


def _principal_header(h: str | None) -> bool:
    """A section whose header is a BARE principal (`### *Literature*`) -- the real
    bucket header was missing on the page, so its own chief article stands in.  A
    `(cont.)` naming the real bucket then belongs to it, however differently named."""
    t = re.sub(r"[#\s]+", "", h) if h else ""
    return len(t) > 2 and t.startswith("*") and t.endswith("*") and t.count("*") == 2


# A parenthesized continuation mark -- "(cont.)", "(*cont.*)", the unclosed
# "(cont." -- and nothing else.  The paren is REQUIRED: bare "Cont" inside a
# name ("Modern CONTinental Churches") is not a continuation.
_CONT_RE = re.compile(r"\(\s*\*?\s*cont[^)]*\)?", re.I)


def _base(h: str | None) -> str:
    """A header's bucket-name key: drop the markers and any `(cont.)`, and
    normalize colon spacing and case -- so `General`, `General (cont.)` and
    `General (*cont.*)` are one bucket, and `Finance` prefix-matches `Finance
    and Currency`.  Any OTHER parenthetical is a DISCRIMINATOR and stays:
    `Biographies (ancient)` / `(modern)`, Italy's `Towns, etc. (modern names)` /
    `(ancient names)`, Classics' `Biographies (Greek)` / `(Byzantine)` /
    `(Latin)` are different buckets, not repeats of one."""
    if not h:
        return ""
    h = _CONT_RE.sub("", h)
    h = re.sub(r"[#*]", "", h)
    h = re.sub(r"\s*:\s*", ":", h)
    return re.sub(r"\s+", " ", h).strip().lower()


def build_sections(name: str, line_tuples, general_bucket=None,
                   node_norms=None) -> list[dict]:
    """ONE walk down a category, on ONE rule: recognize the bucket; everything
    else is a link.  A bucket header opens a section; the links that follow drop
    into it until the next bucket.  A header stacked at a bucket's HEAD, before its
    plain run begins, is that bucket's PRINCIPAL -- an emphasized link (chief
    article) the source prints out of order, `### Commerce` under `### General`,
    `### Painting` under `Painting and Engraving` -- not a new bucket.  A `(cont.)`
    of the open bucket folds back in (a bucket's run spans pages/columns).  After a
    caps BAND banner the next header is a bucket, not a principal, unless it echoes
    the banner (its own chief article).  Nothing is dropped: a furniture line the
    walk consumes (a repeated / `(cont.)` header, a split-header tail) lands in its
    section's `absorbed` list, so headers + items + absorbed == every body line."""
    lines = [l for _, _, l in line_tuples]
    # Drop the category title wall AND every running-header repeat of it: the
    # whole-spread band read re-emits "## {name}" atop each of the category's
    # pages, and a mixed-case title is not a caps banner, so left in it would be
    # mistaken for a stray section header downstream.
    lines = [l for l in lines
             if not (l.strip().startswith("## ")
                     and _norm(re.sub(r"[#*]", "", l)) == _norm(name))]
    # An OCR-split header: a header ending in ':' with its tail stacked on the
    # next header line ("### Modern Continental Churches (Reformed):" over
    # "### *Biographies*") is ONE printed header.  Join them at the top line's
    # level; the tail line is carried for the absorbed accounting.
    joined: list[tuple[str, str | None]] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if (_header_level(s) and _CONT_RE.search(s)
                and _header_level(nxt) and _CONT_RE.search(nxt)):
            # A section running head reprinted at a page turn (`Church History to the
            # Council of Trent (cont.`) immediately above a bucket continuation
            # (`Biographies (cont.)`): the first is furniture.  Emit the real
            # continuation; carry the running head as absorbed so it can't wedge the
            # (cont.) away from its base.
            joined.append((nxt, lines[i]))
            i += 2
        elif (_header_level(s) and s.rstrip("*# ").endswith(":")
                and _header_level(nxt)):
            joined.append((s + " " + re.sub(r"^#+\s*", "", nxt), lines[i + 1]))
            i += 2
        else:
            joined.append((s, None))
            i += 1
    sections: list[dict] = []
    cur = {"header": None, "level": 0, "items": [], "absorbed": []}
    run = False                               # has the open bucket's run begun?
    for s, tail in joined:
        if not s:
            continue
        lvl = _header_level(s)
        if lvl:
            ip = _italic_principal(s)
            if ip is not None and node_norms is not None:
                xn = _norm(ip)
                if (general_bucket and xn in general_bucket
                        and _base(cur["header"]) != _base(general_bucket[xn])):
                    if cur["header"] is not None or cur["items"]:
                        sections.append(cur)          # container principal (`### *Asia*`)
                    cur = {"header": general_bucket[xn], "level": 3,   # opens its general
                           "items": [s], "absorbed": []}               # bucket
                    run = True
                    if tail is not None:
                        cur["absorbed"].append(tail)
                    continue
                if xn not in node_norms:
                    cur["items"].append(s)            # names no node -> a chief-article
                    run = True                        # LINK the OCR bolded, not a bucket
                    if tail is not None:
                        cur["absorbed"].append(tail)
                    continue
            if s.count(")") > s.count("("):           # a split-off parenthetical tail
                cur["absorbed"].append(s)             # (`### ature ... countries)`) the OCR
                if tail is not None:                  # dressed as a heading -> a NOTE
                    cur["absorbed"].append(tail)      # fragment, not a bucket; folding it
                continue                              # keeps it from wedging a (cont.) fold
            b, cb = _base(s), _base(cur["header"])
            # A caps banner's ECHO at its head is the banner's own chief article
            # (`### Mahommedan Religion` under `## MAHOMMEDAN RELIGION`) -- a
            # principal link, even though its name repeats the banner's, so it
            # must escape the repeat-fold below or the link is dropped.
            echo = (cur["header"] is not None and not run
                    and _is_caps_banner(cur["header"]) and not _is_caps_banner(s)
                    and not _CONT_RE.search(s)
                    and _principal_of(s, cur["header"]))
            if cur["header"] is not None and not echo and (
                    b == cb                              # the open bucket's own header
                    or (_CONT_RE.search(s) and (         # repeated, or a (cont.) of it:
                        b.startswith(cb) or cb.startswith(b)   # same / abbreviated name,
                        or _principal_header(cur["header"])))):  # or names a bare-principal
                cur["absorbed"].append(s)                # bucket -- keep it open
            elif (cur["header"] is not None and not run and not _is_caps_banner(s)
                    and not _CONT_RE.search(s)           # a continuation is never a
                    and (not _is_caps_banner(cur["header"])   # principal
                         or _principal_of(s, cur["header"]))):
                cur["items"].append(s)        # a PRINCIPAL: an emphasized link at the
            else:                             # bucket head, not a new bucket
                if cur["header"] is not None or cur["items"]:
                    sections.append(cur)      # a real new bucket -- close the open one
                hdr = s
                if general_bucket and _is_caps_banner(s):
                    bn = _norm(re.sub(r"\(.*?\)", "", s.lstrip("#* ")))
                    if bn in general_bucket:   # a bare "## ASIA" banner names the
                        hdr = general_bucket[bn]   # continent's general-subjects run
                cur = {"header": hdr, "level": lvl, "items": [], "absorbed": []}
                run = False
        else:
            xn = (_norm(s.strip("*")) if s.startswith("*") and s.endswith("*")
                  and s.count("*") == 2 else "")
            if (general_bucket and xn in general_bucket
                    and _base(cur["header"]) != _base(general_bucket[xn])):
                # A whole-italic CONTAINER principal (`*Sculpture*`, `*Asia*`) heads a
                # new general-subjects run that carries NO explicit "X: Subjects" banner
                # -- open its bucket, do not fold it into the section above.  (When the
                # banner DID fire, we are already in that bucket, so this is just its
                # first emphasized link -- the _base guard lets it fall through.)
                if cur["header"] is not None or cur["items"]:
                    sections.append(cur)
                cur = {"header": general_bucket[xn], "level": 3,
                       "items": [s], "absorbed": []}
            else:
                cur["items"].append(s)        # a link -- plain, or a within-bucket
            run = True                        # principal; either way the head is past
        if tail is not None:
            cur["absorbed"].append(tail)      # the split-header's consumed 2nd line
    if cur["header"] is not None or cur["items"]:
        sections.append(cur)
    return sections


def _clean_header(h: str) -> str:
    """A header line -> a plain subsection name: drop the `#`/`**` markers and the
    `*...*` emphasis, collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[*#]+", "", h)).strip()


def _parse_item(s: str):
    """One stream line -> ("note", text) for a marginal cross-reference, or
    ("article", {display, target, emphasized}) for a link.  A principal -- a
    section's chief article printed out of alphabetical order -- carries
    emphasized=True, whether the source set it italic (`*Map*`) or the OCR bolded
    it into a heading (`### Painting`); a plain link wears no markup at all.
    `target` is the link text to resolve to an article later."""
    if _NOTE_RE.match(s):
        return "note", re.sub(r"[#*]+", "", s).strip()
    emphasized = s.startswith("#") or (s.startswith("*") and s.endswith("*"))
    display = re.sub(r"[#*]+", "", s).strip()
    return "article", {"display": display, "target": display,
                       "emphasized": emphasized}


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

    walls, norms, page_bands = band_structure()
    H = json.loads(HALVES.read_text(encoding="utf-8")) if HALVES.exists() else {}
    bad = band_check(walls, norms, page_bands, H)
    print(f"\nband self-check (halves agree with whole-read structure): "
          f"{'PASS' if not bad else f'{len(bad)} violations'}")
    for scope, detail in bad:
        print(f"  {scope}: {detail}")

    OUT.write_text(json.dumps(
        [{"name": c, "text": "\n".join(l for _, _, l in ls)} for c, ls in chunks],
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")

    tree = [{"name": c, "sections": build_sections(c, ls)} for c, ls in chunks]
    n_sec = sum(len(t["sections"]) for t in tree)
    n_hdr = sum(1 for t in tree for s in t["sections"] if s["header"])
    n_item = sum(len(s["items"]) for t in tree for s in t["sections"])
    n_abs = sum(len(s["absorbed"]) for t in tree for s in t["sections"])
    body = sum(len(ls) - 1 for _, ls in chunks)  # each chunk's lines minus its wall
    print(f"\ntree: {n_sec:,} sections ({n_hdr:,} headed), {n_item:,} links/notes, "
          f"{n_abs} furniture lines absorbed")
    print(f"every body line placed: {n_hdr + n_item + n_abs == body}  "
          f"({n_hdr + n_item:,} + {n_abs} absorbed / {body:,})")
    TREE.write_text(json.dumps(tree, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    print(f"wrote {TREE}")


if __name__ == "__main__":
    main()

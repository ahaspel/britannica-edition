"""Populate the classified TOC from the human-marked major boundaries.

An earlier generator (now removed) tried to *recover* the 24-category
segmentation by walking the OCR and reconciling clipped banners against a
skeleton -- the deep-trunk failures of that walk are why we hand-marked the
boundaries instead.  This builder keeps the one genuinely good half of it --
the article RESOLVER, lifted here -- and feeds it the marks:

    docs/vol29_major_markup.txt           (the hand-marked boundaries, git-tracked)
  + data/derived/vol29_halves_debug.json  (the half-page OCR, in reading order)
  -> buckets straight from the printed `###`/`##` section headers
  -> each bucket sorted alphabetically (the source's own order)
  -> every article title resolved to its file (the 10-step cascade below)
  -> data/derived/classified_toc.json     (what topics.html renders)

The structure comes from the marks (correct by construction); the order from
the alphabet; the links from the resolver.  No banner-guessing, no skeleton
matching.  This is the SOLE writer of classified_toc.json.
"""
import bisect
import json
import re
import sys
import unicodedata
from pathlib import Path

# The 24 authoritative top-level category names, in printed order.
CATEGORIES = [
    "Anthropology and Ethnology", "Archaeology and Antiquities", "Art",
    "Astronomy", "Biology", "Chemistry", "Economics and Social Science",
    "Education", "Engineering", "Geography", "Geology", "History",
    "Industries, Manufactures and Occupations", "Language and Writing",
    "Law and Political Science", "Literature", "Mathematics", "Medical Science",
    "Military and Naval", "Philosophy and Psychology", "Physics",
    "Religion and Theology", "Sports and Pastimes", "Miscellaneous",
]

ARTICLES_INDEX = Path("data/derived/articles/index.json")
SECTION_INDEX = Path("data/derived/classified_section_index.json")
MARKUP = Path("docs/vol29_major_markup.txt")
HALVES = Path("data/derived/vol29_halves_debug.json")
OUT = Path("data/derived/classified_toc.json")
CAT_TOC_DIR = Path("data/derived/cat_toc")


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _art_norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.upper())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    return " ".join(s.split())


# ── Category-aware disambiguation (Beja-the-town vs Beja-the-tribe) ───────
_GEO_TERMS = {"town", "city", "province", "river", "county", "state",
              "department", "island", "islands", "lake", "mountain", "mountains",
              "bay", "cape", "district", "village", "parish", "canton", "gulf",
              "sea", "strait", "range", "volcano", "peninsula", "region",
              "colony", "kingdom", "republic", "territory", "commune", "port"}
_PLACE_NAMES = {"england", "scotland", "wales", "ireland", "france", "italy",
                "spain", "germany", "russia", "austria", "switzerland", "belgium",
                "holland", "portugal", "greece", "york", "jersey", "carolina",
                "massachusetts", "pennsylvania", "illinois", "ohio", "indiana",
                "kentucky", "missouri", "virginia", "connecticut", "ontario",
                "texas", "michigan", "wisconsin", "iowa", "kansas", "minnesota",
                "maine", "maryland", "georgia", "alabama", "tennessee",
                "louisiana", "mississippi", "arkansas", "oregon", "california",
                "quebec", "columbia", "dakota", "florida", "hampshire", "rhode"}
_PERSON_TERMS = {"poet", "king", "philosopher", "emperor", "painter", "saint",
                 "pope", "bishop", "general", "composer", "sculptor", "architect",
                 "writer", "dramatist", "theologian", "historian", "scholar",
                 "statesman", "queen", "duke", "earl", "baron", "count",
                 "cardinal", "abbot", "martyr", "musician", "novelist", "engineer",
                 "physician", "naturalist", "reformer", "soldier", "admiral",
                 "family", "mathematician", "actor"}
_ETHNIC_TERMS = {"tribe", "people", "peoples", "race"}
_NATURE_TERMS = {"bird", "plant", "fish", "animal", "insect", "genus", "tree",
                 "flower", "mammal", "shrub", "reptile", "mollusc", "fungus"}


def _disambig_domain(dis: str) -> str | None:
    words = set(re.findall(r"[a-z]+", dis.lower()))
    if words & _ETHNIC_TERMS:
        return "ETHNIC"
    if words & _NATURE_TERMS:
        return "NATURE"
    if words & _PERSON_TERMS:
        return "PERSON"
    if words & _GEO_TERMS or words & _PLACE_NAMES:
        return "PLACE"
    return None


def _node_domain(node_name: str, cat_name: str) -> str | None:
    nl = (node_name or "").lower()
    cl = (cat_name or "").lower()
    if "biograph" in nl or nl == "saints" or "scholars" in nl:
        return "PERSON"
    if "tribe" in nl or "races" in nl or "ethnolog" in cl or "anthropolog" in cl:
        return "ETHNIC"
    if cl == "biology" or any(w in nl for w in (
            "birds", "mammals", "fishes", "insects", "plants", "reptiles",
            "batrachians", "molluscs")):
        return "NATURE"
    if cl == "geography" or any(w in nl for w in (
            "town", "division", "river", "mountain", "physical", "countries",
            "general list", "island", "states", "lakes")):
        return "PLACE"
    return None


def load_section_index() -> dict[str, list]:
    """Unique section titles -> [filename, slug, article_title].  Cached;
    built once from the article files' `sections` when missing."""
    if SECTION_INDEX.exists():
        try:
            return json.loads(SECTION_INDEX.read_text(encoding="utf-8"))
        except Exception:
            pass
    from collections import defaultdict
    bucket: dict[str, set] = defaultdict(set)
    for fn in Path("data/derived/articles").glob("*.json"):
        try:
            d = json.loads(fn.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        for s in d.get("sections") or []:
            if isinstance(s, dict) and (s.get("title") or "").strip():
                bucket[_art_norm(s["title"])].add(
                    (fn.name, s.get("slug", ""), d.get("title", "")))
    uniq = {k: list(next(iter(v))) for k, v in bucket.items() if len(v) == 1}
    try:
        SECTION_INDEX.write_text(json.dumps(uniq, ensure_ascii=False),
                                 encoding="utf-8")
    except Exception:
        pass
    return uniq


# ── Resolver indexes (built once from the article index) ──────────────────
def build_resolver():
    article_index = json.loads(ARTICLES_INDEX.read_text(encoding="utf-8"))
    title_lookup: dict[str, tuple[str, str]] = {}
    for e in article_index:
        if e.get("article_type") != "article":
            continue
        n = _art_norm(e["title"])
        if n and n not in title_lookup:
            title_lookup[n] = (e["filename"], e["title"])
    sorted_norms = sorted(title_lookup)

    bio_index: dict[str, list] = {}
    strip_index: dict[str, list] = {}
    sur_by_first: dict[str, set] = {}
    base_dom: dict[str, list] = {}
    for e in article_index:
        if e.get("article_type") != "article":
            continue
        t = e["title"]
        val = (e["filename"], t)
        qm = re.search(r"\(([^)]*)\)\s*$", t)
        b2 = _art_norm(re.sub(r"\s*\([^)]*\)\s*$", "", t))
        if b2:
            base_dom.setdefault(b2, []).append(
                (e["filename"], t, _disambig_domain(qm.group(1) if qm else "")))
        base = re.sub(r"\s*\([^)]*\)\s*$", "", t).strip()
        base = re.split(r"\s+(?:and|or)\s+", base)[0].strip()
        bn = _art_norm(base)
        if bn:
            strip_index.setdefault(bn, []).append(val)
        if "," in t:
            sur, fore = t.split(",", 1)
            sn = _art_norm(sur)
            toks = [w for w in re.split(r"[ .]+", fore) if w]
            bio_index.setdefault(sn, []).append((toks, val))
            if sn:
                sur_by_first.setdefault(sn[:1], set()).add(sn)
    base_by_first: dict[str, list] = {}
    for bn in strip_index:
        base_by_first.setdefault(bn[:1], []).append(bn)

    section_index = load_section_index()

    def _lev_le(a: str, b: str, k: int) -> bool:
        if abs(len(a) - len(b)) > k:
            return False
        prev = list(range(len(b) + 1))
        for i in range(1, len(a) + 1):
            cur = [i]
            for j in range(1, len(b) + 1):
                cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                               prev[j - 1] + (a[i - 1] != b[j - 1])))
            if min(cur) > k:
                return False
            prev = cur
        return prev[-1] <= k

    def _forenames_ok(toc_toks, art_toks) -> bool:
        if len(toc_toks) > len(art_toks):
            return False
        return all(_art_norm(b).startswith(_art_norm(a))
                   for a, b in zip(toc_toks, art_toks))

    def _resolve_extra(raw: str, domain: str | None):
        n = _art_norm(raw)
        if n + "S" in title_lookup:
            return title_lookup[n + "S"]
        if n.endswith("S") and len(n) > 3 and n[:-1] in title_lookup:
            return title_lookup[n[:-1]]
        st = strip_index.get(n)
        if st and len({v[0] for v in st}) == 1:
            return st[0]
        if domain:
            dm = [(fn, t) for fn, t, dd in base_dom.get(n, []) if dd == domain]
            if len(dm) == 1:
                return dm[0]
        if " or " in raw:
            for part in raw.split(" or "):
                pn = _art_norm(part)
                if pn in title_lookup:
                    return title_lookup[pn]
                u = strip_index.get(pn)
                if u and len({v[0] for v in u}) == 1:
                    return u[0]
                if domain:
                    dm = [(fn, t) for fn, t, dd in base_dom.get(pn, [])
                          if dd == domain]
                    if len(dm) == 1:
                        return dm[0]
        if "," in raw:
            sur, fore = raw.split(",", 1)
            sn = _art_norm(sur)
            toks = [w for w in re.split(r"[ .]+", fore) if w]
            cands = [v for tk, v in bio_index.get(sn, [])
                     if _forenames_ok(toks, tk)]
            if len({v[0] for v in cands}) == 1:
                return cands[0]
            same = bio_index.get(sn, [])
            if same:
                fi = _art_norm(toks[0])[:1] if toks else ""

                def _fscore(tk):
                    s = 0
                    for a, b in zip(toks, tk):
                        if _art_norm(b).startswith(_art_norm(a)):
                            s += 1
                        else:
                            break
                    return s
                scored = [(_fscore(tk), v) for tk, v in same
                          if not fi or (tk and _art_norm(tk[0])[:1] == fi)]
                if scored:
                    best = max(s for s, _ in scored)
                    top = [v for s, v in scored if s == best]
                    if len({v[0] for v in top}) == 1:
                        return top[0]
            ocr = [v for cs in sur_by_first.get(sn[:1], ())
                   if cs != sn and _lev_le(sn, cs, 2)
                   for tk, v in bio_index[cs] if _forenames_ok(toks, tk)]
            if len({v[0] for v in ocr}) == 1:
                return ocr[0]
        elif n:
            cands = [bn for bn in base_by_first.get(n[:1], ())
                     if bn != n and abs(len(bn) - len(n)) <= 1
                     and _lev_le(n, bn, 1)]
            if len({v[0] for bn in cands for v in strip_index[bn]}) == 1:
                return strip_index[cands[0]][0]
        return None

    def resolve(raw_name: str, node_dom: str | None, ctx: set):
        """The full 10-step cascade -> article dict (with filename) or an
        unresolved dict (display/target only)."""
        norm = _art_norm(raw_name)
        match = title_lookup.get(norm)
        if not match:
            cleaned = re.sub(r"\s*\(.*\)\s*$", "", raw_name).strip()
            if cleaned != raw_name:
                match = title_lookup.get(_art_norm(cleaned))
        if not match:
            cleaned = re.sub(r"\s*\([^)]*\)", "", raw_name).strip()
            if cleaned != raw_name:
                match = title_lookup.get(_art_norm(cleaned))
        if not match:
            comma = raw_name.split(",", 1)[0].strip()
            if comma != raw_name and len(comma) >= 4:
                match = title_lookup.get(_art_norm(comma))
        if not match and " or " in raw_name:
            match = title_lookup.get(_art_norm(raw_name.split(" or ")[0].strip()))
        if not match:
            first = raw_name.split()[0].rstrip(".,;:") if raw_name else ""
            fn = _art_norm(first)
            if len(fn) >= 4:
                match = title_lookup.get(fn)
        if not match and " " in norm:
            lo = bisect.bisect_left(sorted_norms, norm)
            if lo < len(sorted_norms) and sorted_norms[lo].startswith(norm):
                cand = sorted_norms[lo]
                unique = (lo + 1 >= len(sorted_norms)
                          or not sorted_norms[lo + 1].startswith(norm))
                last_initial = len(norm.rsplit(" ", 1)[-1]) == 1
                token_boundary = (len(cand) > len(norm) and cand[len(norm)] == " ")
                if unique and (last_initial or token_boundary):
                    match = title_lookup[cand]
        if not match:
            match = _resolve_extra(raw_name, node_dom)
        if not match and "#" in raw_name:
            base, anchor = raw_name.split("#", 1)
            bm = title_lookup.get(_art_norm(base))
            if bm:
                filename, base_disp = bm
                return {"target": raw_name, "display": anchor.strip() or base_disp,
                        "filename": filename, "anchor": anchor.strip()}
        if not match:
            si = section_index.get(_art_norm(raw_name))
            if si:
                sfile, sslug, sart = si
                artwords = [w for w in _art_norm(sart).split() if len(w) >= 4]
                if any(w in ctx for w in artwords):
                    return {"target": f"{sart}#{sslug}", "display": sart,
                            "filename": sfile, "anchor": sslug}
        if match:
            filename, display = match
            if display and display[-1].isdigit():
                bare = display.rstrip("0123456789").strip()
                if bare and _art_norm(bare) == _art_norm(raw_name):
                    display = bare
            return {"target": display, "display": display, "filename": filename}
        return {"target": raw_name, "display": raw_name}

    return resolve


# ── Buckets straight from the marks ───────────────────────────────────────
_CONT_KW = ["unitedkingdom", "britain", "asia", "africa", "australasia",
            "america", "oceania", "ocean", "europe"]
_CONT = re.compile(r"\(\s*\*?\s*cont", re.I)
_MARK = re.compile(r"^<<<<\s*(.*?)\s*>>>>\s*$")
_catnorm = {_normalize(c): c for c in CATEGORIES}


def _match_major(name: str):
    n = _normalize(name)
    return _catnorm.get(n) or next(
        (c for c in CATEGORIES
         if n and (_normalize(c).startswith(n) or n.startswith(_normalize(c)))),
        None)


def _is_hdr(s): return s.startswith("## ") or s.startswith("### ") or s.startswith("**")


# A section header the OCR demoted to a plain entry line (no ##/###) after a
# clipped page-banner -- "Russia: *Biographies*", "Rumania: *Subjects and
# Biographies*", "Argentina: *Divisions*", "Chile: *Towns, etc.*".  The
# "Name: <section>" shape is unmistakable; an article entry never carries that
# tail.  History uses Subjects/Biographies; Geography uses Divisions/Towns and
# "Ancient Names" (the index spells it "Ancient geography").
_DEMOTED_HDR = re.compile(
    r"^[^:]{2,60}:\s*\*?(subjects|biographies|divisions|towns|ancient)\b", re.I)


def _is_demoted_hdr(s):
    return (not s.startswith("#") and not s.startswith("**")
            and bool(_DEMOTED_HDR.match(s.replace("*", ""))))


def _hname(s):
    s = re.sub(r"^#+\s*", "", s).replace("*", "")
    s = re.sub(r"\s*\(\s*cont[^)]*\)?", "", s, flags=re.I)   # drop only "(cont.)"
    return s.strip().rstrip(":").strip()
def _continent(s):
    n = _normalize(s)
    return next((k for k in _CONT_KW if n.startswith(k)), None)
def _is_noise(nm, major):
    n = _normalize(nm)
    if len(n) < 2:
        return True
    if len(n) >= 4 and n in "classifiedlistofarticles":
        return True
    mn = _normalize(major)
    return len(n) < len(mn) and (mn.startswith(n) or mn.endswith(n))


def load_segmented_content() -> dict[str, list[str]]:
    """Cut the half-page OCR into the 24 majors at the human <<<< >>>> marks."""
    lines = MARKUP.read_text(encoding="utf-8").split("\n")
    content = {c: [] for c in CATEGORIES}
    cur = None
    for line in lines:
        s = line.strip()
        if s.startswith("#") and not s.startswith("##"):
            continue                       # instruction comment, not an OCR header
        m = _MARK.match(s)
        if m:
            cur = _match_major(m.group(1))
            continue
        if s.startswith("=====") or not s:
            continue
        if cur:
            content[cur].append(line)
    return content


def build_buckets(cat: str, lines: list[str]) -> list[dict]:
    """Ordered buckets for one category, from its printed headers.  A
    continent banner sets the band; a `(cont.)` folds into the prior bucket of
    the same name; OCR banner-fragments (the clipped major name, page furniture)
    are skipped, not made into stray dividers."""
    band = None
    by_key: dict[tuple, dict] = {}
    order: list[dict] = []
    cur_b = None
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if _is_hdr(s) or _is_demoted_hdr(s):
            is_cont = bool(re.search(r"\(\s*\*?\s*cont", s, re.I))
            nm = _hname(s)
            if _is_noise(nm, cat):
                continue
            # A continent band is a `##` full-width banner; a `###` column header
            # is a country (UK, Asia Minor, Africa Ancient) even when its name
            # starts with a continent keyword -- never treat it as a band.
            if s.startswith("## ") and _continent(s):
                band = nm.split(":")[0].strip()
                cur_b = None
                continue
            if not nm:
                continue
            key = (band, _normalize(nm))
            if is_cont:
                if key in by_key:
                    cur_b = by_key[key]      # a continuation rejoins its bucket
                    continue                 # across the gutter,
                if cur_b is not None:
                    continue                 # or the one immediately above it.
            # A fresh header starts its OWN bucket even when the name repeats in
            # another section -- the top-level "General" and Comparative's
            # "General" are two sections, not one, and must not merge.
            cur_b = {"name": nm, "band": band, "arts": [], "pr": [], "notes": []}
            by_key[key] = cur_b
            order.append(cur_b)
        elif s.startswith("("):
            # A cross-reference ("(See NETHERLANDS)") is a real leaf that points
            # elsewhere, not noise -- carry it so an xref leaf (Belgium) is not
            # read as empty.  Other parenthetical annotations stay dropped.
            if cur_b is not None and re.match(r"\(\s*see\b", s, re.I):
                cur_b["notes"].append(s.strip("()").strip())
        else:
            base = s.strip("*").strip()
            if (s.startswith("*") and s.endswith("*")
                    and _normalize(base) in {"europe", "asia", "africa",
                                             "america", "australasia", "australia"}):
                # A continent's general-subjects run is headed only by its name in
                # italic ("*Africa*"), with no "### Africa: General subjects" line;
                # without this its bare entries fold into the previous bucket.
                nm = f"{base}: General subjects"
                key = (band, _normalize(nm))
                if key in by_key:
                    cur_b = by_key[key]
                else:
                    cur_b = {"name": nm, "band": band, "cgen": True,
                             "arts": [], "pr": [], "notes": []}
                    by_key[key] = cur_b
                    order.append(cur_b)
                continue
            if cur_b is None:                # articles directly under a band
                key = (band, "_gen_")
                cur_b = by_key.get(key)
                if cur_b is None:
                    cur_b = {"name": band or "General", "band": band,
                             "arts": [], "pr": [], "notes": []}
                    by_key[key] = cur_b
                    order.append(cur_b)
            (cur_b["pr"] if (s.startswith("*") and s.endswith("*"))
             else cur_b["arts"]).append(
                s.strip("*").strip() if s.startswith("*") else s)
    return order


# ── Pour the buckets into the REVIEWED nested index ───────────────────────
# The structure is `complete_index`'s tree (the one we reviewed, with its full
# nesting: Geography > Europe > Countries > France > Towns).  We do NOT invent a
# flat structure; we drop each bucket's articles onto the index leaf it names.
import complete_index as _C
import build_toc as _BT
from complete_index import _general_kind as _gen_kind


def load_band_read_content() -> dict[str, list]:
    """Per-category line tuples, read straight from the half-pages BY BAND: bands off
    the `spread` field, marked onto each half by aligning it to the whole read
    (build_toc.assemble_sequence) -- no hand-marking.  Replaces load_segmented_content
    and the markup file."""
    openers = _BT.category_openers()
    seq = _BT.assemble_sequence(openers)
    _, chunks = _BT.build_category_chunks(seq, openers)
    return {name: lts for name, lts in chunks}


def _general_bucket_map(nodes) -> dict:
    """{norm(container) -> 'Container: Subjects'} for every index container that owns a
    general-subjects child.  Lets build_sections open (and correctly name) the general
    run a whole-italic principal (`*Sculpture*`, `*Asia*`) or a bare "## ASIA" banner
    heads with no explicit "X: Subjects" header -- so the pour seats it on that child
    instead of the run folding into the section above."""
    m: dict[str, str] = {}

    def walk(ns):
        for n in ns:
            for c in n.get("children", []):
                if _gen_kind(c["name"]) == "subjects":
                    m[_normalize(_BT._strip_parens(n["name"]))] = n["name"] + ": Subjects"
                    break
            walk(n.get("children", []))
    walk(nodes)
    return m


def _node_norms(nodes) -> set:
    """Every index node name (+ its parens-stripped form), normalized -- the set a
    whole-italic heading must hit to be a real bucket; miss it and it is a link."""
    s: set = set()

    def walk(ns):
        for n in ns:
            s.add(_normalize(n["name"]))
            s.add(_normalize(_BT._strip_parens(n["name"])))
            walk(n.get("children", []))
    walk(nodes)
    return s


def _sections_to_buckets(sections: list[dict]) -> tuple[list[dict], list[str]]:
    """A build_toc section -> a pour_category bucket: split each section's items
    into emphasized principals (`pr`), plain articles (`arts`), and notes.
    A headerless, link-free section is NOT a bucket: it is the category's own
    marginal cross-reference, printed under the banner before the first section
    head ("(For ancient anthropology see ARCHAEOLOGY ...)").  Minted as a bucket
    it occupied a positional slot, shifted every later bucket by one, and
    orphaned each category's last bucket (the recurring Biographies orphans).
    Its notes are returned separately, to carry on the category itself."""
    out, cat_notes = [], []
    for sec in sections:
        arts, pr, notes = [], [], []
        for s in sec["items"]:
            kind, val = _BT._parse_item(s)
            if kind == "note":
                notes.append(val)
            elif val["emphasized"]:
                pr.append(val["target"])
            else:
                arts.append(val["target"])
        name = _BT._clean_header(sec["header"]) if sec["header"] else ""
        if not name and not arts and not pr:
            cat_notes.extend(notes)
            continue
        out.append({"name": name, "band": None, "arts": arts,
                    "pr": pr, "notes": notes})
    return out, cat_notes


def _canon(s: str) -> str:
    """Normalize, then reconcile a BODY spelling to its INDEX spelling through the
    one variant table the index-builder uses (Classics->Classical, Critics->
    Biographies of critics, Servia->Serbia ...).  Lets the pour match a header to
    its node when the page and the index spell the same subcat differently."""
    n = _normalize(s)
    return _BT._NAME_VARIANTS.get(n, n)


def _gk(parent: str, name: str) -> str:
    """Leaf key: parent + name, with General/Subjects/Biographies folded so the
    body's 'General' lands on the index's renamed 'Subjects', etc."""
    g = _gen_kind(name)
    return _normalize(parent) + (g if g else _normalize(name))


# Words too generic to prove a leftover bucket *continues* the leaf above it.
_ROLLUP_STOP = {"subjects", "biographies", "general", "towns", "divisions",
                "cont", "list", "articles", "classified", "various", "names",
                "countries", "modern", "ancient", "with", "and", "the", "etc"}


def _sig_words(s: str) -> set[str]:
    """Distinctive (>=4-char, non-generic) words of a header/leaf name."""
    return {w for w in re.sub(r"[^a-z0-9]+", " ", s.lower()).split()
            if len(w) >= 4} - _ROLLUP_STOP


def pour_category(cat: str, nodes: list[dict], buckets: list[dict], resolve):
    """Align the half-read bucket stream to the index, the way a complete index
    permits.  Targets are EVERY node in pre-order, not only leaves: an internal
    node carries its own direct list (a "Minor Arts" general list sits on the
    Minor Arts node, above its Furniture/Biographies children).  ANCHOR on the
    buckets whose header reads cleanly (qualified name equals a node's, in order)
    -- this homes leaves and internal-node lists alike -- then fill each gap BY
    POSITION onto the LEAF nodes only, because containers carry nothing and the
    count must step over them.  A leftover bucket that continues the node just
    placed (a "Painting"/"Engraving" sub-list under "Painting and Engraving:
    Subjects") rolls into it when they share a distinctive word; otherwise it is
    surfaced as an orphan, never folded.  A flat category (no nesting, e.g.
    Sports) pours into one node.  Returns (orphans, empty_leaves)."""
    seq: list[tuple[dict, list]] = []          # every node, pre-order

    def walk(ns, path):
        for n in ns:
            seq.append((n, path))
            walk(n.get("children", []), path + [n])
    walk(nodes, [])

    def _place(node, bs):
        nd = _node_domain(node["name"], cat)
        ctx = set(_art_norm(node["name"] + " " + cat).split())
        prs = [a for b in bs for a in b["pr"]]
        arts = sorted({a for b in bs for a in b["arts"]}, key=_normalize)
        for title, emph in [(a, True) for a in prs] + [(a, False) for a in arts]:
            a = resolve(title, nd, ctx)
            if emph:
                a["emphasized"] = True
            node.setdefault("articles", []).append(a)
        for note in (n for b in bs for n in b.get("notes", [])):
            if note not in node.setdefault("notes", []):
                node["notes"].append(note)

    # Flat category: no nesting at all -> the whole thing is one A-Z list.
    if not seq:
        # No index nodes for this category at all -> an index GAP (e.g. Sports has
        # zero nodes).  Surface its buckets as orphans; do NOT invent a node.
        return list(buckets), []

    def _strip_par(s):
        return re.sub(r"\s*\([^)]*\)", "", s).strip()

    def _bsplit(nm):
        for sep in (":", "?"):          # "?" is a misread colon in OCR'd headers
            if sep in nm:
                par, lf = nm.split(sep, 1)
                return par.strip(), lf.strip()
        return "", nm.strip()

    nkey = [_gk(path[-1]["name"] if path else "", n["name"]) for n, path in seq]
    # paren-stripped alias key, so "Free Churches: Subjects" can reach the node
    # named "Free Churches (British Empire ...) > Subjects" -- used only as a
    # FALLBACK, so a distinguishing paren (Italy "Towns (modern)"/"(ancient)")
    # stays decisive through the exact key above.
    skey = [_gk(_strip_par(path[-1]["name"]) if path else "", _strip_par(n["name"]))
            for n, path in seq]
    is_leaf = [not n.get("children") for n, path in seq]
    nwords = [_sig_words(" ".join([p["name"] for p in path] + [n["name"]]))
              for n, path in seq]

    # A bare entry like "Egypt" never carries its parent ("Africa > Countries"),
    # so it can't match a qualified key -- but a country name is unique, so its
    # own name pins it to one node.
    from collections import Counter
    nbare = [_normalize(_strip_par(n["name"])) for n, path in seq]
    bare_count = Counter(nbare)

    def _bqk(b):
        par, lf = _bsplit(b["name"])
        g = _gen_kind(lf)
        return _canon(par) + (g if g else _canon(lf))

    def _bbare(b):
        return _canon(_strip_par(_bsplit(b["name"])[1]))
    bkeys = [_bqk(b) for b in buckets]
    bbares = [_bbare(b) for b in buckets]

    # 1. Each bucket gets at most one candidate node -- exact qualified key, else
    #    a unique paren-stripped key, else a unique bare name -- then keep the
    #    longest globally CONSISTENT chain (both indices increasing) as anchors.
    #    That is what stops a single out-of-order name (the gutter scramble) from
    #    jumping the pointer and stranding every leaf behind it: the stray one
    #    drops to positional fill, the rest stand.
    by_key: dict[str, list[int]] = {}
    for nj, k in enumerate(nkey):
        by_key.setdefault(k, []).append(nj)
    by_skey: dict[str, list[int]] = {}
    for nj, k in enumerate(skey):
        by_skey.setdefault(k, []).append(nj)
    by_bare: dict[str, list[int]] = {}
    for nj, b in enumerate(nbare):
        by_bare.setdefault(b, []).append(nj)

    # Generic names repeat under every section, so they identify nothing on their
    # own; everything else is specific enough that a single match IS the answer.
    GENERIC = {"subjects", "biographies", "general"}

    # A physical-feature run ("Lakes"/"Rivers"/"Mountains"/"Misc") under a
    # continent banner is placed by its BAND, never by position: the half-read
    # threads continents together, so positional fill would seat it on a
    # neighbour's leaf.  Pull these out of positional fill and continuation (as
    # with cgen); the band router below seats each on its own continent's leaf.
    PHYS = {"lakes", "rivers", "mountains", "miscellaneous"}

    def _is_phys(bi):
        return (bbares[bi] in PHYS
                and bool(_continent(buckets[bi].get("band") or "")))

    # PHASE A -- definitive placement BY NAME, independent of reading order.  A
    # qualified header (carries its parent) or a specific bare name that matches
    # exactly one node is placed there outright -- "Classics: Legendary Figures"
    # read first still lands on "Classical ... > Legendary Figures".  We also note
    # which placements can serve as POSITION boundaries: a qualified header or a
    # section banner (an internal node) fences a region; a bare leaf name may have
    # been read out of order, so it is placed but does not fence anything.
    assign: dict[int, int] = {}
    reserved: set[int] = set()
    bounds: list[tuple[int, int]] = []
    for bi in range(len(buckets)):
        par, _lf = _bsplit(buckets[bi]["name"])
        nj = None
        bound = False
        if par:
            ks = by_key.get(bkeys[bi], [])
            if len(ks) == 1:
                nj = ks[0]
                bound = True
            else:
                sk = by_skey.get(bkeys[bi], [])
                if len(sk) == 1:
                    nj = sk[0]
                    bound = True
        if nj is None and bbares[bi] and bbares[bi] not in GENERIC \
                and bare_count.get(bbares[bi], 0) == 1:
            nj = by_bare[bbares[bi]][0]
            bound = not is_leaf[nj]
        if nj is not None and nj not in reserved:
            assign[bi] = nj
            reserved.add(nj)
            if bound:
                bounds.append((bi, nj))

    # PHASE B -- everything else (generic names, unmatched headers) BY POSITION,
    # into the leaves the definitives left free, fenced by the longest consistent
    # chain of the trustworthy bounds so a generic stays inside its own section.
    import bisect
    tails: list[int] = []
    tails_ci: list[int] = []
    back = [-1] * len(bounds)
    for ci, (bi, nj) in enumerate(bounds):
        p = bisect.bisect_left(tails, nj)
        back[ci] = tails_ci[p - 1] if p > 0 else -1
        if p == len(tails):
            tails.append(nj)
            tails_ci.append(ci)
        else:
            tails[p] = nj
            tails_ci[p] = ci
    backbone: list[tuple[int, int]] = []
    ci = tails_ci[-1] if tails_ci else -1
    while ci != -1:
        backbone.append(bounds[ci])
        ci = back[ci]
    backbone.reverse()
    pb = pn = -1
    for bi, nj in backbone + [(len(buckets), len(seq))]:
        gl = [x for x in range(pn + 1, nj) if is_leaf[x] and x not in reserved]
        gb = [b for b in range(pb + 1, bi)
              if b not in assign and not buckets[b].get("cgen")
              and not _is_phys(b)]
        for bo, lo in zip(gb, gl):
            assign[bo] = lo
        pb, pn = bi, nj

    # continent (first-level node under the category) each placed bucket lives in
    bcont = {bi: (seq[nj][1][0] if seq[nj][1] else None)
             for bi, nj in assign.items()}

    def _band_continent(band):
        # A bucket's own banner band ("## ASIA -- PHYSICAL", clipped to
        # "ASIA?PHYSIC") still names its continent; map it to the top-level node.
        kw = _continent(band or "")
        if not kw:
            return None
        return next((n for n in nodes if _normalize(n["name"]).startswith(kw)),
                    None)

    # PHASE C -- a leftover continuation rolls into the node just placed.
    place: dict[int, list[int]] = {}
    cur = None
    orph_idx = []
    for bi in range(len(buckets)):
        if bi in assign:
            cur = assign[bi]
            place.setdefault(cur, []).append(bi)
        elif cur is not None and not buckets[bi].get("cgen") \
                and not _is_phys(bi) \
                and (_sig_words(buckets[bi]["name"]) & nwords[cur]):
            place.setdefault(cur, []).append(bi)
        elif buckets[bi]["pr"] or buckets[bi]["arts"]:
            # A section the index has no leaf for -> an index GAP.  Surface it as
            # an orphan so the gap is fixed in complete_index.  WE DO NOT GRAFT.
            orph_idx.append(bi)
    for nj, bis in place.items():
        _place(seq[nj][0], [buckets[bi] for bi in bis])
    # A leftover continent-level run (a "## AS"/"## FRICA" banner the gutter
    # clipped past recognition) carries one continent's general subjects.  Route
    # it by the company it keeps -- the continent of its nearest placed neighbour
    # -- onto that continent's empty "General ..." leaf, never reading the banner.
    def _cont_target(cont, bare, allow_general=False):
        # The empty leaf inside `cont` this bare run belongs on: first one named
        # like the run itself ("Lakes" -> Physical features > Lakes).  A
        # continent-general run (cgen) may instead fall back to the continent's
        # "General ..." leaf; a physical-feature run must NOT -- an unmatched
        # "Miscellaneous" is not a "General list".
        if cont is None:
            return None
        queue = list(cont.get("children", []))
        general = None
        while queue:
            nxt = []
            for n in queue:
                if n.get("children"):
                    nxt.extend(n["children"])
                elif not n.get("articles"):
                    nn = _normalize(n["name"])
                    if bare and nn == bare:
                        return n
                    # "general" need not lead the name -- America files its
                    # country list under "Countries, general list".
                    if allow_general and general is None and "general" in nn:
                        general = n
            queue = nxt
        return general

    orphans = []
    for bi in orph_idx:
        cont = None
        for d in range(1, len(buckets)):
            for nb in (bi + d, bi - d):    # following first: a banner precedes its run
                if 0 <= nb < len(buckets) and bcont.get(nb):
                    cont = bcont[nb]
                    break
            if cont:
                break
        cg = bool(buckets[bi].get("cgen"))
        bandc = _band_continent(buckets[bi].get("band"))
        if _is_phys(bi):                 # a physical run trusts its band FIRST
            target = (_cont_target(bandc, bbares[bi], cg)      # (interleaving), but
                      or _cont_target(cont, bbares[bi], cg))   # a British run whose
        else:                            # band-continent is full falls to neighbour
            target = (_cont_target(cont, bbares[bi], cg)
                      or _cont_target(bandc, bbares[bi], cg))
        if target is not None:
            _place(target, [buckets[bi]])
        else:
            orphans.append(buckets[bi])
    empty = [(n, path) for i, (n, path) in enumerate(seq)
             if is_leaf[i] and not n.get("articles") and not n.get("notes")]
    return orphans, empty


def main() -> None:
    print("Building resolver from the article index...")
    resolve = build_resolver()
    content = load_band_read_content()
    print("Loading the reviewed nested index (complete_index)...")
    idx, _ = _C.merge()

    n_arts = n_res = 0
    n_leaves = n_empty = n_orph = 0
    out_cats = []
    for cat in CATEGORIES:
        nodes = idx.get(cat, [])
        sections = _BT.build_sections(cat, content.get(cat, []),
                                      _general_bucket_map(nodes), _node_norms(nodes))
        buckets, cat_notes = _sections_to_buckets(sections)
        orphans, empty = pour_category(cat, nodes, buckets, resolve)
        flat_arts = None
        if not nodes and buckets:
            # A flat major cat is itself a BAND with links directly beneath it (Sports):
            # no sub-node exists to pour into, so its run fills the category node.
            prs = [a for b in buckets for a in b["pr"]]
            plain = sorted({a for b in buckets for a in b["arts"]}, key=_normalize)
            flat_arts = []
            for title, emph in [(a, True) for a in prs] + [(a, False) for a in plain]:
                a = resolve(title, None, set())
                if emph:
                    a["emphasized"] = True
                flat_arts.append(a)
            orphans = []
        n_empty += len(empty)
        n_orph += len(orphans)
        # Per-leaf dedup: one copy of an article within a single leaf.  NOT per
        # category -- the source legitimately lists the same article in two
        # sections (a province under "Divisions" and its capital under "Towns"
        # share one EB article); collapsing across the category gutted every
        # such capital from its Towns leaf.
        def _dedup(ns):
            for n in ns:
                seen: set[str] = set()
                keep = []
                for a in n.get("articles", []):
                    fn = a.get("filename")
                    if fn and fn in seen:
                        continue
                    if fn:
                        seen.add(fn)
                    keep.append(a)
                n["articles"] = keep
                _dedup(n.get("children", []))
        _dedup(nodes)

        def _count(ns):
            nonlocal n_arts, n_res, n_leaves
            for n in ns:
                ch = n.get("children", [])
                if not ch:
                    n_leaves += 1
                for a in n.get("articles", []):
                    n_arts += 1
                    n_res += 1 if a.get("filename") else 0
                _count(ch)
        _count(nodes)
        cat_obj = {"name": cat, "subsections": nodes}
        if flat_arts is not None:
            cat_obj["articles"] = flat_arts
            for a in flat_arts:
                n_arts += 1
                n_res += 1 if a.get("filename") else 0
        if cat_notes:
            cat_obj["notes"] = cat_notes      # the category's own marginal note
        out_cats.append(cat_obj)

    out_obj = {"categories": out_cats}
    try:
        prev = json.loads(OUT.read_text(encoding="utf-8"))
        if prev.get("intro_html"):
            out_obj["intro_html"] = prev["intro_html"]
    except Exception:
        pass

    CAT_TOC_DIR.mkdir(parents=True, exist_ok=True)
    for cat in out_cats:
        slug = re.sub(r"[^a-z0-9]+", "_", cat["name"].lower()).strip("_")
        (CAT_TOC_DIR / f"{slug}.json").write_text(
            json.dumps(cat, ensure_ascii=False), encoding="utf-8")
    OUT.write_text(json.dumps(out_obj, ensure_ascii=False), encoding="utf-8")
    pct = (100 * n_res // n_arts) if n_arts else 0
    print(f"Wrote {OUT}")
    print(f"  24 categories (nested), {n_arts} articles, {n_res} resolved ({pct}%)")
    print(f"  leaves filled {n_leaves - n_empty}/{n_leaves}, "
          f"{n_empty} empty, {n_orph} orphan buckets surfaced")


if __name__ == "__main__":
    main()

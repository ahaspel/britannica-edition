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
_MARK = re.compile(r"^<<<<\s*(.*?)\s*>>>>\s*$")
_catnorm = {_normalize(c): c for c in CATEGORIES}


# A section header the OCR demoted to a plain entry line (no ##/###) after a
# clipped page-banner -- "Russia: *Biographies*", "Rumania: *Subjects and
# Biographies*", "Argentina: *Divisions*", "Chile: *Towns, etc.*".  The
# "Name: <section>" shape is unmistakable; an article entry never carries that
# tail.  History uses Subjects/Biographies; Geography uses Divisions/Towns and
# "Ancient Names" (the index spells it "Ancient geography").
_DEMOTED_HDR = re.compile(
    r"^[^:]{2,60}:\s*\*?(subjects|biographies|divisions|towns|ancient)\b", re.I)


# ── Pour the buckets into the REVIEWED nested index ───────────────────────
# The structure is `complete_index`'s tree (the one we reviewed, with its full
# nesting: Geography > Europe > Countries > France > Towns).  We do NOT invent a
# flat structure; we drop each bucket's articles onto the index leaf it names.
import complete_index as _C
import build_toc as _BT
from complete_index import _general_kind as _gen_kind


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


# Words too generic to prove a leftover bucket *continues* the leaf above it.


def resolve_tree(node: dict, cat: str, resolve) -> None:
    """Resolve every link already sitting on the tree, node by node, in place --
    walking the finished merge (there is no separate pour any more).  Unresolved
    link records ({target, emphasized}) become resolved articles; plain links sort
    A-Z, principals keep their printed order first."""
    raw = node.get("articles", [])
    if raw:
        pr = [d["target"] for d in raw if d.get("emphasized")]
        arts = [d["target"] for d in raw if not d.get("emphasized")]
        nd = _node_domain(node["name"], cat)
        ctx = set(_art_norm(node["name"] + " " + cat).split())
        node["articles"] = []
        for title, emph in ([(a, True) for a in pr]
                            + [(a, False) for a in sorted(set(arts),
                               key=lambda t: (_normalize(t), t))]):   # stable tiebreak
            a = resolve(title, nd, ctx)
            if emph:
                a["emphasized"] = True
            node["articles"].append(a)
    for ch in node.get("children", []):
        resolve_tree(ch, cat, resolve)


def main() -> None:
    print("Building resolver from the article index...")
    resolve = build_resolver()
    print("Loading the completed index (complete_index)...")
    roots = {r["name"]: r for r in _C.index_tree()}

    n_arts = n_res = n_leaves = 0
    out_cats = []
    for cat in CATEGORIES:
        root = roots.get(cat) or {"name": cat, "children": []}
        nodes = root.get("children", [])
        resolve_tree(root, cat, resolve)      # links already seated by the merge; resolve in place

        # Per-leaf dedup: one copy of an article within a single leaf.  NOT per
        # category -- the source legitimately lists the same article in two sections
        # (a province under "Divisions", its capital under "Towns") sharing one EB
        # article; collapsing across the category gutted every such capital.
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
        _dedup([root])

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
        _count([root])

        cat_obj = {"name": cat, "subsections": nodes}
        if root.get("articles"):
            cat_obj["articles"] = root["articles"]   # a flat category's own run (Sports)
        if root.get("notes"):
            cat_obj["notes"] = root["notes"]          # category/band notes carried on the node
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
    print(f"  {n_leaves} leaves total")


if __name__ == "__main__":
    main()

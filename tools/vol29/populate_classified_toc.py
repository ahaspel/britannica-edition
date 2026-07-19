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

from britannica.link_resolver import build_resolver, _art_norm


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
ARTS_DIR = ARTICLES_INDEX.parent
SECTION_INDEX = Path("data/derived/classified_section_index.json")
MARKUP = Path("docs/vol29_major_markup.txt")
HALVES = Path("data/derived/vol29_halves_debug.json")
OUT = Path("data/derived/classified_toc.json")
CAT_TOC_DIR = Path("data/derived/cat_toc")


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())






# ── Wanted-kind from the TOC's own structure ──────────────────────────────
# The article's kind (canton vs city, chemist vs biblical) is read off its
# lead by the shared `lead_kind`; here we say what kind THIS bucket wants.
# The leaf bucket names a place-kind; a Biographies bucket's category names
# the person-field.  Container/region segments never contribute.
_GEO_BUCKET = {
    "divisions": "division", "division": "division", "cantons": "division",
    "states": "division", "provinces": "division", "departments": "division",
    "counties": "division", "governments": "division",
    "towns": "town", "town": "town", "cities": "town",
    "lakes": "lake", "rivers": "river", "mountains": "mountain",
    "islands": "island",
}
_CAT_FIELD = {
    "chemistry": "chemist", "mathematics": "mathematician",
    "music": "musician", "physics": "physicist", "astronomy": "astronomer",
    "geology": "geologist", "philosophy": "philosopher",
    "painting": "painter", "sculpture": "sculptor", "medical": "physician",
    "stage": "actor", "dancing": "actor",
}


_ETHNIC_LEAF = re.compile(r"\b(races?|tribes?|peoples?)\b", re.I)
_NATURE_LEAF = re.compile(
    r"\b(birds?|mammals?|fishes?|insects?|plants?|reptiles?|molluscs?|"
    r"batrachians?|trees?|flowers?)\b", re.I)


def wanted_kinds(path_segments: list[str]) -> tuple[str, ...]:
    """A specific place-kind from the LEAF bucket, a specific person-field
    from the category, or the class token 'PERSON' for a generic Biographies
    bucket.  Empty when the structure gives no kind signal."""
    leaf = path_segments[-1].lower() if path_segments else ""
    if _ETHNIC_LEAF.search(leaf):
        return ("ethnic",)
    if _NATURE_LEAF.search(leaf):
        return ("nature",)
    for w, k in _GEO_BUCKET.items():
        if re.search(r"\b" + w + r"\b", leaf):
            return (k,)
    if "biograph" in leaf:
        joined = " ".join(path_segments).lower()
        for w, f in _CAT_FIELD.items():
            if re.search(r"\b" + w + r"\b", joined):
                return (f,)
        return ("PERSON",)
    return ()






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


# ── Note pointers -> topic nodes (internal cross-refs, NOT articles) ──────────
_NOTE_STOP = {"see", "for", "the", "a", "an", "also", "under", "article", "articles",
              "and", "or", "not", "following", "in", "of", "on", "to", "but", "this",
              "these", "below", "above", "list", "section", "sections"}
_N_CATSECT = re.compile(r"([A-Z][A-Za-z]{2,})\s*,?\s*§+\s*([A-Z][a-zA-Z]+)")
_N_BARESECT = re.compile(r"§+\s*([A-Z][a-zA-Z]+)")
_N_TOKEN = re.compile(r"[A-Z][A-Za-z]{2,}(?:[ ,]+(?:and |or )?[A-Z][A-Za-z]{2,})*")
_N_WORD = re.compile(r"[A-Z][A-Za-z]{2,}")


def build_note_resolver(roots, article_resolve):
    """A note's `See X` / `X § Y` points to a TOPIC NODE (a node in the TOC itself),
    not an article.  Index every node by name -> its path (== the viewer's element id),
    resolve each note's named/§ pointers disambiguated by the note's own category, with an
    article fallback for `see the article X` and no match for prose.  -> resolve_note()."""
    node_by_name: dict[str, list] = {}
    cat_alias: dict[str, str] = {}

    def _index(node, path, cat):
        for ch in node.get("children", []):
            p = path + [ch["name"]]
            node_by_name.setdefault(_art_norm(ch["name"]), []).append((" > ".join(p), cat))
            _index(ch, p, cat)
    for r in roots:
        node_by_name.setdefault(_art_norm(r["name"]), []).append((r["name"], r["name"]))
        cat_alias[_art_norm(r["name"])] = r["name"]
        for w in r["name"].split():
            if len(w) >= 4:
                cat_alias.setdefault(_art_norm(w), r["name"])
        _index(r, [r["name"]], r["name"])
    norms = sorted(node_by_name)

    def _prefer(cands, cat):
        if len(cands) == 1:
            return cands[0][0]                       # unique name -> link even cross-category
        same = [c for c in cands if c[1] == cat]
        return same[0][0] if same else None          # ambiguous, no same-cat -> don't guess

    def _lookup(n, cat):
        if n in node_by_name:
            return _prefer(node_by_name[n], cat)
        if n in cat_alias:
            return cat_alias[n]
        v = _BT._NAME_VARIANTS.get(n.lower())
        if v and _art_norm(v) in node_by_name:
            return _prefer(node_by_name[_art_norm(v)], cat)
        return None

    def _node(t, cat):
        n = _art_norm(t)
        if len(n) < 3:
            return None
        return _lookup(n, cat)          # topic nodes ONLY -- no loose prefix, no article guess

    def _sect(catword, sub, cat):
        catname = cat_alias.get(_art_norm(catword)) or _node(catword, cat)
        if isinstance(catname, str) and not catname.startswith("art:"):
            v = _BT._NAME_VARIANTS.get(sub.lower())
            for cand in [_art_norm(sub)] + ([_art_norm(v)] if v else []):
                if len(cand) < 3:
                    continue
                i = bisect.bisect_left(norms, cand)
                while i < len(norms) and norms[i].startswith(cand):
                    for path, _c in node_by_name[norms[i]]:
                        if path.startswith(catname):
                            return path
                    i += 1
        a = article_resolve(sub, None, set())   # a § section that lives in an article (Palestine)
        return ("art:" + a["filename"]) if a.get("filename") else None

    def resolve_note(note, cat):
        """-> [(start, end, anchor)] for the note's resolvable pointers; [] for prose."""
        spans = []
        for m in _N_CATSECT.finditer(note):                    # X § Y  (section of category X)
            r = _sect(m.group(1), m.group(2), cat)
            if r:
                spans.append((m.start(), m.end(), r))
        for m in _N_BARESECT.finditer(note):                   # bare § Y (of the note's category)
            if any(s <= m.start() < e for s, e, _ in spans):
                continue
            r = _sect(cat, m.group(1), cat)
            if r:
                spans.append((m.start(), m.end(), r))
        for am in re.finditer(r"\bthe\s+articles?\b", note, re.I):  # "see the article(s) X, Y"
            run = re.match(r"\s*[A-Z][A-Za-z]+(?:[, ]+(?:and |or )?[A-Z][A-Za-z]+)*",
                           note[am.end():])           # only the caps run RIGHT AFTER, not to ')'
            if not run:
                continue
            for wm in _N_WORD.finditer(run.group(0)):
                a = article_resolve(wm.group(0), None, set())      # -> the ARTICLE (the exception)
                if a.get("filename"):
                    spans.append((am.end() + wm.start(), am.end() + wm.end(),
                                  "art:" + a["filename"]))
        # the SUBJECT of a "For <subject> see …" clause is not a pointer -- exclude it
        subj = [(m.start(1), m.end(1)) for m in re.finditer(r"\bfor\b(.*?)\bsee\b", note, re.I | re.S)]
        taken = [(s, e) for s, e, _ in spans]
        for m in _N_TOKEN.finditer(note):                      # plain named pointers -> nodes
            parts = [(w.group(0), m.start() + w.start(), m.start() + w.end())
                     for w in _N_WORD.finditer(m.group(0))
                     if w.group(0).lower() not in _NOTE_STOP
                     and not any(s <= m.start() + w.start() < e for s, e in taken)
                     and not any(s <= m.start() + w.start() < e for s, e in subj)]
            i = 0
            while i < len(parts):
                hit = None
                for j in range(len(parts), i, -1):
                    r = _node(" ".join(p[0] for p in parts[i:j]), cat)
                    if r:
                        hit = (parts[i][1], parts[j - 1][2], r, j)
                        break
                if hit:
                    spans.append(hit[:3])
                    i = hit[3]
                else:
                    i += 1
        return sorted(set(spans))

    return resolve_note


def resolve_notes(node: dict, cat: str, resolve_note) -> None:
    """Turn each plain-string note into {text, links:[{start,end,display,anchor}]} in place."""
    if node.get("notes"):
        out = []
        for note in node["notes"]:
            if not isinstance(note, str):
                out.append(note)
                continue
            links = [{"start": s, "end": e, "display": note[s:e], "anchor": a}
                     for s, e, a in resolve_note(note, cat)]
            out.append({"text": note, "links": links})
        node["notes"] = out
    for ch in node.get("children", []):
        resolve_notes(ch, cat, resolve_note)


def resolve_tree(node: dict, cat: str, resolve, path=None) -> None:
    """Resolve every link already sitting on the tree, node by node, in place --
    walking the finished merge (there is no separate pour any more).  Unresolved
    link records ({target, emphasized}) become resolved articles; plain links sort
    A-Z, principals keep their printed order first.  `path` (category root down to
    this node) gives the resolver the bucket context for kind-disambiguation."""
    cur = (path or []) + [node["name"]]
    raw = node.get("articles", [])
    if raw:
        pr = [d["target"] for d in raw if d.get("emphasized")]
        arts = [d["target"] for d in raw if not d.get("emphasized")]
        want = wanted_kinds(cur)
        ctx = set(_art_norm(node["name"] + " " + cat).split())
        node["articles"] = []
        for title, emph in ([(a, True) for a in pr]
                            + [(a, False) for a in sorted(set(arts),
                               key=lambda t: (_normalize(t), t))]):   # stable tiebreak
            a = resolve(title, want, ctx, cur)
            if emph:
                a["emphasized"] = True
            node["articles"].append(a)
    for ch in node.get("children", []):
        resolve_tree(ch, cat, resolve, cur)


def main() -> None:
    print("Building resolver from the article index...")
    resolve = build_resolver()
    print("Loading the completed index (complete_index)...")
    roots = {r["name"]: r for r in _C.index_tree()}
    resolve_note = build_note_resolver(list(roots.values()), resolve)

    n_arts = n_res = n_leaves = 0
    out_cats = []
    for cat in CATEGORIES:
        root = roots.get(cat) or {"name": cat, "children": []}
        nodes = root.get("children", [])
        resolve_tree(root, cat, resolve)      # links already seated by the merge; resolve in place
        resolve_notes(root, cat, resolve_note)   # note pointers -> topic-node anchors, in place

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

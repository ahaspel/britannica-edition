"""Complete the printed index from the whole-spread reads.

parse_index() carries the AUTHORITATIVE trunk (levels 1-3) but stops short of the
leaf sections for the flatter categories.  The whole reads carry every band and
column-section header, whole and in order -- the one thing the half-page reads
cannot give (they shred the full-width banners).  The merge:

    index supplies the trunk  +  whole reads supply the leaves,
    joined on the band name (the easy high-level match).

Pipeline:
  1. skeleton(text)  -- one whole read -> its ordered header events (band/section)
  2. stitch()        -- walk all spreads -> ordered bands per category, the 24
                        pinned by SEQUENCE (a banner only opens the NEXT category;
                        a re-statement of the current category is a running header)
  3. merge()         -- graft each band + its section leaves onto its index node
  4. audit()         -- 24 categories, no 25th, every band placed

stdlib + build_toc only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_toc as B


def whole_path(ws: int) -> Path:
    return Path(f"data/derived/vol29_whole_{ws}.txt")


def skeleton(text: str) -> list[tuple[str, str]]:
    """One whole read -> ordered header events, articles dropped.
    ('band', name) for a `## ` full-width banner; ('section', name) for a `### `
    column header.  Order is the read's order (which the 912 test showed reliable
    for headers even where the article columns between them scramble)."""
    out: list[tuple[str, str]] = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("## "):
            kind, name = "band", s[3:].strip()
        elif s.startswith("### "):
            kind, name = "section", s[4:].strip()
        else:
            continue
        if name.startswith("["):             # a layout annotation, not a header
            continue                          # ("[Left page columns]" on ws895)
        if "classifiedlist" in B._norm(name):  # the page running header, furniture
            continue
        out.append((kind, name))
    return out


def _banner_token(name: str) -> str:
    """A band name -> its category-name token (drop any `: Subjects` / `*..*`
    tail), normalized -- what the sequence-walk matches against the openers."""
    return B._norm(re.sub(r"[*:].*$", "", name))


def _openers() -> list[tuple[str, list[str]]]:
    """In printed order, each category and its own name token.  Unlike
    build_toc's category_openers (which opens Art on its sub-arts because the
    half reads shred the 'Art' banner), the whole read gives a real '## Art', so
    Art opens on its name -- and its sub-arts (Architecture, Music, ...) stay
    sub-bands instead of being read as running-header repeats of the category."""
    return [(c, [B._norm(c)]) for c in B.CATEGORIES]


def stitch() -> dict[str, list[dict]]:
    """All whole reads, in ws order -> {category: [groups]} where a group is
    {'band': name|None, 'sections': [name,...]}.  band=None is the category's
    own leaves before any continent banner (the flat categories).  The 24 are
    pinned by sequence; a running-header repeat of the open category is dropped."""
    openers = _openers()
    cur = -1
    cats: dict[int, list[dict]] = {}

    def group(ci: int, band: str | None, new: bool) -> dict:
        lst = cats.setdefault(ci, [])
        if new or not lst:
            lst.append({"band": band, "sections": []})
        return lst[-1]

    for ws in range(B.WS_START, B.WS_END + 1):
        p = whole_path(ws)
        if not p.exists():
            continue
        for kind, name in skeleton(p.read_text(encoding="utf-8")):
            if kind == "band":
                bt = _banner_token(name)
                nxt = B._advance(bt, openers, cur)
                if nxt is not None:                  # opens the NEXT category
                    cur = nxt
                    cats.setdefault(cur, [])
                    continue                         # the category banner itself
                if cur < 0:
                    continue
                if B._opens(bt, openers[cur][1]):    # re-states current -> running hdr
                    continue
                group(cur, band=name, new=True)      # a continent / section band
            else:                                    # section
                if cur < 0:
                    continue
                group(cur, band=None, new=False)["sections"].append(name)
    return {B.CATEGORIES[i]: cats[i] for i in sorted(cats)}


def _clean_name(name: str) -> str:
    """Drop the OCR's emphasis/continuation furniture from a band/section name,
    leaving the bare header text the resolver matches on."""
    s = re.sub(r"\(\s*\*?\s*cont\.?\s*\*?\s*\)", "", name, flags=re.I)
    s = s.replace("*", "").strip().rstrip(".").strip().strip(":").strip()
    return s


def _general_kind(name: str) -> str | None:
    """The general-section KIND a node label denotes, collapsing the source's
    synonyms for one bucket: `General` / `Subjects` / `General subjects` -> one
    (`subjects`); `Biographies` / `General Biographies` -> one (`biographies`).
    A `General X` of any other X keeps X.  Not a general node -> None."""
    n = B._norm(name)
    if n in ("general", "subjects", "generalsubjects"):
        return "subjects"
    if n in ("biographies", "generalbiographies"):
        return "biographies"
    m = re.match(r"general(.+)", n)
    return m.group(1) if m else None


def _dedup(names: list[str]) -> list[str]:
    """Collapse a `(cont.)` repeat that cleaned down to its original name."""
    out: list[str] = []
    for n in names:
        if not out or B._norm(out[-1]) != B._norm(n):
            out.append(n)
    return out


def _augment_general(skeleton: list[dict], lookup: dict) -> None:
    """Register each general node under `<parent> + kind`, so the page's word
    resolves ONTO it and folds -- the source's two labels for one bucket collapse
    to that node, never a twin.  The index's `General Biographies` answers to
    `Asia: Biographies`; a single `General` answers to `Europe: Subjects`
    (General == Subjects)."""
    def walk(nodes: list[dict], parent: dict | None) -> None:
        for n in nodes:
            k = _general_kind(n["name"])
            if k and parent is not None:
                comp = B._norm(B._strip_parens(parent["name"])) + k
                lookup.setdefault(comp, []).append(n)
            walk(n.get("children", []), n)
    walk(skeleton, None)


def _seat(lookup: dict, parent_map: dict, name: str,
          cursor: dict | None) -> tuple[dict | None, str | None]:
    """Resolve a section to its index node: the self-qualified name first, then
    the name compounded with the cursor's continent -- so a bare `Subjects` under
    the EUROPE band finds `europe`+`subjects` (folding onto `General`), and a
    bare `Biographies` finds its `General Biographies`."""
    node, suffix = B._match(lookup, parent_map, name, cursor)
    if node is not None:
        return node, suffix
    if cursor is not None:
        comp = B._norm(B._strip_parens(cursor["name"])) + B._norm(name)
        if comp in lookup:
            return B._prefer(lookup[comp], parent_map, cursor), None
    return None, None


def _graft_resolved(parent: dict, name: str, parent_map: dict) -> dict:
    """Find the child of `parent` that `name` denotes -- by exact match, variant,
    general-kind, or `X`/`X and Y` prefix -- BEFORE creating one.  Stops a suffix
    or completion from grafting a twin of a node the index already carries under
    a different label (Ancient Names = Ancient geography, States, etc = States,
    a second Biographies = the first)."""
    nn = B._norm(name)
    var = B._NAME_VARIANTS.get(nn)
    kind = _general_kind(name)
    for ch in parent.get("children", []):
        cn = B._norm(ch["name"])
        if not cn:
            continue
        if cn == nn or cn == var or B._NAME_VARIANTS.get(cn) == nn:
            return ch
        if kind and _general_kind(ch["name"]) == kind:
            return ch
        if len(nn) >= 5 and len(cn) >= 5 and (cn.startswith(nn) or nn.startswith(cn)):
            return ch
    return B._graft(parent, name, parent_map)


def _top_ancestor(node: dict, parent_map: dict, skeleton: list[dict]) -> dict | None:
    """The top-level (continent/region) node `node` sits under, or None."""
    tops = {id(s) for s in skeleton}
    nd: dict | None = node
    while nd is not None and id(nd) not in tops:
        nd = parent_map.get(id(nd))
    return nd


def _resolve_band(lookup: dict, parent_map: dict, skeleton: list[dict],
                  name: str, cont: dict | None) -> tuple[dict | None, dict | None]:
    """A band -> (cursor node, its continent).  Tries the exact/compound/variant
    match; then a PREFIX match of the band's head against the top-level nodes
    (`United Kingdom` -> "...of Great Britain and Ireland"; `America—Countries`
    -> America, descending to the section child if the tail names one); then, for
    a sub-band that named no continent (`Divisions and Towns`), resolves it under
    the continent we are standing in."""
    node, suffix = B._match(lookup, parent_map, name, cont)
    if node is not None:
        if suffix:
            node = _graft_resolved(node, suffix, parent_map)
        return node, _top_ancestor(node, parent_map, skeleton)
    parts = re.split(r"\s*[—–:]\s*", name, 1)
    hn = B._norm(parts[0])
    best = None
    if len(hn) >= 4:
        for s in skeleton:
            sn = B._norm(s["name"])
            if sn and (sn == hn or sn.startswith(hn) or hn.startswith(sn)):
                if best is None or len(B._norm(best["name"])) < len(sn):
                    best = s
    if best is not None:
        if len(parts) > 1:
            sec = B._norm(parts[1])
            for ch in best.get("children", []):
                cn = B._norm(ch["name"])
                if sec and (cn.startswith(sec) or sec.startswith(cn)):
                    return ch, best
        return best, best
    if cont is not None:
        node, suffix = _seat(lookup, parent_map, name, cont)
        if node is not None:
            if suffix:
                node = _graft_resolved(node, suffix, parent_map)
            return node, cont
    return None, None


def merge() -> tuple[dict, dict]:
    """Graft the whole-read headers onto the index trunk, category by category.

    Walks each category's bands (the stitch groups): a band resolves to its
    continent/section node and becomes the CURSOR; the band's section headers
    resolve beneath it (the cursor is what gives a bare-prefix `Subjects` its
    continent).  Placement is by NAME, not read order, so the dense-page scramble
    never matters -- a self-qualified name hits its node, a name the index
    stopped short of grafts a child (the completion, e.g. India: Subjects), and
    the index's `General X` nodes answer to the page's bare `X`.  A name that
    resolves nowhere is 'deferred'.

    The lone thing this can't seat is the WORDLESS bare run (a band's lead links
    under no header) -- no name to resolve.  Its home is the band's first general
    child (`General subjects`), already present from the index; the links are
    poured in by step 2 (the half-page reading order)."""
    index = B.parse_index()
    cats = stitch()
    report: dict[str, dict] = {}
    for cat in B.CATEGORIES:
        groups = cats.get(cat, [])
        skeleton = index.get(cat, [])
        if not skeleton:                              # index-flat category
            names = []
            for g in groups:
                if g["band"]:
                    names.append(_clean_name(g["band"]))
                names.extend(_clean_name(s) for s in g["sections"])
            report[cat] = {"flat": True,
                           "sections": _dedup([n for n in names if n])}
            continue
        lookup, parent_map = B._index_lookup(skeleton)
        _augment_general(skeleton, lookup)
        resolved, grafted, deferred = 0, 0, []
        cont = None                  # current continent/region, persists across bands
        for g in groups:
            cursor = None
            if g["band"]:
                bn = _clean_name(g["band"])
                if bn and not bn.startswith("("):
                    node, top = _resolve_band(lookup, parent_map, skeleton, bn, cont)
                    if node is not None:
                        resolved += 1
                        cursor = node
                        if top is not None:
                            cont = top
                    elif cont is not None:        # a region the index omits (Belgium)
                        cursor = _graft_resolved(cont, bn, parent_map)
                        grafted += 1
                    else:
                        deferred.append(bn)
            for s in g["sections"]:
                sn = _clean_name(s)
                if not sn:
                    continue
                home = cursor or cont
                if sn.startswith("("):           # a cross-reference note, not a bucket
                    if home is not None:
                        home.setdefault("notes", []).append(sn)
                    continue
                if (home is not None and _general_kind(sn)
                        and _general_kind(sn) == _general_kind(home["name"])):
                    continue                     # section re-heads its own band
                node, suffix = _seat(lookup, parent_map, sn, home)
                if node is None:
                    # the index stopped short here -> graft below the band (the
                    # completion: Lakes under Physical features, Biographies where
                    # the index drew none).  A bandless section has no home.
                    if home is not None:
                        _graft_resolved(home, sn, parent_map)
                        grafted += 1
                    else:
                        deferred.append(sn)
                    continue
                if suffix:
                    node = _graft_resolved(node, suffix, parent_map)
                    grafted += 1
                else:
                    resolved += 1
                    tail = sn.split(":")[-1].strip()       # keep the page's word
                    if tail and B._norm(node["name"]) != B._norm(tail):
                        node["name"] = tail
        report[cat] = {"flat": False, "resolved": resolved,
                       "grafted": grafted, "deferred": deferred}
    return index, report


def _coverage() -> tuple[list[int], list[int]]:
    have = [ws for ws in range(B.WS_START, B.WS_END + 1) if whole_path(ws).exists()]
    missing = [ws for ws in range(B.WS_START, B.WS_END + 1) if not whole_path(ws).exists()]
    return have, missing


def _asc(s: str) -> str:
    return s.encode("ascii", "replace").decode()


def main() -> None:
    have, missing = _coverage()
    print(f"whole reads present: {len(have)}/{B.WS_END - B.WS_START + 1}")
    if missing:
        print(f"missing: {missing[:12]}{' ...' if len(missing) > 12 else ''}")

    if "--skeleton" in sys.argv:                      # parser check, per spread
        for ws in have:
            print(f"\n=== ws{ws} ===")
            for kind, name in skeleton(whole_path(ws).read_text(encoding="utf-8")):
                print(("  ## " if kind == "band" else "       ### ") + _asc(name))
        return

    if "--stitch" in sys.argv:                         # raw band sequence per cat
        for cat, groups in stitch().items():
            print(f"\n## {_asc(cat)}")
            for g in groups:
                if g["band"]:
                    print(f"   [{_asc(g['band'])}]")
                for sec in g["sections"]:
                    print(f"      - {_asc(sec)}")
        return

    # default: merge audit -- what the whole reads add to the index trunk
    _, report = merge()
    placed = deferred = 0
    for cat in B.CATEGORIES:
        r = report.get(cat)
        if r is None:
            continue
        if r["flat"]:
            print(f"\n## {_asc(cat)}  [index-flat] {len(r['sections'])} body sections")
            for s in r["sections"]:
                print(f"      - {_asc(s)}")
            continue
        d = r["deferred"]
        placed += r["resolved"] + r["grafted"]
        deferred += len(d)
        print(f"\n## {_asc(cat)}  resolved={r['resolved']} "
              f"grafted={r['grafted']} deferred={len(d)}")
        for nm in d:
            print(f"      ? {_asc(nm)}")
    print(f"\nTOTAL across rich categories: placed={placed} deferred={deferred}")


if __name__ == "__main__":
    main()

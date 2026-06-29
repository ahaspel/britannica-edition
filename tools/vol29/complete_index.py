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

import json
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


_HALVES: dict | None = None


def _half_headers(ws: int) -> set:
    """The column headers the HALF reads give for this spread, normalized.  The
    halves are the authority for which `###` are real: they don't shred a column
    header, and they keep an emphasized link as *italic* rather than a header.
    They mark a header in ANY of three styles -- `### Spain : *Subjects*` (left
    page), bold `**Switzerland :** *Subjects*` (right page), or over-levelled to
    `## Sculpture: *Subjects*` -- so read all three, or a header is silently missed
    and its section falsely dropped."""
    global _HALVES
    if _HALVES is None:
        _HALVES = json.loads(Path(
            "data/derived/vol29_halves_debug.json").read_text(encoding="utf-8"))
    h = _HALVES.get(str(ws), {})
    out = set()
    for side in ("left", "right"):
        for line in h.get(side, "").split("\n"):
            s = line.strip()
            if s.startswith("### "):
                hdr = s[4:]
            elif s.startswith("## "):
                hdr = s[3:]
            elif s.startswith("**"):
                hdr = s
            else:
                continue
            nm = B._norm(_clean_name(hdr.replace("*", "")))
            if nm:
                out.add(nm)
    return out


def reconciled_skeleton(ws: int) -> list[tuple[str, str]]:
    """The whole read's band/section headers -- the band STRUCTURE only, NEVER the
    links.  The dense six-column page scrambles entries across bucket boundaries, so
    buckets and their links are read from the half pages, not here.  `##` bands are
    kept (the halves shred them); a `###` is kept only when the halves confirm it as
    a real header, matched bare or band-qualified -- phantoms (Theatre, a stray
    Subjects) drop out."""
    confirmed = _half_headers(ws)
    out: list[tuple[str, str]] = []
    band = ""
    in_lead = False               # standing in a band's lead, before its first section
    lead_done = False
    for line in whole_path(ws).read_text(encoding="utf-8").split("\n"):
        s = line.strip()
        if s.startswith("## "):
            name = s[3:].strip()
            if not name.startswith("[") and "classifiedlist" not in B._norm(name):
                band = name
                out.append(("band", name))
                in_lead, lead_done = True, False
        elif s.startswith("### "):
            name = s[4:].strip()
            if name.startswith("["):
                continue
            # the whole read writes a section bare ("Subjects") under its band; the
            # half may qualify it ("Sculpture: Subjects"), so confirm either form.
            bare = B._norm(_clean_name(name))
            qual = B._norm(_clean_name(band) + " " + _clean_name(name))
            if bare in confirmed or qual in confirmed:
                out.append(("section", name))
                in_lead = False
        elif s and not s.startswith("#") and not s.startswith("="):
            # an article line in the lead region means the band carries its own bare
            # run -> a filled bucket in its own right (the "Minor Arts" case).  Emit
            # the FACT, not the scrambled links (those must never enter the index).
            if in_lead and not lead_done and band:
                out.append(("lead", band))
                lead_done = True
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
    """All whole reads, in ws order -> {category: [groups]}.  A group is
    {'band': name|None, 'lead': [links], 'notes': [...], 'sections': [section]}
    and a section is {'name', 'links': [...], 'notes': [...]}.  A link/note lands
    in the open section, or in the band's `lead` if no section has opened yet (the
    wordless run).  band=None is the category's own leaves before any continent
    banner (the flat categories).  The 24 are pinned by sequence; a running-header
    repeat of the open category is dropped."""
    openers = _openers()
    cur = -1
    cats: dict[int, list[dict]] = {}

    def group(ci: int, band: str | None, new: bool) -> dict:
        lst = cats.setdefault(ci, [])
        if new or not lst:
            lst.append({"band": band, "lead": [], "notes": [], "sections": [],
                        "lead_present": False})
        return lst[-1]

    def attach(ci: int, kind: str, text: str) -> None:
        if ci < 0:
            return
        g = group(ci, band=None, new=False)
        if g["sections"]:
            g["sections"][-1]["links" if kind == "link" else "notes"].append(text)
        else:
            g["lead" if kind == "link" else "notes"].append(text)

    for ws in range(B.WS_START, B.WS_END + 1):
        if not whole_path(ws).exists():
            continue
        for kind, name in reconciled_skeleton(ws):
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
            elif kind == "section":
                if cur < 0:
                    continue
                group(cur, band=None, new=False)["sections"].append(
                    {"name": name, "links": [], "notes": []})
            elif kind == "lead":                     # the band's bare run is non-empty
                if cur >= 0:
                    group(cur, band=None, new=False)["lead_present"] = True
            else:                                    # link / note
                attach(cur, kind, name)
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


def _general_child(node: dict) -> dict | None:
    """The band's general-subjects child -- where a wordless lead run belongs."""
    for c in node.get("children", []):
        if _general_kind(c["name"]) == "subjects":
            return c
    return None


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


def _descendant_by_norm(root: dict, target: str) -> dict | None:
    """Nearest node in root's subtree whose name normalizes to `target` (BFS) --
    lets a reconciliation target sit a level below the matched parent."""
    queue = list(root.get("children", []))
    while queue:
        nxt: list[dict] = []
        for n in queue:
            if B._norm(n["name"]) == target:
                return n
            nxt.extend(n.get("children", []))
        queue = nxt
    return None


def _descendant_by_prefix(root: dict, nn: str) -> dict | None:
    """The longest descendant whose name is a near-prefix of `nn` (within a few
    characters) -- so a grafted section "Britain and Ireland: Ancient Names"
    finds the existing "Britain and Ireland, ancient" leaf one level down instead
    of forking a fresh top-level twin."""
    best = None
    queue = list(root.get("children", []))
    while queue:
        nxt: list[dict] = []
        for n in queue:
            cn = B._norm(n["name"])
            if (len(cn) >= 12 and (nn.startswith(cn) or cn.startswith(nn))
                    and abs(len(nn) - len(cn)) <= 6):
                if best is None or len(B._norm(best["name"])) < len(cn):
                    best = n
            nxt.extend(n.get("children", []))
        queue = nxt
    return best


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
    if var:                                  # the variant may name a node nested
        d = _descendant_by_norm(parent, var)  # a level below (Scholars -> Bio-
        if d is not None:                     # graphies > Classical scholars)
            return d
    d = _descendant_by_prefix(parent, nn)    # a long section name that merely
    if d is not None:                        # extends an existing leaf IS that leaf
        return d
    return B._graft(parent, name, parent_map)


def _top_ancestor(node: dict, parent_map: dict, skeleton: list[dict]) -> dict | None:
    """The top-level (continent/region) node `node` sits under, or None."""
    tops = {id(s) for s in skeleton}
    nd: dict | None = node
    while nd is not None and id(nd) not in tops:
        nd = parent_map.get(id(nd))
    return nd


def _resolve_band(lookup: dict, parent_map: dict, skeleton: list[dict],
                  name: str, cont: dict | None
                  ) -> tuple[dict | None, dict | None, dict | None]:
    """A band -> (cursor node, its continent, anchor).  `anchor` is the band's own
    entity before a `: Section` tail, so a sibling band the index omits grafts
    beside it (Belgium beside Balkan Peninsula), not under it.
    Tries the exact/compound/variant
    match; then a PREFIX match of the band's head against the top-level nodes
    (`United Kingdom` -> "...of Great Britain and Ireland"; `America—Countries`
    -> America, descending to the section child if the tail names one); then, for
    a sub-band that named no continent (`Divisions and Towns`), resolves it under
    the continent we are standing in."""
    node, suffix = B._match(lookup, parent_map, name, cont)
    if node is not None:
        anchor = node                       # the band's entity, before a section tail
        if suffix:
            node = _graft_resolved(node, suffix, parent_map)
        return node, _top_ancestor(node, parent_map, skeleton), anchor
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
                    return ch, best, best
        return best, best, best
    if cont is not None:
        node, suffix = _seat(lookup, parent_map, name, cont)
        if node is not None:
            anchor = node
            if suffix:
                node = _graft_resolved(node, suffix, parent_map)
            return node, cont, anchor
    return None, None, None


def _build_flat(groups: list[dict]) -> list[dict]:
    """An index-flat category has no trunk -- the body's headers ARE its
    structure.  The `##`/`###` level is unreliable, so flatten band+sections into
    one stream and nest only on an explicit `Parent: Child` (Philosophy and
    Psychology: Subjects), deduping `(cont.)` repeats and pouring each header's
    links into its node."""
    roots: list[dict] = []

    def add(name: str, siblings: list[dict]) -> dict | None:
        nm = _clean_name(name)
        if not nm or nm.startswith("("):
            return None
        n = B._norm(nm)
        for ch in siblings:
            if B._norm(ch["name"]) == n:
                return ch
        node = {"name": nm, "articles": [], "notes": [], "children": []}
        siblings.append(node)
        return node

    def place(name: str, links: list, notes: list) -> dict | None:
        nm = _clean_name(name)
        if not nm or nm.startswith("("):
            return None
        if ":" in nm:                                # explicit Parent: Child -> nest
            x, y = (p.strip() for p in nm.split(":", 1))
            px = add(x, roots)
            node = add(y, px["children"]) if px is not None else None
        else:
            node = add(nm, roots)
        if node is not None:
            node["articles"].extend(links)
            node["notes"].extend(notes)
        return node

    for g in groups:
        if g["band"]:
            node = place(g["band"], g["lead"], g["notes"])
            if node is not None and g.get("lead_present"):
                node["lead_filled"] = True           # the band's own bare run = a bucket
        for sec in g["sections"]:
            place(sec["name"], sec["links"], sec["notes"])
    return roots


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
        if not skeleton:                              # index-flat: body IS the structure
            index[cat] = _build_flat(groups)
            report[cat] = {"flat": True,
                           "sections": [n["name"] for n in index[cat]]}
            continue
        lookup, parent_map = B._index_lookup(skeleton)
        _augment_general(skeleton, lookup)
        resolved, grafted, deferred = 0, 0, []
        cont = None                  # current continent (top-level), persists across bands
        region = None                # the level the current sibling-bands live at
        for g in groups:
            cursor = None
            if g["band"]:
                bn = _clean_name(g["band"])
                if bn and not bn.startswith("("):
                    node, top, anchor = _resolve_band(lookup, parent_map, skeleton, bn, cont)
                    if node is not None:
                        resolved += 1
                        cursor = node
                        region = parent_map.get(id(node)) or node
                        # an index-omitted sibling country (Belgium) must graft BESIDE
                        # its country, not under it -- but ONLY when that country sits
                        # directly under its continent, so a sub-section (Islands) still
                        # grafts under its country (Scotland), not floated above it:
                        rt = _top_ancestor(anchor, parent_map, skeleton)
                        if anchor is not node and rt is not None \
                                and parent_map.get(id(anchor)) is rt:
                            region = rt
                        if top is not None:
                            cont = top
                    else:                          # a region the index omits: graft it
                        home = region or cont      # BESIDE its siblings (Islands under
                        if home is not None:       # Scotland, Malay Peninsula under Countries)
                            cursor = _graft_resolved(home, bn, parent_map)
                            grafted += 1
                        else:
                            deferred.append(bn)
            if cursor is not None:           # the band's wordless lead run pours into
                home = _general_child(cursor) or cursor         # its general-subjects
                home.setdefault("articles", []).extend(g["lead"])   # child (else band)
                if g.get("lead_present"):    # a real bare run -> a filled bucket of its
                    home["lead_filled"] = True                  # own (the Minor Arts case)
                cursor.setdefault("notes", []).extend(g["notes"])
            grp_region = None                # a finer parent a "Region: X" section sets
            for s in g["sections"]:
                sn = _clean_name(s["name"])
                if not sn:
                    continue
                home = grp_region or cursor or cont
                if sn.startswith("("):           # a cross-reference note, not a bucket
                    if home is not None:
                        home.setdefault("notes", []).append(sn)
                    continue
                if (home is not None and _general_kind(sn)
                        and _general_kind(sn) == _general_kind(home["name"])):
                    home.setdefault("articles", []).extend(s["links"])   # section re-
                    home.setdefault("notes", []).extend(s["notes"])      # heads its band
                    continue
                node, suffix = _seat(lookup, parent_map, sn, home)
                if node is None:
                    # the index stopped short here -> graft below the band (the
                    # completion: Lakes under Physical features, Biographies where
                    # the index drew none).  A bandless section has no home.
                    if home is None:
                        deferred.append(sn)
                        continue
                    node = _graft_resolved(home, sn, parent_map)
                    grafted += 1
                elif suffix:
                    grp_region = node            # "Ireland: Divisions" -> Ireland, so a
                    node = _graft_resolved(node, suffix, parent_map)  # bare "Islands" next
                    grafted += 1                 # seats under Ireland, not the UK band
                else:
                    resolved += 1
                    k = _general_kind(node["name"])        # ONLY a general node is renamed,
                    tail = sn.split(":")[-1].strip()       # to the page's plain word -- so
                    if k in ("subjects", "biographies") and \
                            _general_kind(B._strip_parens(tail)) == k:
                        node["name"] = k.capitalize()      # never a misspelling (Bird), and
                        m = re.search(r"\(([^)]+)\)", tail)  # never swallowing a note
                        if m:
                            node.setdefault("notes", []).append("(" + m.group(1) + ")")
                node.setdefault("articles", []).extend(s["links"])
                node.setdefault("notes", []).extend(s["notes"])
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

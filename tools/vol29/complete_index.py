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


def _band_slices(lts, cat):
    """Split a category's band-read line tuples into (band_name, buffer) at the
    page-0 band openers -- the same band segmentation the builder walks."""
    catn = B._norm(cat)
    out, band, buf = [], None, []
    for t in lts:
        if str(t[0]) == "0":
            nm = re.sub(r"[#*]", "", t[-1]).strip()
            if B._norm(nm) == catn:
                continue
            if buf:
                out.append((band, buf))
            band, buf = nm, []
        else:
            buf.append(t)
    if buf:
        out.append((band, buf))
    return out


def _general_map(nodes: list[dict]) -> dict:
    """{norm(container) -> 'Container: Subjects'} so build_sections opens a general
    run onto its node -- the same map the builder passes."""
    m: dict[str, str] = {}

    def walk(ns):
        for n in ns:
            for c in n.get("children", []):
                if _general_kind(c["name"]) == "subjects":
                    m[B._norm(B._strip_parens(n["name"]))] = n["name"] + ": Subjects"
                    break
            walk(n.get("children", []))
    walk(nodes)
    return m


def _node_norms(nodes: list[dict]) -> set:
    """Every index node name (+ parens-stripped), normalized -- lets build_sections
    tell a real bucket header from an emphasized link."""
    s: set = set()

    def walk(ns):
        for n in ns:
            s.add(B._norm(n["name"]))
            s.add(B._norm(B._strip_parens(n["name"])))
            walk(n.get("children", []))
    walk(nodes)
    return s


def stitch() -> dict[str, list[dict]]:
    """{category: [groups]}, read BY BAND off the HALF-page reads -- the buckets in
    proper order, each carrying its LINKS and notes.  A group is {'band', 'lead',
    'notes', 'sections'}; a section is {'name', 'links', 'notes'}.  This is the read
    tree the merge grafts onto the printed index; the
    halves already order the buckets, so nothing here reorders or marks anything."""
    content = B.band_read_content()
    trunk = B.parse_index()
    _, norms, _ = B.band_structure()
    _, band_notes = B.whole_tracks(norms)          # the whole read's band-notes, uncut
    cats: dict[str, list[dict]] = {}
    for cat in B.CATEGORIES:
        ct = trunk.get(cat, [])
        gb, nn = _general_map(ct), _node_norms(ct)
        groups: list[dict] = []
        for band, buf in _band_slices(content.get(cat, []), cat):
            g = {"band": band, "lead": [], "notes": [], "sections": []}
            for sec in B.build_sections(cat, buf, gb, nn):
                links, secnotes = [], []
                for it in sec["items"]:
                    kind, val = B._parse_item(it)
                    (secnotes if kind == "note" else links).append(val)
                name = B._clean_header(sec["header"]) if sec["header"] else ""
                if not name:
                    g["lead"].extend(links)          # a band's headerless run (the whole
                    #                                  read carries its sheared notes)
                else:
                    g["sections"].append({"name": name, "links": links,
                                          "notes": secnotes})
            groups.append(g)
        # hang the WHOLE read's band-notes on each band node, minus any a bucket already
        # carries as a finer column note (the bucket's copy wins).
        col = {n for g in groups for s in g["sections"] for n in s["notes"]}
        for g in groups:
            key = B._norm(g["band"]) if g["band"] else B._norm(cat)
            g["notes"] = [n for n in band_notes.get(key, []) if n not in col]
        cats[cat] = groups
    return cats


_XREF_NOTE = re.compile(r"\(\s*\*?\s*[^)]*?(?:\bsee\b|§)[^)]*\)", re.I)


def _clean_name(name: str) -> str:
    """Drop the OCR's emphasis/continuation furniture from a band/section name,
    leaving the bare header text the resolver matches on.  A cross-reference note
    baked into a header -- `Biographies (see also § Saints)` -- is a NOTE, not part of
    the name; strip it so the bucket matches its own `(cont.)` continuation.  Only a
    `see`/`§` parenthetical goes; a real discriminator (`(Greek)`, `(U.S.A.)`) stays."""
    s = re.sub(r"\(\s*\*?\s*cont\.?\s*\*?\s*\)", "", name, flags=re.I)
    s = _XREF_NOTE.sub("", s)
    s = s.replace("*", "").strip().rstrip(".").strip().strip(":").strip()
    return s


def _general_kind(name: str) -> str | None:
    """The general-section KIND a node label denotes, collapsing the source's
    synonyms for one bucket: `General` / `Subjects` / `General subjects` /
    `General list` (Geography's country-band catch-all) -> one (`subjects`);
    `Biographies` / `General Biographies` -> one (`biographies`).
    A `General X` of any OTHER X keeps X.  Not a general node -> None."""
    n = B._norm(name)
    if n in ("general", "subjects", "generalsubjects", "generallist"):
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


_GENERAL_ALIASES = {                             # the page's interchangeable general
    "subjects": ("general", "subjects", "generalsubjects"),   # labels -- one kind each
    "biographies": ("biographies", "generalbiographies"),
}


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
            elif k:                              # a TOP-LEVEL general node has no parent
                for syn in _GENERAL_ALIASES.get(k, (k,)):   # to compound; the page's
                    if syn != B._norm(n["name"]):           # General / Subjects / General
                        lookup.setdefault(syn, []).append(n)  # Subjects all fold onto it
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
            # `Biographies (Greek)` prefix-matches the `Biographies` container -- but its
            # (Greek) discriminator names an actual child; descend so the band's run lands
            # on `Greek`, leaving the container the empty grouping the body says it is.
            if nn.startswith(cn):
                m = re.search(r"\(([^)]+)\)", name)
                if m:
                    gc = next((c for c in ch.get("children", [])
                               if B._norm(c["name"]) == B._norm(m.group(1))), None)
                    if gc is not None:
                        return gc
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
            place(g["band"], g["lead"], g["notes"])
        for sec in g["sections"]:
            place(sec["name"], sec["links"], sec["notes"])
    return roots


_GRAFT_TRACE = None                              # diagnostic: collect grafted (unresolved) sections


def _is_descendant(node: dict, anc: dict, parent_map: dict) -> bool:
    """True if `node` sits under `anc` in the (possibly grafted) index tree."""
    n = node
    while n is not None:
        if id(n) == id(anc):
            return True
        n = parent_map.get(id(n))
    return False


def _child_of(node: dict, home: dict, parent_map: dict) -> dict | None:
    """Walk up from `node` to the direct child of `home` (None if not under it) --
    the reading-order predecessor a fresh graft should slot in behind."""
    n = node
    while n is not None:
        par = parent_map.get(id(n))
        if par is home:
            return n
        n = par
    return None


# NAMED EXCEPTION -- the lexical concession in an otherwise structural merge.  History
# prints "Belgium" and "Holland" as their own "(see NETHERLANDS)" cross-ref headings, each
# a bare banner right after some country's "X: Subjects" bucket -- structurally identical to
# a sub-section (only the word tells us it is a country), so no structural rule can tell
# either from `Islands`.  A bare graft named here is seated on the continent beside its
# siblings, not adopted into the open region.  Grow it only under the same proof.
_BARE_SIBLING_EXCEPTION = {"belgium", "holland"}


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
        hits: dict = {}              # id(node) -> [node, {bucket names}]; >1 == a collision
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
                        hits.setdefault(id(cursor), [cursor, set()])[1].add(B._norm(bn))
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
                cursor.setdefault("notes", []).extend(g["notes"])
            grp_region = None                # a finer parent a "Region: X" section sets
            prev = None                      # previous section's node -> reading-order graft
            for s in g["sections"]:
                _xm = _XREF_NOTE.search(s["name"])      # a (see …) baked into the header is a
                xnote = _xm.group(0).replace("*", "").strip() if _xm else None  # note, not a name
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
                    if B._norm(sn) in _BARE_SIBLING_EXCEPTION and cont is not None:
                        home = cont          # named exception: a bare country the source
                        #  prints like a sub-section -> seat it beside its siblings on the
                        #  continent, not under the open region (see _BARE_SIBLING_EXCEPTION)
                    # the index stopped short here -> graft below the band (the
                    # completion: Lakes under Physical features, Biographies where
                    # the index drew none).  A bandless section has no home.
                    if home is None:
                        deferred.append(sn)
                        continue
                    if _GRAFT_TRACE is not None:
                        _GRAFT_TRACE.append((cat, cursor["name"] if cursor else None,
                                             home["name"], sn, ":" in s["name"], bool(s["links"])))
                    node = _graft_resolved(home, sn, parent_map)
                    grafted += 1
                    kids = home.get("children", [])
                    if prev is not None and kids and kids[-1] is node:
                        # a graft appends, but the trunk children are pre-placed in index
                        # order -- slot it right after its reading-order predecessor, so
                        # Malay Peninsula follows Malay Archipelago, not the last country
                        anchor = _child_of(prev, home, parent_map)
                        if anchor is not None:
                            ai = next((i for i, c in enumerate(kids) if c is anchor), None)
                            if ai is not None and ai < len(kids) - 1:
                                kids.pop()                 # the just-appended graft ...
                                kids.insert(ai + 1, node)  # ... re-slotted into reading order
                elif suffix:
                    grp_region = node            # "Ireland: Divisions" -> Ireland, so a
                    node = _graft_resolved(node, suffix, parent_map)  # bare "Islands" next
                    grafted += 1                 # seats under Ireland, not the UK band
                else:
                    resolved += 1
                    if grp_region is not None and not _is_descendant(node, grp_region, parent_map):
                        grp_region = None      # resolved a FRESH sibling -> we've left the
                        #  last X:Y's sub-region; a later bare graft belongs on the cursor,
                        #  not adopted into a stale country (Malay Peninsula, not under India)
                    k = _general_kind(node["name"])        # ONLY a general node is renamed,
                    tail = sn.split(":")[-1].strip()       # to the page's plain word -- so
                    if k in ("subjects", "biographies") and \
                            _general_kind(B._strip_parens(tail)) == k:
                        node["name"] = k.capitalize()      # never a misspelling (Bird), and
                        m = re.search(r"\(([^)]+)\)", tail)  # never swallowing a note
                        if m:
                            node.setdefault("notes", []).append("(" + m.group(1) + ")")
                if any(c.isalpha() for c in sn) and sn == sn.upper():
                    grp_region = node            # a caps CONTAINER header (JUDAISM, BIBLE...) sets
                    # the nesting context, so its bare children graft under it -- as a qualified
                    # `X: Y` already does.  The trunk still wins for a known sibling (a country).
                hits.setdefault(id(node), [node, set()])[1].add(B._norm(sn))
                node.setdefault("articles", []).extend(s["links"])
                node.setdefault("notes", []).extend(s["notes"])
                if xnote:
                    node["notes"].append(xnote)
                prev = node
        collisions = [(nd["name"], sorted(names))
                      for _id, (nd, names) in hits.items() if len(names) > 1]
        report[cat] = {"flat": False, "resolved": resolved, "grafted": grafted,
                       "deferred": deferred, "collisions": collisions}
    return index, report


def index_tree() -> list[dict]:
    """The index as ONE uniform tree of nodes: the 24 categories are its top row.  A
    flat category that is nothing but a wordless bare run (Sports) carries that run on
    the category node itself."""
    idx, _ = merge()
    trunk = B.parse_index()
    cats = stitch()
    roots = []
    for cat in B.CATEGORIES:
        node = {"name": cat, "children": idx.get(cat, []),
                "articles": [], "notes": []}
        for g in cats.get(cat, []):
            if not g["band"]:                        # the category's own band node --
                node["notes"].extend(g["notes"])     # its band-notes (from the whole);
                if not trunk.get(cat):               # a flat cat also carries its own
                    node["articles"].extend(g["lead"])   # bare run (Sports)
        roots.append(node)
    return roots


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

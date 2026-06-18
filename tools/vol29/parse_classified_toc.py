"""Parse vol 29's Classified Table of Contents into a category tree.

Output: data/derived/classified_toc.json
Schema:
  {
    "categories": [
      {
        "name": "Anthropology and Ethnology",
        "subsections": [
          {
            "name": "General Subjects and Terms",
            "articles": [
              {"target": "Anthropology", "display": "Anthropology",
               "filename": "12345-ANTHROPOLOGY.json", "emphasized": true},
              ...
            ]
          },
          ...
        ]
      },
      ...
    ]
  }

Sources:
  - Meta-TOC (ws 889-890): the 24 top-level category names and their
    hierarchical sub-sections with printed-page anchors.
  - Body pages (ws 891-955): vision-LLM transcription in vol29_ocr.json.
    ## marks Blackletter category headers; everything else is sub-headers
    or article entries.
"""
import bisect
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")

VOL29_DIR = Path("data/raw/wikisource/vol_29")
ARTICLES_INDEX = Path("data/derived/articles/index.json")
OCR_FILE = Path("data/derived/vol29_ocr.json")
OUT = Path("data/derived/classified_toc.json")

VOL29_OFFSET = 8  # ws 891 = printed 883


def _normalize(s: str) -> str:
    """Lowercase, strip non-alphanumeric. Used for cat/sub matching."""
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _art_norm(s: str) -> str:
    """Normalize for article-title matching: uppercase, strip accents,
    keep only A-Z and spaces, collapse whitespace."""
    s = unicodedata.normalize("NFKD", s.upper())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Z0-9 ]+", " ", s)
    return " ".join(s.split())


# ── Meta-TOC loading ─────────────────────────────────────────────────

def load_meta_toc_entries() -> list[dict]:
    """Parse the full meta-TOC (ws 889-890) into a flat list of
    entries with hierarchy info.

    The source is a wikitable where each row has:
      - leading empty cells (indentation)
      - a marker cell: '''I.''' (Roman, L1), 1. (Arabic, L2),
        (''a'') (italic letter, L3), or (1) (numeric, L4)
      - a name cell (possibly with colspan)
      - a page-number cell (3-digit)
    """
    text = ""
    for ws in (889, 890):
        wpath = VOL29_DIR / f"vol29-page{ws:04d}.json"
        if wpath.exists():
            try:
                d = json.loads(wpath.read_text(encoding="utf-8"))
                text += d.get("raw_text", "")
            except Exception:
                pass
    if not text:
        return []
    # Strip page-break boilerplate (running head, {{pagequality}}, the mid-
    # table </table><table> the scan inserts at each page foot).  Left in, it
    # glues onto a row's page-number cell ("917<noinclude>...") so the row
    # (e.g. History > Germany, which straddles the 889/890 break) is dropped.
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.DOTALL)

    entries: list[dict] = []
    current_cat = ""
    current_l2 = ""
    current_l3 = ""

    # Split into table rows.
    rows = re.split(r"^\|-\s*$", text, flags=re.MULTILINE)
    for row in rows:
        # Collapse to one line, join cells.
        flat = " ".join(row.split())
        # Strip {{ts|...}} templates.
        flat = re.sub(r"\{\{ts\|[^}]*\}\}", "", flat)
        # Strip colspan=N.
        flat = re.sub(r"colspan=\d+", "", flat)
        # Split on | and clean.
        cells = [c.strip() for c in flat.split("|") if c.strip()]
        if not cells:
            continue

        # Find the marker and name.
        marker = None
        level = 0
        name = ""
        page = 0

        for i, c in enumerate(cells):
            # Roman: '''I.''' or I.
            m = re.match(r"^(?:''')?([IVXLC]+)\.(?:''')?$", c)
            if m:
                marker = m.group(1)
                level = 1
                # Name is next non-numeric non-empty cell.
                for j in range(i + 1, len(cells)):
                    cj = re.sub(r"'''", "", cells[j]).strip()
                    if cj and not re.match(r"^\d{3}$", cj):
                        name = cj
                        break
                break
            # Arabic: 1.  (L2 marker — but Religion/Theology p941
            # has rows where this is co-located with an L3 marker:
            # `| 1. || (''a'') | General | 941`.  In that case the L2
            # has no own name; promote to the deeper level so we don't
            # emit a phantom L2 entry named "(a)".)
            m = re.match(r"^(\d+)\.$", c)
            if m:
                start = i + 1
                level = 2
                if start < len(cells):
                    nxt = cells[start]
                    if re.match(r"^\((?:'')?[a-z](?:'')?\)$", nxt):
                        level = 3; start += 1
                    elif re.match(r"^\(\d+\)$", nxt):
                        level = 4; start += 1
                for j in range(start, len(cells)):
                    cj = cells[j].strip()
                    if cj and not re.match(r"^\d{3}$", cj):
                        name = cj
                        break
                break
            # Italic letter: (''a'') or (a)  (L3 — peek for L4 in same row)
            m = re.match(r"^\((?:'')?([a-z])(?:'')?\)$", c)
            if m:
                start = i + 1
                level = 3
                if start < len(cells) and re.match(r"^\(\d+\)$", cells[start]):
                    level = 4; start += 1
                for j in range(start, len(cells)):
                    cj = cells[j].strip()
                    if cj and not re.match(r"^\d{3}$", cj):
                        name = cj
                        break
                break
            # Numeric: (1)
            m = re.match(r"^\((\d+)\)$", c)
            if m:
                level = 4
                for j in range(i + 1, len(cells)):
                    cj = cells[j].strip()
                    if cj and not re.match(r"^\d{3}$", cj):
                        name = cj
                        break
                break

        if not level or not name:
            continue

        # Find page number (last 3-digit number in cells).
        for c in reversed(cells):
            m2 = re.match(r"^(\d{3})\b", c.strip())
            if m2:
                page = int(m2.group(1))
                break
        if not page:
            continue

        # Clean name: strip italic markup and cross-ref notes.
        name = re.sub(r"''", "", name).strip()
        # Strip parenthetical cross-ref notes:
        #   (for X see under Y), (see also ...), (see further ...)
        name = re.sub(r"\s*\((?:for|see) .*", "", name).strip()
        # Strip broken template fragments: (to {{...
        name = re.sub(r"\s*\(to \{\{.*", "", name).strip()
        name = name.rstrip(".")

        if level == 1:
            current_cat = name
            current_l2 = ""
            current_l3 = ""
        elif level == 2:
            current_l2 = name
            current_l3 = ""
        elif level == 3:
            current_l3 = name

        entries.append({
            "level": level,
            "name": name,
            "top_cat": current_cat,
            "sub_label": (
                "" if level == 1
                else name if level == 2
                else f"{current_l2} \u2014 {name}" if level == 3
                else (
                    f"{current_l2} \u2014 {current_l3} \u2014 {name}"
                    if current_l3
                    else f"{current_l2} \u2014 {name}"
                )
            ),
            "printed_page": page,
        })

    return entries


def load_classified_toc_intro() -> str:
    """Load the editors' introduction (ws 887-888) and return HTML."""
    pages = []
    for ws in (887, 888):
        wpath = VOL29_DIR / f"vol29-page{ws:04d}.json"
        if wpath.exists():
            try:
                d = json.loads(wpath.read_text(encoding="utf-8"))
                text = d.get("raw_text", "").strip()
                if text:
                    text = re.sub(
                        r'<noinclude>.*?</noinclude>', '', text,
                        flags=re.DOTALL | re.IGNORECASE,
                    )
                    text = text.strip()
                    if text:
                        pages.append(text)
            except Exception:
                pass
    if not pages:
        return ""
    combined = "\n\n".join(pages)
    # Strip wikitext templates and markup.
    combined = re.sub(r"\{\{dropinitial\|(\w)\}\}", r"\1", combined)
    combined = re.sub(r"\{\{c\|[^}]*\}\}", "", combined)
    combined = re.sub(r"\{\{x-larger\|([^}]*)\}\}", r"\1", combined)
    combined = re.sub(r"\{\{[^{}]*\}\}", "", combined)
    combined = re.sub(r"'''([^']+)'''", r"<b>\1</b>", combined)
    combined = re.sub(r"''([^']+)''", r"<em>\1</em>", combined)
    combined = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", combined)
    # Strip remaining markup artifacts.
    combined = re.sub(r"<[^>]+>", "", combined)
    combined = re.sub(r"\{\{[^}]*\}\}", "", combined)
    paras = [p.strip() for p in combined.split("\n\n") if p.strip()]
    # Filter out very short fragments (template residue).
    paras = [p for p in paras if len(p) > 20]
    return "\n".join(f"<p>{p}</p>" for p in paras)


def load_meta_toc_categories() -> list[dict]:
    """Return the 24 top-level category names + printed pages."""
    entries = load_meta_toc_entries()
    return [e for e in entries if e.get("level") == 1]


def build_toc_from_meta(meta_categories: list[dict],
                        meta_entries: list[dict]) -> list[dict]:
    """Build the hierarchical TOC tree from meta-TOC entries."""
    by_cat: dict[str, list[dict]] = {}
    for e in meta_entries:
        if e.get("level", 1) <= 1:
            continue
        top = e.get("top_cat") or ""
        if top:
            by_cat.setdefault(top, []).append(e)

    toc: list[dict] = []
    for c in meta_categories:
        name = c["name"]
        entries = by_cat.get(name, [])
        if not entries:
            # Flat in the meta-TOC summary: this category's section names
            # live only in the body pages.  Start empty; walk_and_attribute
            # grows the subs from the printed `###` headers (_create_sub).
            # This is what retired the hard-coded _FLAT_CAT_SUBS.
            toc.append({"name": name, "subsections": []})
            continue
        subsections: list[dict] = []
        parent_at_level: dict[int, dict] = {}
        for e in entries:
            node = {
                "name": e.get("name") or "",
                "printed_page": e.get("printed_page"),
                "articles": [],
                "children": [],
                "_meta": True,   # a pp.881-882 skeleton node
            }
            level = e.get("level", 2)
            if level == 2:
                subsections.append(node)
            else:
                parent = None
                for pl in range(level - 1, 1, -1):
                    if pl in parent_at_level:
                        parent = parent_at_level[pl]
                        break
                if parent is None:
                    subsections.append(node)
                else:
                    parent["children"].append(node)
            parent_at_level[level] = node
            for deeper in [k for k in parent_at_level if k > level]:
                del parent_at_level[deeper]
        # The meta-TOC numbers each continent's 'Ancient geography' as the last
        # item in its country list (Turkey in Europe = (22), Ancient geography
        # = (23)), so it nests under 'Countries' at country level.  But ancient
        # geography is NOT a country -- it's a continent-level section spanning
        # the whole continent (the body heads it '### Europe: Ancient Geography',
        # parallel to Physical features and Countries).  Lift it to a
        # continent-level sibling of Countries, and fix the meta-TOC's
        # 'goography' transcription typo while we're moving it.
        for continent in subsections:
            for container in continent.get("children", []):
                promoted = [k for k in container.get("children", [])
                            if _normalize(k["name"])
                            in ("ancientgeography", "ancientgoography")]
                for node in promoted:
                    container["children"].remove(node)
                    node["name"] = "Ancient geography"
                    continent["children"].append(node)
        # Mark skeleton leaves.  In a category whose meta-TOC spells out its
        # subcategories (Literature: Classical has Subjects/Biographies/...,
        # but every COUNTRY is a bare leaf), a leaf is TERMINAL: it has no
        # subcategories, so the body lists its articles directly (France's
        # *French Literature* is a principal article, not a sub-header).
        def _mark_terminal(nodes: list[dict]):
            for n in nodes:
                _mark_terminal(n.get("children", []))
                n["_terminal"] = not n.get("children")
        _mark_terminal(subsections)
        toc.append({"name": name, "subsections": subsections})
    return toc


# ── Walk & attribute ─────────────────────────────────────────────────

# Known aliases: body-text form → meta-TOC canonical form (normalized).
_SUB_ALIASES: dict[str, str] = {
    "servia": "serbia",
    "australasia": "australia",  # History's "Australasia" — meta-TOC typo'd it
    "britainandirelandancientnames": "britainandirelandancient",
    "mammalia": "mammals",
    "bird": "birds",
    "insect": "insects",
    "batrachia": "batrachians",
    "divisionsandtowns": "divisionandtowns",
    "saint": "saints",
    "indochinafrench": "indochlnafrench",
    "mediterraneanislandsetc": "mediterraneanislandsc",
    # The body's page-2 continuation drops "the": "Church History to Council
    # of Trent" for the skeleton's "Church History to THE Council of Trent".
    "churchhistorytocounciloftrent": "churchhistorytothecounciloftrent",
    "classicalscholar": "classicalscholars",
    "classics": "classicalgreekandlatin",
    "classical": "classicalgreekandlatin",
    "hebrewarmenianandsyriacliterature": "hebrewarmenianandsyriac",
    "militarywritersandengineers": "biographies",
}


def walk_and_attribute(toc: list[dict],
                       meta_entries: list[dict],
                       article_index: list[dict]) -> dict:
    """Walk vol29_ocr.json linearly, attribute articles to the meta-TOC
    tree, and resolve them against the article index.

    Structure detection uses only exact matching (with aliases).
    Fuzzy matching is used only for article-name → corpus resolution."""

    ocr_data: dict[str, str] = {}
    if OCR_FILE.exists():
        ocr_data = json.loads(OCR_FILE.read_text(encoding="utf-8"))

    # ── Cat lookup ────────────────────────────────────────────────
    cat_by_norm: dict[str, dict] = {}
    for cat in toc:
        cat_by_norm[_normalize(cat["name"])] = cat

    # ── Sub lookup per cat (all depths) ───────────────────────────
    # Maps cat_name → {normalized_sub_name → [candidate nodes]}.
    # A single name (e.g. "Biographies") can occur under many parents
    # in one cat (Religion has Biographies under Catholic, Eastern,
    # Reformation, Modern Continental, ...). Store all candidates so
    # the walker can prefer the one that's a sibling of cur_sub.
    sub_lookup: dict[str, dict[str, list[dict]]] = {}
    parent_map: dict[int, dict | None] = {}  # id(node) → parent node

    def _strip_parens(s: str) -> str:
        """Strip parenthetical qualifiers from sub names:
        'Europe (continental)' → 'Europe',
        'Countries (with division and towns)' → 'Countries'."""
        return re.sub(r"\s*\(.*?\)", "", s).strip()

    def _register_subs(cat_name: str, nodes: list[dict],
                       parents: list[dict] | None = None):
        if parents is None:
            parents = []
        lk = sub_lookup.setdefault(cat_name, {})
        parent_node = parents[-1] if parents else None
        for n in nodes:
            parent_map[id(n)] = parent_node
            name = n["name"]
            # Register both full name and stripped-parens form.
            for form in {name, _strip_parens(name)}:
                norm = _normalize(form)
                if norm:
                    lk.setdefault(norm, []).append(n)
            # Parent-prefixed compounds for X:Y matching.
            norm = _normalize(_strip_parens(name))
            if parents:
                parent_norm = _normalize(_strip_parens(parents[-1]["name"]))
                compound = parent_norm + norm
                if compound:
                    lk.setdefault(compound, []).append(n)
            _register_subs(cat_name, n.get("children", []),
                           parents + [n])

    for cat in toc:
        _register_subs(cat["name"], cat["subsections"])

    def _prefer_relative(candidates: list[dict],
                          cur: dict | None) -> dict:
        """When multiple sub nodes share a name, prefer the one whose
        parent is on cur's ancestor chain (or cur itself). This keeps
        'Biographies' under Modern Continental from matching Catholic
        Biographies when cur_sub is inside Modern Continental."""
        if not cur or len(candidates) == 1:
            return candidates[0]
        # Build cur's ancestor chain.
        ancestors: set[int] = set()
        node = cur
        while node is not None:
            ancestors.add(id(node))
            node = parent_map.get(id(node))
        # Prefer candidate whose parent is in the ancestor chain.
        for cand in candidates:
            p = parent_map.get(id(cand))
            if p is not None and id(p) in ancestors:
                return cand
        return candidates[0]

    # ── Page carryover from meta-TOC anchors ──────────────────────
    sub_anchors: list[tuple[int, str, dict]] = []

    def _collect_anchors(cat_name: str, nodes: list[dict]):
        for n in nodes:
            pp = n.get("printed_page")
            if pp:
                sub_anchors.append((pp, cat_name, n))
            _collect_anchors(cat_name, n.get("children", []))

    for cat in toc:
        _collect_anchors(cat["name"], cat["subsections"])
    sub_anchors.sort(key=lambda x: x[0])

    def _carryover(ws: int) -> tuple[str | None, dict | None]:
        printed = ws - VOL29_OFFSET
        starts = [(c, n) for pp, c, n in sub_anchors if pp == printed]
        if starts:
            return starts[0]
        active_cat, active_node = None, None
        for pp, c, n in sub_anchors:
            if pp > printed:
                break
            active_cat, active_node = c, n
        return active_cat, active_node

    # ── Article title index ───────────────────────────────────────
    title_lookup: dict[str, tuple[str, str]] = {}  # _art_norm → (filename, title)
    for e in article_index:
        if e.get("article_type") != "article":
            continue
        norm = _art_norm(e["title"])
        if norm and norm not in title_lookup:
            title_lookup[norm] = (e["filename"], e["title"])
    # Sorted title norms for the abbreviated-forename prefix fallback below.
    sorted_norms = sorted(title_lookup)

    # ── Safe matcher structures (biographies + structural variants) ───
    # The classified TOC lists REAL articles in abbreviated form, so every
    # entry has exactly one target.  These indexes recover the obvious misses
    # WITHOUT fuzzing: biographies key on surname + forename-initials (the
    # forename confirms even an OCR-garbled surname); structural strips let
    # "Zug" find "Zug (Canton)" and "Ethnology" find "Ethnology and
    # Ethnography".
    bio_index: dict[str, list[tuple[list[str], tuple[str, str]]]] = {}
    strip_index: dict[str, list[tuple[str, str]]] = {}
    sur_by_first: dict[str, set[str]] = {}
    for e in article_index:
        if e.get("article_type") != "article":
            continue
        t = e["title"]
        val = (e["filename"], t)
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

    base_by_first: dict[str, list[str]] = {}
    for bn in strip_index:
        base_by_first.setdefault(bn[:1], []).append(bn)

    def _lev_le(a: str, b: str, k: int) -> bool:
        """Levenshtein(a, b) <= k, early-exit."""
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

    def _forenames_ok(toc_toks: list[str], art_toks: list[str]) -> bool:
        """Each TOC forename token is a prefix of the article's (initials OK):
        "Adolph F. A." confirms "Adolph Francis Alphonse"."""
        if len(toc_toks) > len(art_toks):
            return False
        return all(_art_norm(b).startswith(_art_norm(a))
                   for a, b in zip(toc_toks, art_toks))

    def _resolve_extra(raw: str) -> tuple[str, str] | None:
        """Recover the obvious misses the exact cascade leaves — never a guess:
        biographies (surname + forename, surname OCR-tolerant ONLY when the
        forename confirms it and the result is unique) and structural variants
        (disambiguator/compound strip, singular/plural, "X or Y")."""
        n = _art_norm(raw)
        # _art_norm upper-cases, so the plural suffix must too.
        if n + "S" in title_lookup:
            return title_lookup[n + "S"]
        if n.endswith("S") and len(n) > 3 and n[:-1] in title_lookup:
            return title_lookup[n[:-1]]
        st = strip_index.get(n)
        if st and len({v[0] for v in st}) == 1:
            return st[0]
        if " or " in raw:
            for part in raw.split(" or "):
                pn = _art_norm(part)
                if pn in title_lookup:
                    return title_lookup[pn]
        if "," in raw:
            sur, fore = raw.split(",", 1)
            sn = _art_norm(sur)
            toks = [w for w in re.split(r"[ .]+", fore) if w]
            cands = [v for tk, v in bio_index.get(sn, [])
                     if _forenames_ok(toks, tk)]
            if len({v[0] for v in cands}) == 1:
                return cands[0]
            ocr = [v for cs in sur_by_first.get(sn[:1], ())
                   if cs != sn and _lev_le(sn, cs, 2)
                   for tk, v in bio_index[cs] if _forenames_ok(toks, tk)]
            if len({v[0] for v in ocr}) == 1:
                return ocr[0]
        elif n:
            # OCR-garbled single name (a place or tribe: "Chukehi" -> CHUKCHI).
            # A UNIQUE corpus title within edit-distance 1.  No second signal to
            # confirm, so an occasional wrong link is possible -- acceptable for
            # a navigation aid (not contributor data); >90% right is a win.
            cands = [bn for bn in base_by_first.get(n[:1], ())
                     if bn != n and abs(len(bn) - len(n)) <= 1
                     and _lev_le(n, bn, 1)]
            if len({v[0] for bn in cands for v in strip_index[bn]}) == 1:
                return strip_index[cands[0]][0]
        return None

    def _split_lead(text: str) -> list[str]:
        """Split a lead line the OCR ran together ("Anglo-Norman Literature
        French Literature Provençal Literature") into its constituent article
        titles by greedy longest-prefix.  Returns [text] unchanged unless the
        WHOLE line consumes into >= 2 known articles (so a single lead, or a
        normal title, is never half-split)."""
        toks = text.split()
        if len(toks) < 2:
            return [text]
        pieces: list[str] = []
        i = 0
        while i < len(toks):
            hit = None
            for j in range(len(toks), i, -1):
                cand = " ".join(toks[i:j])
                if _art_norm(cand) in title_lookup:
                    hit = (cand, j)
                    break
            if hit is None:
                return [text]
            pieces.append(hit[0])
            i = hit[1]
        return pieces if len(pieces) >= 2 else [text]

    # ── Sub matching ──────────────────────────────────────────────

    def _try_sub(cat_name: str, text: str,
                  cur: dict | None = None) -> dict | None:
        """Exact sub-header match with (cont.) stripping and aliases.
        When multiple candidates share a name, prefers the one related
        to `cur` (same ancestor chain)."""
        if cat_name not in sub_lookup:
            return None
        lk = sub_lookup[cat_name]
        clean = re.sub(r"\s*\(cont\.?\)\s*$", "", text,
                       flags=re.IGNORECASE).strip()
        norm = _normalize(clean)
        if not norm:
            return None
        # Exact.
        if norm in lk:
            return _prefer_relative(lk[norm], cur)
        # Alias.
        alias = _SUB_ALIASES.get(norm)
        if alias and alias in lk:
            return _prefer_relative(lk[alias], cur)
        # Singular ↔ plural.
        if norm + "s" in lk:
            return _prefer_relative(lk[norm + "s"], cur)
        if norm.endswith("s") and len(norm) > 3 and norm[:-1] in lk:
            return _prefer_relative(lk[norm[:-1]], cur)
        # "Parent (Child)" — a trailing parenthetical that names a SUB of
        # Parent selects that sub: "Biographies (Latin)" -> Biographies > Latin,
        # "Biographies (Greek)" -> Greek (not Biographies' first leaf).  Only
        # fires when BOTH the outer name resolves to a node AND the parenthetical
        # matches one of its children, so "India (with lesser Frontier States)"
        # and "Naples (Italy)" fall through to the bare-name strip below.
        pm = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", clean)
        if pm:
            outer = _try_sub(cat_name, pm.group(1), cur)
            if outer is not None:
                bnorm = _normalize(pm.group(2))
                for child in outer.get("children", []):
                    if _normalize(child["name"]) == bnorm:
                        return child
        # Parenthetical qualifier removed: "India (with lesser Frontier
        # States)" matches the meta node registered under its bare name
        # (the meta-TOC sometimes carries a different qualifier or typo).
        bare = _normalize(_strip_parens(clean))
        if bare and bare != norm and bare in lk:
            return _prefer_relative(lk[bare], cur)
        return None

    # Sub-sub header names that the classified TOC uses inline under
    # level-2 subs (e.g. "Architecture: Subjects", "Music: Instruments").
    # When an X:Y pattern has Y in this set and X matches a level-2 sub
    # with no existing child Y, we create a new child dynamically.
    _DYNAMIC_SUBSUB_NAMES = {
        "subjects", "biographies", "instruments", "divisions",
        "towns", "townsetc", "general", "names", "legendaryfigures",
        "scholars", "critics",
    }

    # Reconciliation table: a printed BODY section name → the authoritative
    # SKELETON child name it abbreviates.  EB11's body and its pp.881-2 index
    # spell the same section differently ("Biographies" for "General
    # Biographies", "Towns, etc." for "Towns", "Critics" for "Biographies of
    # critics").  Keyed by the normalized body name.  This NEVER fires on its
    # own — `_match_sub` consults it only after an exact/plural child match
    # fails, and re-enters the skeleton child ONLY when a child by that exact
    # name already exists under the matched parent.  So it can't cross parents,
    # can't match fuzzily, and can't create a node: where the body name IS the
    # skeleton name (US History's own "Biographies"), the exact match fires
    # first and this is never reached.
    _SUBSUB_VARIANTS: dict[str, tuple[str, ...]] = {
        "biographies": ("General Biographies",),
        "townsetc": ("Towns",),
        "critics": ("Biographies of critics",),
        "general": ("General subjects",),
        "ancientnames": ("Ancient geography",),
        "scholars": ("Classical scholars",),
    }

    def _descendant_by_norm(root: dict, target_norm: str) -> dict | None:
        """Nearest node in root's subtree whose name normalizes to target_norm
        (BFS).  Lets a reconciliation target sit a level below the matched
        parent — "Classics: Scholars" -> Classical > Biographies > Classical
        scholars."""
        queue = list(root.get("children", []))
        while queue:
            nxt: list[dict] = []
            for n in queue:
                if _normalize(n["name"]) == target_norm:
                    return n
                nxt.extend(n.get("children", []))
            queue = nxt
        return None

    # Parent-scoped reconciliation, for body names too common to key on alone.
    # (parent_norm, body_norm) -> skeleton child name.  "Subjects" is used as
    # the lead-section name across the whole corpus, so it can't be a global
    # variant; but Church History to the Council of Trent is the one sub whose
    # skeleton names that lead "General" (every sibling church-history sub uses
    # "Subjects"), and the body heads it "...: Subjects" like the rest.
    _SCOPED_SUBSUB_VARIANTS: dict[tuple[str, str], str] = {
        ("churchhistorytothecounciloftrent", "subjects"): "General",
    }

    def _match_sub(cat_name: str, line: str,
                    cur: dict | None = None) -> dict | None:
        """Try full line, then X:Y split.
        For X:Y, if X matches a parent sub, try Y as a child of X.
        Creates dynamic child if Y is a known sub-sub name."""
        hit = _try_sub(cat_name, line, cur)
        if hit:
            return hit
        if ":" in line:
            x, y = line.split(":", 1)
            x, y = x.strip(), y.strip()
            # X == cat name itself: the body uses "Cat : Sub" to re-assert
            # the current cat at a sub transition. Just resolve Y.
            if _normalize(x) == _normalize(cat_name):
                y_clean = re.sub(r"\s*\(cont\.?\)\s*$", "", y,
                                 flags=re.IGNORECASE).strip()
                return _try_sub(cat_name, y_clean, cur)
            parent = _try_sub(cat_name, x, cur)
            if parent:
                # Try Y as a child of parent (strip cont. and parens).
                y_clean = re.sub(r"\s*\(cont\.?\)\s*$", "", y,
                                 flags=re.IGNORECASE).strip()
                # A parenthetical sub-selector ("Biographies (Latin)") resolves
                # to a DESCENDANT of parent — route there before the parens are
                # stripped (which would collapse it to "Biographies" and land on
                # the first leaf).  Scoped: only accept a hit living under parent.
                if "(" in y_clean:
                    y_hit = _try_sub(cat_name, y_clean, parent)
                    _nd = y_hit
                    while _nd is not None:
                        if _nd is parent:
                            return y_hit
                        _nd = parent_map.get(id(_nd))
                y_clean = re.sub(r"\s*\(.*?\)", "", y_clean).strip()
                if y_clean:
                    y_norm = _normalize(y_clean)
                    for child in parent.get("children", []):
                        # Match full name, parens-stripped, or the leading phrase
                        # before a comma ("Countries" -> "Countries, general
                        # list", the America countries node).
                        for form in {child["name"],
                                     _strip_parens(child["name"]),
                                     child["name"].split(",")[0].strip()}:
                            if _normalize(form) == y_norm:
                                return child
                        # Singular/plural on child name.
                        cn = _normalize(_strip_parens(child["name"]))
                        if cn + "s" == y_norm or (
                            y_norm.endswith("s") and y_norm[:-1] == cn
                        ):
                            return child
                    # Spelling reconciliation: re-enter an EXISTING skeleton
                    # child this body name abbreviates, rather than spawning a
                    # stray beside it (guarded — only fires when that skeleton
                    # child already exists under this parent).
                    for skel_name in _SUBSUB_VARIANTS.get(y_norm, ()):
                        hit = _descendant_by_norm(parent, _normalize(skel_name))
                        if hit is not None:
                            return hit
                    parent_norm = _normalize(_strip_parens(parent["name"]))
                    sk = _SCOPED_SUBSUB_VARIANTS.get((parent_norm, y_norm))
                    if sk:
                        sk_norm = _normalize(sk)
                        for child in parent.get("children", []):
                            if _normalize(child["name"]) == sk_norm:
                                return child
                    # Dynamic child creation: Y is a known sub-sub name
                    # and parent has no matching child yet.
                    if y_norm in _DYNAMIC_SUBSUB_NAMES:
                        new_child = {
                            "name": y_clean,
                            "printed_page": parent.get("printed_page"),
                            "articles": [],
                            "children": [],
                        }
                        parent.setdefault("children", []).append(new_child)
                        parent_map[id(new_child)] = parent
                        lk = sub_lookup.setdefault(cat_name, {})
                        lk.setdefault(y_norm, []).append(new_child)
                        # Parent-prefixed compound for future matching.
                        parent_prefix = _normalize(
                            _strip_parens(parent["name"]))
                        lk.setdefault(parent_prefix + y_norm,
                                      []).append(new_child)
                        return new_child
                return parent  # Y didn't match a child; use X
        return None

    def _first_leaf(node: dict | None) -> dict | None:
        """Descend children[0] until leaf. Articles accumulate in leaves."""
        if node is None:
            return None
        while node.get("children"):
            node = node["children"][0]
        return node

    def _create_sub(cat_name: str, text: str,
                    cur: dict | None) -> dict | None:
        """Create + register a sub from a body SECTION header the meta-TOC
        never carried.  Parses the `Parent : Child` colon form into the
        right nesting; a bare name becomes a top-level sub.  This is what
        retires _FLAT_CAT_SUBS — the meta-flat categories now grow their
        own subs straight from the printed `###` headers."""
        text = re.sub(r"\s*\(cont\.?\)\s*$", "", text,
                      flags=re.IGNORECASE).strip()
        if not text:
            return None
        parent = None
        name = text
        if ":" in text:
            x, y = (p.strip() for p in text.split(":", 1))
            if y and _normalize(x) == _normalize(cat_name):
                name = y                      # `Cat : Child` re-assertion
            elif y:
                parent = _try_sub(cat_name, x, cur)
                if parent is None:
                    parent = _create_sub(cat_name, x, cur)  # new Parent
                name = y
        elif cur is not None:
            # A banner re-asserting an existing top-level region ("UNITED
            # KINGDOM" for "United Kingdom of Great Britain and Ireland",
            # "Finance" for "Finance and Currency") re-enters it rather than
            # spawning a stray.
            _cat = cat_by_norm.get(_normalize(cat_name))
            _nn = _normalize(name)
            for ex in (_cat["subsections"] if _cat else []):
                en = _normalize(ex["name"])
                if en and _nn and (en.startswith(_nn) or _nn.startswith(en)):
                    return ex
            # Otherwise hang off the nearest SKELETON node (never another body
            # node) so siblings don't chain (`France > [Anglo-Norman, ...]`).
            nd = cur
            while nd is not None and not nd.get("_meta"):
                nd = parent_map.get(id(nd))
            parent = nd
        if not name:
            return None
        node = {"name": name, "printed_page": None,
                "articles": [], "children": []}
        if parent is not None:
            parent.setdefault("children", []).append(node)
            parent_map[id(node)] = parent
        else:
            cat = cat_by_norm.get(_normalize(cat_name))
            if cat is None:
                return None
            # An abbreviated re-assertion banner ("UNITED KINGDOM" for the
            # existing "United Kingdom of Great Britain and Ireland") should
            # re-enter that region, not spawn an empty duplicate top-level sub.
            nn = _normalize(name)
            for ex in cat["subsections"]:
                en = _normalize(ex["name"])
                if en and nn and (en.startswith(nn) or nn.startswith(en)):
                    return ex
            cat["subsections"].append(node)
            parent_map[id(node)] = None
        lk = sub_lookup.setdefault(cat_name, {})
        for form in {name, _strip_parens(name)}:
            nn = _normalize(form)
            if nn:
                lk.setdefault(nn, []).append(node)
        if parent is not None:
            compound = (_normalize(_strip_parens(parent["name"]))
                        + _normalize(_strip_parens(name)))
            if compound:
                lk.setdefault(compound, []).append(node)
        return node

    # ── Walk pages ────────────────────────────────────────────────
    cur_cat: str | None = None
    cur_sub: dict | None = None
    # Accumulated raw article names per sub node.
    raw_entries: dict[int, list[tuple[str, bool]]] = {}
    node_map: dict[int, dict] = {}

    for ws in range(891, 956):
        text = ocr_data.get(str(ws), "")
        if not text.strip():
            print(f"    ws{ws} ... skipped")
            continue

        # Page carryover from meta-TOC anchors. Used to:
        # - Bootstrap the first page (cur_cat is None).
        # - Update cur_sub within the same cat (the meta-TOC knows
        #   which sub starts on which printed page).
        # NOT used to switch cats — ## headers in the OCR do that.
        # Without this guard, carryover would override the OCR
        # (e.g. Military content on ws947 would be reset to Philosophy
        # because the meta-TOC anchors Philosophy at printed p.939).
        co_cat, co_node = _carryover(ws)
        if co_cat:
            if cur_cat is None:
                # Bootstrap.
                cur_cat = co_cat
                if co_node is not None:
                    cur_sub = _first_leaf(co_node)
            elif co_cat == cur_cat and co_node is not None:
                # Same cat — update sub anchor.
                cur_sub = _first_leaf(co_node)

        count = 0
        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if not line or line == "<!-- vision-ocr -->":
                continue

            # Skip cross-reference annotations like `(See also …)` /
            # `(See further under …)` / `(For X see under Y)` — these
            # are inline notes from the printed index, not category
            # entries. Without this guard, the article-matching
            # `first-word` fallback strips the leading `(` via
            # `_art_norm` and resolves `(See` → SEE article, polluting
            # categories with bogus SEE entries.
            if re.match(r"^\(\s*(?:see|for)\b", line, re.IGNORECASE):
                continue

            # Detect a ## / ### header.  The OCR is inconsistent about the
            # marker depth (it writes `##` for some sections), so treat both
            # as headers and disambiguate category-vs-section by the known
            # category names below, not by the depth.
            is_header = False
            hdr3 = False  # a `###` header is ALWAYS a section, never a category
            if line.startswith("### "):
                is_header = True
                hdr3 = True
                line = line[4:].strip()
            elif line.startswith("## "):
                is_header = True
                line = line[3:].strip()

            # Strip **bold** markers first, then detect *italic*.
            line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
            emphasized = (
                line.startswith("*") and line.endswith("*")
                and not line.startswith("**")
            )
            line = re.sub(r"\*([^*]+)\*", r"\1", line)

            # Normalize em-dash → colon for sub-header detection.
            line = re.sub(r"\s*[\u2014\u2013]\s*", ": ", line)

            # ── ## line: cat or sub transition ────────────────────
            if is_header:
                # Drop a trailing cross-reference note so it isn't split into
                # bogus sub-nodes ("... (See also ASIA: Mountains, above ...)").
                line = re.sub(r"\s*\((?:see|for)\b.*$", "", line,
                              flags=re.IGNORECASE).strip()
                norm = _normalize(line)
                if not hdr3 and norm in cat_by_norm:
                    cat_dict = cat_by_norm[norm]
                    cur_cat = cat_dict["name"]
                    subs = cat_dict.get("subsections", [])
                    cur_sub = _first_leaf(subs[0]) if subs else None
                    continue
                # Not a category, so it's a SECTION header.  Match it to a
                # known sub, or — when the body carries a section the meta-TOC
                # never had (the meta-flat categories) — create and register
                # it.  A header is consumed, never accumulated as an article.
                if cur_cat:
                    # A bare physical-features subsection header (Lakes,
                    # Mountains, Rivers, Miscellaneous, Deserts, Islands, ...)
                    # recurs under EVERY continent's "Physical features".  A
                    # global match binds them all to the first continent walked
                    # (Europe's), so Asia/Africa/America's lakes and rivers leak
                    # into Europe's.  When inside a PF node, bind such a
                    # subsection to OUR PF — but a bare header that resolves to a
                    # real sub elsewhere (a country) is a genuine transition out.
                    pf_owner = None
                    if ":" not in line:
                        nd = cur_sub
                        while nd is not None:
                            if _normalize(nd["name"]) == "physicalfeatures":
                                pf_owner = nd
                                break
                            nd = parent_map.get(id(nd))
                    new_sub = _match_sub(cur_cat, line, cur_sub)
                    if pf_owner is not None:
                        mp = parent_map.get(id(new_sub)) if new_sub else None
                        # A PF subsection: matched nothing, or matched a node
                        # that is itself a child of SOME "Physical features"
                        # (Europe's, in the leak).  Re-home it on our PF.
                        if new_sub is None or (
                                mp is not None
                                and _normalize(mp["name"]) == "physicalfeatures"):
                            name = (new_sub["name"] if new_sub else
                                    re.sub(r"\s*\(cont\.?\)\s*$", "", line,
                                           flags=re.IGNORECASE).strip())
                            new_sub = next(
                                (c for c in pf_owner.get("children", [])
                                 if _normalize(c["name"]) == _normalize(name)),
                                None) or _create_sub(cur_cat, name, pf_owner)
                    # A flat Literature classification (every country is a bare
                    # skeleton leaf) has NO subcategories.  Its ### entries are
                    # the country's literature ARTICLES — bare "French
                    # Literature" (split if the OCR ran several together) — or
                    # SECTION LINKS — colon "Denmark : Literature", i.e. the
                    # Literature section of the country article (Denmark#Literature).
                    # Never a sub-header; never a phantom subcategory.
                    if (cur_cat == "Literature" and cur_sub is not None
                            and cur_sub.get("_terminal")
                            and (new_sub is None or new_sub is cur_sub)):
                        # Section link: the entry leads with the country's OWN
                        # name + a section mark ("Denmark : Literature").  The
                        # print's mark reads as colon / comma / section-sign —
                        # the OCR is inconsistent — so key on the country name
                        # followed by ANY such punctuation, not a literal ":".
                        sl = re.match(
                            re.escape(cur_sub["name"])
                            + r"\s*[,:;.§–—-]+\s*(.+)$",
                            line, re.IGNORECASE)
                        if sl:
                            sec = re.sub(r"\s*\(cont\.?\)\s*$", "", sl.group(1),
                                         flags=re.IGNORECASE).strip()
                            if sec:
                                raw_entries.setdefault(id(cur_sub), []).append(
                                    (f"{cur_sub['name']}#{sec}", emphasized))
                                node_map[id(cur_sub)] = cur_sub
                                count += 1
                            continue
                        if new_sub is None:
                            # Bare principal article(s) (split a run-together line).
                            for piece in _split_lead(line):
                                raw_entries.setdefault(id(cur_sub), []).append(
                                    (piece, emphasized))
                                count += 1
                            node_map[id(cur_sub)] = cur_sub
                            continue
                        continue  # re-assertion of the country, no new content
                    if new_sub is None:
                        new_sub = _create_sub(cur_cat, line, cur_sub)
                    if new_sub:
                        # A flat section (Art's Sculpture) accumulates its own
                        # articles directly until its FIRST sub-header is seen;
                        # the body prints that header ("Sculpture: Subjects")
                        # after the column it heads.  Those articles belong to
                        # the sub just declared — hand them over so nothing is
                        # left stranded in the bare section.
                        par = parent_map.get(id(new_sub))
                        if (par is not None and id(par) in raw_entries
                                and par.get("children") == [new_sub]):
                            raw_entries.setdefault(id(new_sub), []).extend(
                                raw_entries.pop(id(par)))
                            node_map[id(new_sub)] = new_sub
                        cur_sub = _first_leaf(new_sub)
                continue

            # ── Plain line: sub transition? ───────────────────────
            # Special handling for "General list" sections: these are
            # flat lists of country articles where some names coincide
            # with sub names. The country name appears twice — first
            # as an article in the General list, then as a sub-header
            # introducing the detailed section. Treat the FIRST
            # occurrence as an article; the SECOND as a sub transition.
            in_general_list = (
                cur_sub is not None
                and "general list" in cur_sub.get("name", "").lower()
            )
            if cur_cat and len(line) <= 80:
                if in_general_list and ":" not in line:
                    # Check if this line already appeared as an article
                    # in the current General list bucket. If so, it's a
                    # sub transition. If not, it's another article.
                    existing = raw_entries.get(id(cur_sub), [])
                    seen_here = any(
                        raw_name.strip().lower() == line.strip().lower()
                        for raw_name, _ in existing
                    )
                    if not seen_here:
                        pass  # first occurrence — treat as article
                    else:
                        new_sub = _match_sub(cur_cat, line, cur_sub)
                        if new_sub:
                            leaf = _first_leaf(new_sub)
                            if leaf is not cur_sub:
                                cur_sub = leaf
                            continue
                else:
                    new_sub = _match_sub(cur_cat, line, cur_sub)
                    if new_sub:
                        leaf = _first_leaf(new_sub)
                        # If new_sub is an ANCESTOR of cur_sub we're already
                        # inside it: this "transition" is the section's
                        # emphasized headword (*Asia* heading "Asia: Ancient
                        # Names", *Sculpture* heading its own section) or a
                        # mid-section re-assertion — NOT a forward move.
                        # Descending to the ancestor's first leaf would wrongly
                        # eject us from the section (the ancient-names list then
                        # piles into Physical features > Lakes).
                        anc = set()
                        _n = cur_sub
                        while _n is not None:
                            anc.add(id(_n))
                            _n = parent_map.get(id(_n))
                        if leaf is not cur_sub and id(new_sub) not in anc:
                            cur_sub = leaf
                            continue
                        # leaf IS cur_sub: a "transition" that doesn't move is
                        # the tell that this line is the section's OWN headword
                        # article (SCULPTURE under Sculpture), which sits right
                        # under its header.  Empty bucket => we're at the section
                        # head, so keep it as the lead; non-empty bucket => a
                        # mid-section "(cont.)" re-assertion, consume as before.
                        if raw_entries.get(id(cur_sub)):
                            continue

            # ── Article accumulation ──────────────────────────────
            if cur_sub is not None:
                nid = id(cur_sub)
                raw_entries.setdefault(nid, []).append((line, emphasized))
                node_map[nid] = cur_sub
                count += 1

        print(f"    ws{ws} ... {count} entries")

    # ── Match accumulated entries against article index ───────────
    total_raw = sum(len(v) for v in raw_entries.values())
    print(f"\n  Matching {total_raw:,} raw entries against "
          f"{len(title_lookup):,} article titles...")

    discovered = 0
    unmatched_entries: list[str] = []

    for nid, entries in raw_entries.items():
        node = node_map[nid]
        seen: set[str] = {
            a.get("filename") for a in node.get("articles", [])
            if a.get("filename")
        }
        for raw_name, emph in entries:
            norm = _art_norm(raw_name)
            match = title_lookup.get(norm)
            if not match:
                # Strip parenthetical qualifier: "Naples (Italy)" → "Naples"
                cleaned = re.sub(r"\s*\(.*\)\s*$", "", raw_name).strip()
                if cleaned != raw_name:
                    match = title_lookup.get(_art_norm(cleaned))
            if not match:
                # Strip everything in parens anywhere:
                # "Lofoten and Vesteraalen (isls.)" → "Lofoten and Vesteraalen"
                cleaned = re.sub(r"\s*\([^)]*\)", "", raw_name).strip()
                if cleaned != raw_name:
                    match = title_lookup.get(_art_norm(cleaned))
            if not match:
                # Try up to first comma: "LASTNAME, Firstname" → "LASTNAME"
                comma = raw_name.split(",", 1)[0].strip()
                if comma != raw_name and len(comma) >= 4:
                    match = title_lookup.get(_art_norm(comma))
            if not match:
                # "X or Y" alternate names: "Ahom or Aham" → "AHOM"
                if " or " in raw_name:
                    before_or = raw_name.split(" or ")[0].strip()
                    match = title_lookup.get(_art_norm(before_or))
            if not match:
                # First word only (biographical entries with initials):
                # "Detaille, J. B. E." → "DETAILLE"
                first = raw_name.split()[0].rstrip(".,;:") if raw_name else ""
                # Length check on the NORMALIZED form so a 4-char
                # token like `(See` doesn't pass — its normalized form
                # is `SEE` (3 chars) and would resolve to the SEE
                # article inappropriately.
                first_norm = _art_norm(first)
                if len(first_norm) >= 4:
                    match = title_lookup.get(first_norm)

            if not match and " " in norm:
                # Abbreviated forename: the printed index clips the last
                # forename to an initial — "Airy, Sir George B." vs the article
                # "AIRY, SIR GEORGE BIDDELL".  Accept the OCR name as a token-
                # prefix of EXACTLY ONE article title (the trailing token an
                # initial, or a clean token-boundary drop).  Unique-only — it
                # never guesses between two candidates.
                lo = bisect.bisect_left(sorted_norms, norm)
                if lo < len(sorted_norms) and sorted_norms[lo].startswith(norm):
                    cand = sorted_norms[lo]
                    unique = (lo + 1 >= len(sorted_norms)
                              or not sorted_norms[lo + 1].startswith(norm))
                    last_initial = len(norm.rsplit(" ", 1)[-1]) == 1
                    token_boundary = (len(cand) > len(norm)
                                      and cand[len(norm)] == " ")
                    if unique and (last_initial or token_boundary):
                        match = title_lookup[cand]

            if not match:
                # Safe recovery of the obvious misses: biographies by surname +
                # forename, structural disambiguator/compound/plural variants.
                match = _resolve_extra(raw_name)

            if not match and "#" in raw_name:
                # Section link "Country#Section" (Denmark#Literature): resolve
                # the article, carry the #anchor to the section.
                base, anchor = raw_name.split("#", 1)
                bm = title_lookup.get(_art_norm(base))
                if bm:
                    filename, base_disp = bm
                    if filename not in seen:
                        node["articles"].append({
                            "target": raw_name,
                            "display": anchor.strip() or base_disp,
                            "filename": filename,
                            "anchor": anchor.strip(),
                            "emphasized": emph,
                        })
                        seen.add(filename)
                        discovered += 1
                    continue
            if match:
                filename, display = match
                if filename not in seen:
                    node["articles"].append({
                        "target": display,
                        "display": display,
                        "filename": filename,
                        "emphasized": emph,
                    })
                    seen.add(filename)
                    discovered += 1
            else:
                unmatched_entries.append((raw_name, node.get("name", "")))

    print(f"  {discovered:,} matched, {len(unmatched_entries):,} unmatched")
    import os as _os
    if _os.environ.get("DUMP_UNMATCHED"):
        from pathlib import Path as _P
        _P("tools/_scratch").mkdir(parents=True, exist_ok=True)
        _P("tools/_scratch/unmatched.json").write_text(
            json.dumps(unmatched_entries, ensure_ascii=False), encoding="utf-8")

    # ── Intra-cat dedup ───────────────────────────────────────────
    total_removed = 0
    for cat in toc:
        seen_in_cat: set[str] = set()

        def _dedup(node: dict):
            nonlocal total_removed
            keep = []
            for a in node.get("articles", []):
                fn = a.get("filename")
                if fn:
                    if fn in seen_in_cat:
                        total_removed += 1
                        continue
                    seen_in_cat.add(fn)
                keep.append(a)
            node["articles"] = keep
            for c in node.get("children", []):
                _dedup(c)

        for s in cat["subsections"]:
            _dedup(s)

    if total_removed:
        print(f"  Post-dedup: removed {total_removed} intra-cat duplicates")

    return {"discovered": discovered, "unmatched": len(unmatched_entries)}


# ── Main ──────────────────────────────────────────────────────────────

def main() -> None:
    print("Loading meta-TOC categories...")
    categories = load_meta_toc_categories()
    print(f"  {len(categories)} top-level categories found")
    for c in categories:
        page = c.get("printed_page")
        page_str = f" (p. {page})" if page else ""
        print(f"    \u2022 {c['name']}{page_str}")

    meta_entries = load_meta_toc_entries()
    toc = build_toc_from_meta(categories, meta_entries)

    print()
    print("Loading article index...")
    article_index = json.loads(ARTICLES_INDEX.read_text(encoding="utf-8"))
    n_articles = sum(1 for a in article_index
                     if a.get("article_type") == "article")
    print(f"  {n_articles:,} articles")

    print()
    print("Walking vision-OCR pages and attributing articles...")
    print(f"  ({len(meta_entries)} meta-TOC entries; "
          f"{sum(len(c['subsections']) for c in toc)} canonical buckets)")
    stats = walk_and_attribute(toc, meta_entries, article_index)

    # ── Report ────────────────────────────────────────────────────

    def _count(node: dict) -> tuple[int, int, int, int]:
        nodes = 1
        arts = len(node.get("articles", []))
        resolved = sum(1 for a in node.get("articles", [])
                       if a.get("filename"))
        empty_leaves = 0
        children = node.get("children", [])
        if not children and arts == 0:
            empty_leaves = 1
        for c in children:
            cn, ca, cr, ce = _count(c)
            nodes += cn
            arts += ca
            resolved += cr
            empty_leaves += ce
        return nodes, arts, resolved, empty_leaves

    print()
    print("Per-category coverage (nodes = total incl. children):")
    total_empty = 0
    for cat in toc:
        n_subs, n_arts, n_resolved, empty = 0, 0, 0, 0
        for s in cat["subsections"]:
            ns, na, nr, ne = _count(s)
            n_subs += ns
            n_arts += na
            n_resolved += nr
            empty += ne
        total_empty += empty
        print(f"  {cat['name'][:40]:40s} {n_subs:4d} nodes, "
              f"{n_arts:5d} arts, {n_resolved:5d} resolved, "
              f"{empty:3d} empty leaves")
    print(f"\nTotal empty leaves: {total_empty}")

    # ── Write output ──────────────────────────────────────────────
    intro = load_classified_toc_intro()
    out_obj: dict = {"categories": toc}
    if intro:
        out_obj["intro_html"] = intro

    CAT_TOC_DIR = Path("data/derived/cat_toc")
    CAT_TOC_DIR.mkdir(parents=True, exist_ok=True)
    for cat in toc:
        slug = re.sub(r"[^a-z0-9]+", "_", cat["name"].lower()).strip("_")
        cat_path = CAT_TOC_DIR / f"{slug}.json"
        cat_path.write_text(json.dumps(cat, indent=2, ensure_ascii=False),
                            encoding="utf-8")
    print(f"  Per-cat TOCs written to {CAT_TOC_DIR}/")

    OUT.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    print(f"\nDone. Wrote {OUT}")


if __name__ == "__main__":
    main()

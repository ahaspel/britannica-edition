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
            m2 = re.match(r"^(\d{3})$", c.strip())
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


# Flat-in-meta-TOC cats with known body-page sub-headings.
# Each sub is either a string (leaf sub) or a dict with {name, children}.
_FLAT_CAT_SUBS: dict[str, list] = {
    "Anthropology and Ethnology": [
        "General Subjects and Terms", "Races and Tribes, &c.", "Biographies",
    ],
    "Archaeology and Antiquities": ["Subjects", "Biographies"],
    "Astronomy": ["Subjects", "Biographies"],
    "Education": ["Subjects", "Biographies"],
    "Language and Writing": ["General", "Biographies"],
    "Mathematics": ["Pure", "Applied", "Biographies"],
    "Military and Naval": ["Subjects", "Biographies"],
    "Philosophy and Psychology": [
        "General", "Subjects", "Biographies",
        {"name": "Psychical Research and Occultism",
         "children": ["Subjects", "Biographies"]},
    ],
    "Sports and Pastimes": ["Subjects", "Biographies"],
}


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
            hard_subs = _FLAT_CAT_SUBS.get(name, [])
            def _make_node(spec, printed_page):
                if isinstance(spec, str):
                    return {
                        "name": spec,
                        "printed_page": printed_page,
                        "articles": [],
                        "children": [],
                    }
                return {
                    "name": spec["name"],
                    "printed_page": printed_page,
                    "articles": [],
                    "children": [
                        _make_node(ch, printed_page)
                        for ch in spec.get("children", [])
                    ],
                }
            subs = [_make_node(s, c.get("printed_page")) for s in hard_subs]
            toc.append({"name": name, "subsections": subs})
            continue
        subsections: list[dict] = []
        parent_at_level: dict[int, dict] = {}
        for e in entries:
            node = {
                "name": e.get("name") or "",
                "printed_page": e.get("printed_page"),
                "articles": [],
                "children": [],
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
        toc.append({"name": name, "subsections": subsections})
    return toc


# ── Walk & attribute ─────────────────────────────────────────────────

# Known aliases: body-text form → meta-TOC canonical form (normalized).
_SUB_ALIASES: dict[str, str] = {
    "servia": "serbia",
    "mammalia": "mammals",
    "bird": "birds",
    "insect": "insects",
    "batrachia": "batrachians",
    "divisionsandtowns": "divisionandtowns",
    "saint": "saints",
    "indochinafrench": "indochlnafrench",
    "mediterraneanislandsetc": "mediterraneanislandsc",
    "ancientgeography": "ancientgoography",
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
                y_clean = re.sub(r"\s*\(.*?\)", "", y_clean).strip()
                if y_clean:
                    y_norm = _normalize(y_clean)
                    for child in parent.get("children", []):
                        for form in {child["name"],
                                     _strip_parens(child["name"])}:
                            if _normalize(form) == y_norm:
                                return child
                        # Singular/plural on child name.
                        cn = _normalize(_strip_parens(child["name"]))
                        if cn + "s" == y_norm or (
                            y_norm.endswith("s") and y_norm[:-1] == cn
                        ):
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

            # Detect ## Blackletter header.
            is_header = line.startswith("## ")
            if is_header:
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
                norm = _normalize(line)
                if norm in cat_by_norm:
                    cat_dict = cat_by_norm[norm]
                    cur_cat = cat_dict["name"]
                    subs = cat_dict.get("subsections", [])
                    cur_sub = _first_leaf(subs[0]) if subs else None
                    continue
                # ## line didn't match a cat — try as sub.
                if cur_cat:
                    new_sub = _match_sub(cur_cat, line, cur_sub)
                    if new_sub:
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
                        if leaf is not cur_sub:
                            cur_sub = leaf
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
                # Dehyphenate wrapped titles: "Schellen-dorf" → "Schellendorf"
                if "-" in raw_name:
                    dehyphed = re.sub(r"(\w)-(\w)", r"\1\2", raw_name)
                    match = title_lookup.get(_art_norm(dehyphed))
                    if not match:
                        # Also try comma-split after dehyphenation
                        comma2 = dehyphed.split(",", 1)[0].strip()
                        if comma2 != dehyphed and len(comma2) >= 4:
                            match = title_lookup.get(_art_norm(comma2))
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
                unmatched_entries.append(raw_name)

    print(f"  {discovered:,} matched, {len(unmatched_entries):,} unmatched")

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

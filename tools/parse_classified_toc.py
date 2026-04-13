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
  • Meta-TOC (ws 889-890): the 24 top-level category names
  • Body pages (ws 891-955): Blackletter category headers, subsection
    headers (<big>{{c|'''X'''}}</big>), and {{EB1911 lkpl|Target}}
    or {{EB1911 lkpl|Target|Display}} article links

Untranscribed pages (ws 895-947 partly OCR-only) yield no entries —
those subsections show as empty until Wikisource transcribes them.
"""
import io
import json
import os
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

# Vol 29 ws→printed offset: ws 891 = printed 883 → offset = 8.
VOL29_OFFSET = 8

# Article titles shorter than this aren't worth substring-matching
# in noisy OCR — too many false positives.
MIN_TITLE_LEN = 6


def load_meta_toc_entries() -> list[dict]:
    """Parse the full meta-TOC (ws 889-890) into a flat list of
    entries with hierarchy info. Each entry has:
      - level: 1 (Roman) | 2 (Arabic) | 3 (letter) | 4 (numeric)
      - name: the displayed label
      - top_cat: the level-1 category this entry belongs under
      - sub_label: human-readable subcategory path
        (e.g. "Botany — Systematic" or "Architecture")
      - printed_page: the page number from the right column
    """
    text = ""
    for ws in (889, 890):
        path = VOL29_DIR / f"vol29-page{ws:04d}.json"
        if not path.exists():
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        text += d.get("raw_text", "") + "\n"
    text = re.sub(r"<noinclude>.*?</noinclude>", "", text, flags=re.DOTALL)

    entries: list[dict] = []
    rows = re.split(r"\n\|-[^\n]*\n", text)
    # Track current top_cat / arabic-level / letter-level labels.
    cur_top = ""
    cur_arabic = ""
    cur_letter = ""

    for row in rows:
        # Determine level + name
        level = None
        name = ""
        # Level 1: '''X.''' Roman bold
        if re.search(r"'''[IVXLCDM]+\.'''", row):
            m = re.search(r"colspan=\d+\s*\|\s*'''([^']+)'''", row)
            if not m:
                continue
            level = 1
            name = m.group(1).strip()
            cur_top = name
            cur_arabic = ""
            cur_letter = ""
        # Level 4: |  ||  || \n| {{ts|ar}} | (N) \n| LABEL  (numeric)
        elif re.search(r"\|\s*\(\d+\)", row) and row.lstrip().startswith("|") \
                and row.count("||") >= 2:
            num_m = re.search(r"\|\s*\((\d+)\)\s*\n\|\s*([^|\n]+)", row)
            if not num_m:
                continue
            level = 4
            name = num_m.group(2).strip()
        # Level 3: |  || \n| ...(letter)... \n| LABEL
        elif re.search(r"\(''[a-z]''\)|^\|\s*\([a-z]\)", row, re.MULTILINE):
            let_m = re.search(
                r"\(''?([a-z])''?\)\s*\n(?:\|\s*colspan=\d+\s*)?\|\s*([^|\n]+)",
                row,
            )
            if not let_m:
                continue
            level = 3
            name = let_m.group(2).strip()
            cur_letter = name
        # Level 2: | (no leading empty) \n| {{ts|ar}} | N. \n| LABEL
        elif re.search(r"\|\s*\d+\.(?!\d)", row):
            ar_m = re.search(
                r"\|\s*(\d+)\.\s*\n\|\s*colspan=\d+\s*\|\s*([^|\n]+)", row,
            )
            if not ar_m:
                continue
            level = 2
            name = ar_m.group(2).strip()
            cur_arabic = name
            cur_letter = ""
        else:
            continue

        # Strip trailing parenthetical notes from name
        name = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
        if not name:
            continue

        # Right-most numeric cell is the printed page reference
        page_m = re.findall(r"\|\s*(\d{3,4})\s*(?:\n|$)", row)
        page = int(page_m[-1]) if page_m else None

        # Build human-readable sub_label
        if level == 1:
            sub_label = ""  # top-level itself
        elif level == 2:
            sub_label = name
        elif level == 3:
            sub_label = f"{cur_arabic} \u2014 {name}" if cur_arabic else name
        elif level == 4:
            base = cur_letter or cur_arabic
            sub_label = f"{base} \u2014 {name}" if base else name
        else:
            sub_label = name

        entries.append({
            "level": level,
            "name": name,
            "top_cat": cur_top,
            "sub_label": sub_label,
            "printed_page": page,
        })

    # Repair typos: printed pages must be monotonically non-decreasing
    # within each top-level category.
    last_top = ""
    last_good = 0
    for e in entries:
        if e["level"] == 1:
            last_top = e["top_cat"]
            last_good = e["printed_page"] or 0
            continue
        if e["top_cat"] != last_top:
            last_top = e["top_cat"]
            last_good = 0
        p = e.get("printed_page")
        if p is None:
            continue
        if p < last_good:
            e["printed_page"] = last_good
        else:
            last_good = p

    # Also enforce monotonic across top-level categories.
    last_good = 0
    for e in entries:
        if e["level"] != 1:
            continue
        p = e.get("printed_page")
        if p is None:
            continue
        if p < last_good:
            e["printed_page"] = last_good + 1
        else:
            last_good = p

    return entries


def load_meta_toc_categories() -> list[dict]:
    """Backwards-compatible: just the level-1 entries."""
    return [
        {"name": e["name"], "printed_page": e["printed_page"]}
        for e in load_meta_toc_entries() if e["level"] == 1
    ]


def collect_body_pages() -> list[tuple[int, str]]:
    """Return (ws_page, raw_text) for every classified-TOC body page
    (ws 891-955), in order."""
    pages: list[tuple[int, str]] = []
    for ws in range(891, 956):
        path = VOL29_DIR / f"vol29-page{ws:04d}.json"
        if not path.exists():
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        raw = d.get("raw_text", "").strip()
        if raw:
            pages.append((ws, raw))
    return pages


# Category header pattern: {{Blackletter|Name}} or {{bl|Name}}
_CAT_HEADER_RE = re.compile(
    r"\{\{(?:Blackletter|bl)\|([^{}|]+?)\}\}", re.IGNORECASE,
)

# Subsection header: <big>{{c|'''Name'''}}</big>  OR
#                   <big>{{center|'''Name'''}}</big>  OR
#                   {{big|{{c|'''Name'''}}}}
# Tolerate trailing colon and any nested formatting.
_SUBSEC_RE = re.compile(
    r"(?:<big>\s*\{\{(?:c|center)\||\{\{big\s*\|\s*\{\{(?:c|center)\|)"
    r"\s*'''([^']+)'''",
    re.IGNORECASE,
)

# Article entry: {{EB1911 lkpl|Target}} or {{EB1911 lkpl|Target|Display}}
# Optionally wrapped in '''...''' for emphasis.
_LKPL_RE = re.compile(
    r"(''')?(?:''')?\{\{EB1911\s+lkpl\|([^{}|]+?)(?:\|([^{}]+?))?\}\}",
    re.IGNORECASE,
)


def _normalize(s: str) -> str:
    """For category-header matching: lowercase, alphanumerics only."""
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def parse_category_body(text: str) -> list[dict]:
    """Extract subsection list (with article entries) from a body
    page's wikitext after a category Blackletter header. Splits by
    subsequent subsection headers."""
    # Split text by subsection header. Anything before the first
    # subsection (intro, see-also note) goes in a synthetic "" subsec.
    splits = list(_SUBSEC_RE.finditer(text))
    if not splits:
        # No explicit subsections — treat all lkpl as one unnamed group.
        articles = [_parse_article(m) for m in _LKPL_RE.finditer(text)]
        return ([{"name": "", "articles": articles}] if articles else [])

    sections: list[dict] = []
    # Intro (before first subsection): include if it has any lkpl
    intro_text = text[:splits[0].start()]
    intro_arts = [_parse_article(m) for m in _LKPL_RE.finditer(intro_text)]
    if intro_arts:
        sections.append({"name": "", "articles": intro_arts})

    for i, m in enumerate(splits):
        name = m.group(1).strip()
        sec_start = m.end()
        sec_end = splits[i + 1].start() if i + 1 < len(splits) else len(text)
        sec_text = text[sec_start:sec_end]
        articles = [_parse_article(am) for am in _LKPL_RE.finditer(sec_text)]
        sections.append({"name": name, "articles": articles})

    return sections


def _parse_article(m: re.Match) -> dict:
    """Build an article entry from an _LKPL_RE match."""
    target = m.group(2).strip()
    display = (m.group(3) or m.group(2)).strip()
    return {
        "target": target,
        "display": display,
        "emphasized": bool(m.group(1)),
    }


def resolve_article_filenames(toc: list[dict],
                              article_index: list[dict]) -> dict:
    """Add `filename` to each article entry whose target matches an
    existing article. First tries exact (uppercased) title match; if
    that fails, falls back to the same fuzzy-resolution strategies
    used for cross-references."""
    from britannica.xrefs.scoring import find_fuzzy_match

    # title_map maps uppercased title → article_index entry index
    # (find_fuzzy_match expects int values; we'll use them as
    # indices to recover filenames after).
    title_map: dict[str, int] = {}
    by_idx: list[dict] = []
    for e in article_index:
        if e.get("article_type") != "article":
            continue
        upper = e["title"].strip().upper()
        if upper not in title_map:
            title_map[upper] = len(by_idx)
            by_idx.append(e)

    total = 0
    exact = 0
    fuzzy = 0
    for cat in toc:
        for sub in cat["subsections"]:
            for art in sub["articles"]:
                total += 1
                target_upper = art["target"].strip().upper()
                idx = title_map.get(target_upper)
                if idx is not None:
                    art["filename"] = by_idx[idx]["filename"]
                    exact += 1
                    continue
                # Fuzzy fallback
                idx = find_fuzzy_match(target_upper, title_map)
                if idx is not None:
                    art["filename"] = by_idx[idx]["filename"]
                    fuzzy += 1
    return {"total": total, "exact": exact, "fuzzy": fuzzy,
            "resolved": exact + fuzzy}


def _ocr_norm(s: str) -> str:
    """Normalize a string for noisy-OCR substring matching: uppercase,
    drop accents, collapse anything not A-Z to single spaces."""
    s = s.upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Z]+", " ", s)
    return f" {s.strip()} "  # pad for boundary matching


# ── Recursive boundary-detection parser ────────────────────────────────

# Top-level category marker in OCR text: e.g. "BIOLOGY]" or "ART}"
# at the start of a line — the running header. The bracket may be a
# misrecognized "}" or ")" too. Allow text following (e.g. "ART]
# CLASSIFIED LIST OF ARTICLES").
_OCR_TOP_RE = re.compile(r"^([A-Z][A-Z &]{2,})[\]\}\)]")

# Subsection header in OCR text: e.g. "Botany : Natural History (cont.)",
# "Zoology, Systematic : Znvertebrata", "France : Biographies".
# Heuristic: line with `Word : Word`, where the words are short and
# Title Case.
_OCR_SUB_RE = re.compile(
    r"^([A-Z][A-Za-z' \-]+?)\s*:\s*([A-Z][A-Za-z' \-]+?)"
    r"(\s*\([Cc]ont[\.\)]?[\.)]?)?\s*$"
)

# Region marker in OCR text: e.g. "EUROPE—COUNTRIES (cont.)"
_OCR_REGION_RE = re.compile(
    r"^([A-Z][A-Z]{2,}(?:[\u2014\u2013\-][A-Z]{2,})+)(\s*\([Cc]ont[\.\)]?[\.)]?)?\s*$"
)

# Wikisource Blackletter top-level header
_WS_TOP_RE = re.compile(r"\{\{(?:Blackletter|bl)\|([^{}|]+?)\}\}", re.IGNORECASE)
# Wikisource subsection header inside <big>{{c|'''X'''}}</big> etc.
_WS_SUB_RE = re.compile(
    r"(?:<big>\s*\{\{(?:c|center)\||\{\{big\s*\|\s*\{\{(?:c|center)\||"
    r"\{\{(?:larger|center)\|)"
    r"\s*'''([^']+)'''",
    re.IGNORECASE,
)


def _normalize_cat_name(name: str) -> str:
    """Map a top-level marker found in text to a meta-TOC category
    name (or itself if it looks like a category)."""
    return _normalize(name)


def dump_category_boundaries(meta_categories: list[dict],
                             out_path: Path) -> None:
    """Emit a human-readable map of which lines on which vol-29 ws
    pages belong to which top-level category. Useful for verifying
    boundary detection independently of article matching."""
    if OCR_FILE.exists():
        ocr_data = json.loads(OCR_FILE.read_text(encoding="utf-8"))
    else:
        ocr_data = {}

    # Reuse the same cat-resolver logic as the recursive parser
    cat_canonical: dict[str, str] = {}
    for c in meta_categories:
        cat_canonical[_normalize(c["name"])] = c["name"]
    cat_norm_keys = list(cat_canonical.keys())
    import difflib

    def find_cat(name: str) -> str | None:
        key = _normalize(name)
        if key in cat_canonical:
            return cat_canonical[key]
        for k in cat_norm_keys:
            if k.startswith(key) and len(key) >= 4:
                return cat_canonical[k]
        close = difflib.get_close_matches(key, cat_norm_keys, n=1, cutoff=0.6)
        return cat_canonical[close[0]] if close else None

    cat_anchors: dict[int, str] = {}
    for c in meta_categories:
        if c.get("printed_page"):
            ws = c["printed_page"] + VOL29_OFFSET
            cat_anchors.setdefault(ws, c["name"])
    sorted_anchor_ws = sorted(cat_anchors)
    meta_cat_for_ws: dict[int, str] = {}
    if sorted_anchor_ws:
        active = cat_anchors[sorted_anchor_ws[0]]
        anchor_idx = 0
        for ws in range(sorted_anchor_ws[0], 956):
            while (anchor_idx + 1 < len(sorted_anchor_ws)
                   and sorted_anchor_ws[anchor_idx + 1] <= ws):
                anchor_idx += 1
                active = cat_anchors[sorted_anchor_ws[anchor_idx]]
            meta_cat_for_ws[ws] = active

    # Walk all body lines, recording (ws, line_idx, line_text, cur_cat).
    # Detect transitions and group into runs.
    runs: list[dict] = []
    cur_cat: str | None = None
    run_start: tuple[int, int] | None = None
    sample_first: str = ""
    sample_last: str = ""
    line_count_in_run = 0

    def _flush_run(cat: str | None, end_ws: int, end_line: int):
        nonlocal sample_first, sample_last, line_count_in_run
        if cat is None or run_start is None:
            return
        runs.append({
            "cat": cat,
            "start_ws": run_start[0], "start_line": run_start[1],
            "end_ws": end_ws, "end_line": end_line,
            "lines": line_count_in_run,
            "sample_first": sample_first[:100],
            "sample_last": sample_last[:100],
        })
        sample_first = ""
        sample_last = ""
        line_count_in_run = 0

    for ws in range(891, 956):
        text = ""
        path = VOL29_DIR / f"vol29-page{ws:04d}.json"
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
            text = d.get("raw_text", "").strip()
        is_wikisource = bool(text)
        if not text:
            text = ocr_data.get(str(ws), "")
        if not text.strip():
            continue

        meta_cat = meta_cat_for_ws.get(ws)
        if meta_cat and meta_cat != cur_cat:
            _flush_run(cur_cat, ws, 0)
            cur_cat = meta_cat
            run_start = (ws, 0)

        for line_idx, raw_line in enumerate(text.split("\n")):
            line = raw_line.strip()
            if not line:
                continue

            new_top = None
            if is_wikisource:
                m = _WS_TOP_RE.search(line)
                if m:
                    new_top = find_cat(m.group(1))
            if not new_top:
                m = _OCR_TOP_RE.match(line)
                if m and len(m.group(1).split()) <= 4:
                    new_top = find_cat(m.group(1))
            if not new_top:
                tokens_m = re.match(r"^((?:[A-Z][a-z]+\s*){1,3})", line)
                if tokens_m:
                    candidate_full = tokens_m.group(1).strip()
                    parts = candidate_full.split()
                    for n in range(min(3, len(parts)), 0, -1):
                        cand = " ".join(parts[:n])
                        cand_norm = _normalize(cand)
                        if cand_norm in cat_canonical:
                            new_top = cat_canonical[cand_norm]
                            break
                        if len(cand_norm) >= 5:
                            for k in cat_norm_keys:
                                if k == cand_norm or (
                                    k.startswith(cand_norm)
                                    and len(k) - len(cand_norm) <= 12
                                ):
                                    new_top = cat_canonical[k]
                                    break
                            if new_top:
                                break

            if new_top and new_top != cur_cat:
                _flush_run(cur_cat, ws, line_idx)
                cur_cat = new_top
                run_start = (ws, line_idx)

            if cur_cat is not None:
                if not sample_first:
                    sample_first = line
                sample_last = line
                line_count_in_run += 1

    _flush_run(cur_cat, 955, 0)

    # Emit summary, grouped by category
    by_cat: dict[str, list[dict]] = {}
    for r in runs:
        by_cat.setdefault(r["cat"], []).append(r)

    lines: list[str] = []
    lines.append("# Vol 29 classified-TOC category boundaries")
    lines.append("# Detected by recursive walker. Each run = a contiguous")
    lines.append("# region attributed to one top-level category.\n")
    for c in meta_categories:
        cat_name = c["name"]
        cat_runs = by_cat.get(cat_name, [])
        total = sum(r["lines"] for r in cat_runs)
        lines.append(f"=== {cat_name} ({total} lines, {len(cat_runs)} runs) ===")
        if not cat_runs:
            lines.append("  (no content detected)\n")
            continue
        for r in cat_runs:
            span = (f"ws {r['start_ws']}.{r['start_line']}"
                    f" \u2192 ws {r['end_ws']}.{r['end_line']}")
            lines.append(f"  {span}  ({r['lines']} lines)")
            lines.append(f"    first: {r['sample_first']!r}")
            lines.append(f"    last:  {r['sample_last']!r}")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def parse_vol29_recursive(article_index: list[dict],
                          meta_categories: list[dict]) -> dict:
    """Walk all vol-29 body pages line by line, tracking current
    top-level category and subcategory based on header markers
    found in the text. For each line, scan for known article title
    matches and attribute them to (top_cat, sub_label).

    Returns: {top_cat: {sub_label: set of (filename, display)}}.
    """
    if OCR_FILE.exists():
        ocr_data = json.loads(OCR_FILE.read_text(encoding="utf-8"))
    else:
        ocr_data = {}

    # Build title lookup (same as before).
    title_lookup: dict[str, tuple[str, str]] = {}
    for e in article_index:
        if e.get("article_type") != "article":
            continue
        norm = _ocr_norm(e["title"]).strip()
        if len(norm.replace(" ", "")) < MIN_TITLE_LEN:
            continue
        norm_padded = f" {norm} "
        if norm_padded not in title_lookup:
            title_lookup[norm_padded] = (e["filename"], e["title"])

    # Map normalized cat name → canonical meta-TOC name (so OCR-detected
    # "EDUCATION" maps to "Education")
    cat_canonical: dict[str, str] = {}
    for c in meta_categories:
        cat_canonical[_normalize(c["name"])] = c["name"]
    # Also accept fuzzy matches
    import difflib
    cat_norm_keys = list(cat_canonical.keys())

    def find_cat(name: str) -> str | None:
        key = _normalize(name)
        if key in cat_canonical:
            return cat_canonical[key]
        # Prefix match: OCR often gives just the abbreviated form
        # (e.g. "LANGUAGE" matches "Language and Writing").
        for k in cat_norm_keys:
            if k.startswith(key) and len(key) >= 4:
                return cat_canonical[k]
        close = difflib.get_close_matches(key, cat_norm_keys, n=1, cutoff=0.6)
        return cat_canonical[close[0]] if close else None

    # Build meta-TOC ws → top-cat anchor map. At each ws page boundary
    # we set cur_cat from this map (then OCR headers on the page can
    # refine within). This handles categories like Astronomy where
    # OCR doesn't recognize the top-cat header.
    cat_anchors: dict[int, str] = {}
    for c in meta_categories:
        if c.get("printed_page"):
            ws = c["printed_page"] + VOL29_OFFSET
            # First-wins so shared printed pages keep the first cat.
            cat_anchors.setdefault(ws, c["name"])

    # Carry forward: each ws inherits the most-recent anchor's cat.
    if cat_anchors:
        sorted_anchor_ws = sorted(cat_anchors)
        meta_cat_for_ws: dict[int, str] = {}
        active = cat_anchors[sorted_anchor_ws[0]]
        anchor_idx = 0
        for ws in range(sorted_anchor_ws[0], 956):
            while (anchor_idx + 1 < len(sorted_anchor_ws)
                   and sorted_anchor_ws[anchor_idx + 1] <= ws):
                anchor_idx += 1
                active = cat_anchors[sorted_anchor_ws[anchor_idx]]
            meta_cat_for_ws[ws] = active
    else:
        meta_cat_for_ws = {}

    discovered: dict[str, dict[str, set]] = {}
    cur_cat: str | None = None
    cur_sub: str = ""

    for ws in range(891, 956):
        # At each ws page, default cur_cat to the meta-TOC anchor.
        # OCR-detected top markers (below) can override within the page.
        meta_cat = meta_cat_for_ws.get(ws)
        if meta_cat and meta_cat != cur_cat:
            cur_cat = meta_cat
            cur_sub = ""
        # Prefer Wikisource raw text (cleaner)
        text = ""
        path = VOL29_DIR / f"vol29-page{ws:04d}.json"
        if path.exists():
            d = json.loads(path.read_text(encoding="utf-8"))
            text = d.get("raw_text", "").strip()
        is_wikisource = bool(text)
        if not text:
            text = ocr_data.get(str(ws), "")
        if not text.strip():
            continue

        for raw_line in text.split("\n"):
            line = raw_line.strip()
            if not line:
                continue

            # ── Detect top-level category marker ──
            new_top = None
            if is_wikisource:
                m = _WS_TOP_RE.search(line)
                if m:
                    new_top = find_cat(m.group(1))
            if not new_top:
                m = _OCR_TOP_RE.match(line)
                if m and len(m.group(1).split()) <= 4:
                    new_top = find_cat(m.group(1))
            if not new_top:
                # Plain category name appearing as a column header in
                # OCR text (e.g. "Astronomy Eccentric Metonic cycle..."
                # where "Astronomy" is the column-merged column header
                # of a new category). Try the first 1, 2, or 3 words.
                tokens_m = re.match(r"^((?:[A-Z][a-z]+\s*){1,3})", line)
                if tokens_m:
                    candidate_full = tokens_m.group(1).strip()
                    parts = candidate_full.split()
                    # Try progressively shorter prefixes
                    for n in range(min(3, len(parts)), 0, -1):
                        cand = " ".join(parts[:n])
                        cand_norm = _normalize(cand)
                        if cand_norm in cat_canonical:
                            new_top = cat_canonical[cand_norm]
                            break
                        # Prefix match (e.g. "Mathematics" → "Mathematics")
                        if len(cand_norm) >= 5:
                            for k in cat_norm_keys:
                                if k == cand_norm or (
                                    k.startswith(cand_norm)
                                    and len(k) - len(cand_norm) <= 12
                                ):
                                    new_top = cat_canonical[k]
                                    break
                            if new_top:
                                break
            if new_top and new_top != cur_cat:
                cur_cat = new_top
                cur_sub = ""
                continue

            # ── Detect subsection header ──
            new_sub = None
            if is_wikisource:
                ms = _WS_SUB_RE.search(line)
                if ms:
                    new_sub = ms.group(1).strip()
            if not new_sub:
                ms = _OCR_SUB_RE.match(line)
                if ms:
                    name1, name2, _ = ms.groups()
                    new_sub = f"{name1.strip()} \u2014 {name2.strip()}"
                else:
                    mr = _OCR_REGION_RE.match(line)
                    if mr:
                        new_sub = mr.group(1).strip()
            if new_sub:
                cur_sub = new_sub
                continue

            # ── Article matching within current (cat, sub) region ──
            if cur_cat is None:
                continue
            norm_line = _ocr_norm(line)
            for title_norm, (filename, display) in title_lookup.items():
                if title_norm in norm_line:
                    discovered.setdefault(cur_cat, {}).setdefault(
                        cur_sub, set()).add((filename, display))

    return discovered


def enrich_with_ocr(toc: list[dict],
                    cat_pages: list[dict],
                    article_index: list[dict],
                    meta_entries: list[dict] | None = None) -> dict:
    """For categories whose body pages lack Wikisource transcription,
    scan the OCR text of those pages for occurrences of known article
    titles. Each title found is added to the category as a discovered
    article."""
    if not OCR_FILE.exists():
        return {"discovered": 0}
    ocr_data = json.loads(OCR_FILE.read_text(encoding="utf-8"))

    # Build (normalized title) → (filename, original title) lookup.
    # Skip too-short titles.
    title_lookup: dict[str, tuple[str, str]] = {}
    for e in article_index:
        if e.get("article_type") != "article":
            continue
        norm = _ocr_norm(e["title"]).strip()
        if len(norm.replace(" ", "")) < MIN_TITLE_LEN:
            continue
        norm_padded = f" {norm} "
        if norm_padded not in title_lookup:
            title_lookup[norm_padded] = (e["filename"], e["title"])

    # Build ws → category-name map from cat_pages printed_page anchors.
    sorted_cats = sorted(
        [c for c in cat_pages if c.get("printed_page")],
        key=lambda x: x["printed_page"],
    )
    # Bound: classified TOC body ends around ws 956. Beyond that is
    # the Contributors list — don't sweep those into Miscellaneous.
    CLASSIFIED_END_WS = 955
    # Each ws may map to multiple (top_cat, sub_label) anchors so
    # discoveries land in their best subcategory. Use meta_entries
    # if available (level 2-4 anchors); fall back to top-level only.
    # Build sorted list of (printed_page, top_cat, sub_label).
    if meta_entries:
        anchors = [
            (e["printed_page"], e["top_cat"], e["sub_label"])
            for e in meta_entries if e.get("printed_page")
        ]
    else:
        anchors = [
            (c["printed_page"], c["name"], "") for c in sorted_cats
        ]
    anchors.sort(key=lambda x: x[0])

    # For each ws, find ALL anchors whose printed_page maps to it,
    # PLUS the most-recent anchor for each top_cat (continuation).
    ws_to_assignments: dict[int, list[tuple[str, str]]] = {}

    # Walk through ws pages in order. Each ws gets the assignments of
    # all anchors whose printed_page maps to it directly, OR a
    # carry-forward of the LAST set of anchors when no new anchor
    # starts here (the assignment persists until a newer anchor
    # supersedes it).
    starts_at_ws: dict[int, list[tuple[str, str]]] = {}
    for printed, top_cat, sub_label in anchors:
        ws = printed + VOL29_OFFSET
        starts_at_ws.setdefault(ws, []).append((top_cat, sub_label))

    if anchors:
        first_ws = min(starts_at_ws)
        active: list[tuple[str, str]] = []
        for ws in range(first_ws, CLASSIFIED_END_WS + 1):
            if ws in starts_at_ws:
                # Replace the active set (don't accumulate forever).
                active = list(starts_at_ws[ws])
            if active:
                ws_to_assignments[ws] = active

    # Scan each ws page in any category's range. Prefer Wikisource
    # raw_text (cleaner) but fall back to OCR. Run fuzzy substring
    # matching either way — Wikisource transcribers sometimes wrote
    # article names as plain text instead of {{EB1911 lkpl|…}}
    # templates (e.g. Physics on ws 948), in which case the lkpl
    # parser misses them but substring matching still catches them.
    # New recursive boundary-detection approach: walk vol-29 body line
    # by line, tracking current top-level category and subsection from
    # headers found in the text. Article matches are attributed to
    # the (cat, sub) active at that line — bounded by the surrounding
    # subsection headers, not by guessed page ranges.
    discovered = parse_vol29_recursive(article_index, sorted_cats)

    # Inject discovered articles into the toc, grouped by sub_label.
    # Don't re-add articles already in the category from Wikisource's
    # lkpl extraction.
    total_discovered = 0
    for cat in toc:
        if cat["name"] not in discovered:
            continue
        existing_filenames = {
            a.get("filename") for s in cat["subsections"]
            for a in s["articles"] if a.get("filename")
        }
        for sub_label, articles_set in discovered[cat["name"]].items():
            new_arts = sorted(
                [(fn, dis) for fn, dis in articles_set
                 if fn not in existing_filenames],
                key=lambda x: x[1],
            )
            if not new_arts:
                continue
            total_discovered += len(new_arts)
            for fn, _ in new_arts:
                existing_filenames.add(fn)
            cat["subsections"].append({
                "name": sub_label or "General",
                "articles": [
                    {"target": dis, "display": dis, "filename": fn,
                     "emphasized": False, "from_ocr": True}
                    for fn, dis in new_arts
                ],
            })
    return {"discovered": total_discovered}


def main() -> None:
    print("Loading meta-TOC categories...")
    categories = load_meta_toc_categories()
    print(f"  {len(categories)} top-level categories found")
    for c in categories:
        page = c.get("printed_page")
        page_str = f" (p. {page})" if page else ""
        print(f"    • {c['name']}{page_str}")

    print()
    print("Collecting body pages...")
    pages = collect_body_pages()
    print(f"  {len(pages)} body pages with content")

    # Concatenate all body pages — category headers split them naturally
    all_body = "\n".join(text for _, text in pages)

    # Split body by Blackletter category headers. Each chunk belongs to
    # whatever category came first in the meta-TOC list and matches.
    print()
    print("Parsing body for categories + subsections...")
    chunks: list[tuple[str, str]] = []
    headers = list(_CAT_HEADER_RE.finditer(all_body))
    for i, m in enumerate(headers):
        name = m.group(1).strip()
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(all_body)
        chunks.append((name, all_body[start:end]))

    # Aggregate chunks by category name. Multi-page categories repeat
    # the Blackletter header on each page (e.g. Religion and Theology
    # on ws 949-953), so concatenate all matching chunks.
    import difflib
    chunk_lookup: dict[str, list[str]] = {}
    for name, body in chunks:
        chunk_lookup.setdefault(_normalize(name), []).append(body)
    chunk_lookup_joined: dict[str, str] = {
        k: "\n\n".join(v) for k, v in chunk_lookup.items()
    }

    toc: list[dict] = []
    for cat in categories:
        key = _normalize(cat["name"])
        body = chunk_lookup_joined.get(key)
        if body is None:
            close = difflib.get_close_matches(
                key, list(chunk_lookup_joined.keys()), n=1, cutoff=0.85)
            if close:
                body = chunk_lookup_joined[close[0]]
                print(f"  ~ matched {cat['name']!r} via fuzzy → {close[0]!r}")
        if body is None:
            print(f"  ! no body found for {cat['name']!r}")
            toc.append({"name": cat["name"], "subsections": []})
            continue
        subsections = parse_category_body(body)
        toc.append({"name": cat["name"], "subsections": subsections})

    print()
    print("Resolving Wikisource-parsed article references...")
    article_index = json.loads(ARTICLES_INDEX.read_text(encoding="utf-8"))
    stats = resolve_article_filenames(toc, article_index)
    pct = stats["resolved"] * 100 / stats["total"] if stats["total"] else 0
    print(f"  {stats['resolved']}/{stats['total']} ({pct:.1f}%) resolved "
          f"({stats['exact']} exact + {stats['fuzzy']} fuzzy)")

    print()
    print("Enriching with OCR for untranscribed categories...")
    meta_entries = load_meta_toc_entries()
    print(f"  ({len(meta_entries)} meta-TOC entries used as anchors)")
    ocr_stats = enrich_with_ocr(toc, categories, article_index, meta_entries)
    print(f"  {ocr_stats['discovered']} additional articles discovered via OCR")

    print()
    print("Per-category coverage:")
    for cat in toc:
        n_subs = len(cat["subsections"])
        n_arts = sum(len(s["articles"]) for s in cat["subsections"])
        n_resolved = sum(
            1 for s in cat["subsections"] for a in s["articles"]
            if a.get("filename")
        )
        print(f"  {cat['name'][:40]:40s} {n_subs:3d} subs, {n_arts:5d} arts, {n_resolved:5d} resolved")

    OUT.write_text(json.dumps({"categories": toc}, indent=2,
                              ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()

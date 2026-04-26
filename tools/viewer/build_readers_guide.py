#!/usr/bin/env python3
"""Build Reader's Guide pages from the Gutenberg HTML source.

Takes the Project Gutenberg edition of "The Reader's Guide to the
Encyclopaedia Britannica" (ebook #74039) and emits one styled HTML
page per chapter, with article references (<span class="sc">Name</span>
and alphabetical <ul class="index"> items) resolved to live links into
our article corpus where the title matches.

PROOF OF CONCEPT: currently emits only Chapter I (Farmers) so we can
judge the rendering before building out the full Guide.

Usage:
    uv run python tools/viewer/build_readers_guide.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

sys.path.insert(0, "src")
from britannica.contributors.resolver import ContributorResolver
from britannica.xrefs.scoring import find_fuzzy_match

SOURCE_HTML = Path("data/raw/readers_guide/source.html")
INDEX_JSON = Path("data/derived/articles/index.json")
CONTRIBUTORS_JSON = Path("data/derived/articles/contributors.json")
OUT_DIR = Path("tools/viewer")

# --- Title → URL map -------------------------------------------------

def load_article_indexes() -> tuple[dict[str, str], dict[int, list[dict]]]:
    """Return (title_map, by_volume).

    title_map: uppercase-title -> first-filename.
    by_volume: volume -> list of {title, filename, page_start, page_end}
    for looking up articles by (Vol. N, p. M) annotations in the
    Reader's Guide text.
    """
    data = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    title_map: dict[str, str] = {}
    by_volume: dict[int, list[dict]] = {}
    for entry in data:
        if entry.get("article_type", "article") != "article":
            continue
        title = entry.get("title")
        filename = entry.get("filename")
        if not title or not filename:
            continue
        title_map.setdefault(title.upper().strip(), filename)
        vol = entry.get("volume")
        ps = entry.get("page_start")
        pe = entry.get("page_end") or ps
        if isinstance(vol, int) and isinstance(ps, int):
            by_volume.setdefault(vol, []).append({
                "title": title.upper().strip(),
                "filename": filename,
                "page_start": ps,
                "page_end": pe,
            })
    return title_map, by_volume


def lookup_by_vol_page(
    by_volume: dict[int, list[dict]],
    vol: int,
    page: int,
    hint_title: str | None = None,
) -> str | None:
    """Return the filename of the article at (vol, page).

    If multiple articles overlap the page boundary, pick the one whose
    title best matches `hint_title` (case-insensitive substring in
    either direction). Falls back to the first overlap if no hint.
    """
    candidates = [
        a for a in by_volume.get(vol, [])
        if a["page_start"] <= page <= a["page_end"]
    ]
    if not candidates:
        return None
    if len(candidates) == 1 or not hint_title:
        return candidates[0]["filename"]
    # Score by Jaccard similarity of title words against hint words —
    # favours tight matches over titles with extra disambiguator words.
    # E.g. for hint "JOHN SMITH" at v25 p264, candidates include
    # SMITH, JOHN (perfect match) and SMITH, HENRY JOHN STEPHEN
    # (partial); Jaccard correctly picks the former.
    hint = hint_title.upper().strip()
    hint_words = set(re.findall(r"[A-Z]{2,}", hint))
    if not hint_words:
        return candidates[0]["filename"]
    scored = []
    for a in candidates:
        title_words = set(re.findall(r"[A-Z]{2,}", a["title"]))
        if not title_words:
            continue
        inter = len(hint_words & title_words)
        union = len(hint_words | title_words)
        jaccard = inter / union if union else 0.0
        scored.append((jaccard, inter, a))
    if not scored:
        return candidates[0]["filename"]
    # Sort by Jaccard desc, then by intersection size desc as tiebreaker
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return scored[0][2]["filename"]


def load_contributor_resolver() -> ContributorResolver:
    """Build a ContributorResolver from contributors.json."""
    if not CONTRIBUTORS_JSON.is_file():
        return ContributorResolver([])
    data = json.loads(CONTRIBUTORS_JSON.read_text(encoding="utf-8"))
    names = [
        c.get("full_name") for c in data
        if isinstance(c.get("full_name"), str) and c["full_name"].strip()
    ]
    return ContributorResolver(names)


# "by <NAME>" contributor citation. Captures an optional academic
# title (Prof., Dr., Sir, etc.) followed by a name that ends just
# before the next comma/semicolon/period (end of clause). The NAME
# may contain initials with trailing periods ("J. S. Flett"), which
# we differentiate from clause-terminating periods by requiring the
# terminating period to be followed by whitespace + lowercase, or
# end of line.
_BY_AUTHOR_RE = re.compile(
    r"\bby\s+"
    r"(?P<title>(?:Prof(?:essor)?\.?|Dr\.?|Mr\.?|Mrs\.?|Miss|Sir|The)\s+)?"
    r"(?P<name>[A-Z][A-Za-z.'\-]*"
    r"(?:\s+(?:[A-Z]\.(?=\s)|[A-Z][a-zé'\-]*|de|du|van|von|der|la))*"
    r"\s+[A-Z][A-Za-zé'’\-]+)"
    r"(?=[,.;]|\s+and\b|\s*$)"
)


def resolve_article_title(
    raw: str, title_map: dict[str, str]
) -> str | None:
    """Resolve an article reference to a filename using the same fuzzy
    matching used for corpus xrefs — name inversion, prefix match,
    plural/singular, trailing article/period/qualifier, etc.

    See src/britannica/xrefs/scoring.py for the full strategy list.
    """
    plain = re.sub(r"\s+", " ", raw).strip()
    if not plain:
        return None
    target = plain.upper()
    # Exact match first
    if target in title_map:
        return title_map[target]
    # Handle Palæobotany -> Palaeobotany (not currently in scoring.py;
    # cheap to pre-normalise here).
    if "Æ" in target or "æ" in plain:
        alt = target.replace("Æ", "AE")
        if alt in title_map:
            return title_map[alt]
    # Delegate to the shared fuzzy matcher. It accepts a str->int map
    # by type annotation, but the values are opaque — pass the str
    # filename and we get the same str back on match.
    return find_fuzzy_match(target, title_map)  # type: ignore[arg-type]


def filename_to_url(filename: str) -> str | None:
    """Mirror of article-urls.js filenameToUrl() (prod path)."""
    base = filename.removesuffix(".json")
    m = re.match(r"^(\d{2}-\d{4}-[a-z0-9][a-z0-9-]*?)-([^a-z0-9-].*)$", base)
    if not m:
        return None
    stable_id, title = m.group(1), m.group(2)
    return f"/article/{stable_id}/{title.lower()}"


# --- Chapter extraction ----------------------------------------------

_CHAPTER_START = re.compile(
    r'<h3 class="c001">CHAPTER ([IVXLCDM]+)<br>\s*<span class="c014">([^<]+)</span></h3>'
)


_PART_HEADER = re.compile(
    r'<h2 class="c005"><span class="sc">Part\s+\w+</span>',
    re.IGNORECASE,
)
# Full Part header: captures roman and description. Matches e.g.
#   <h2 class="c005"><span class="sc">Part I</span><br>
#     <span class="c013"><span class="sc">Courses of Reading...</span></span></h2>
_PART_FULL = re.compile(
    r'<h2 class="c005"><span class="sc">Part\s+([IVXLCDM]+)</span>'
    r'(?:<br>\s*<span[^>]*><span class="sc">([^<]+)</span></span>)?'
    r'</h2>',
    re.DOTALL,
)


def extract_all_chapters(source: str) -> dict[str, tuple[str, str]]:
    """Return {roman: (title, inner_html)} for every chapter."""
    matches = list(_CHAPTER_START.finditer(source))
    out: dict[str, tuple[str, str]] = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(source)
        body = source[start:end]
        # If a Part divider falls inside this chapter's range, the
        # chapter actually ends there — otherwise the Part heading
        # and its description get absorbed into the previous chapter.
        part_m = _PART_HEADER.search(body)
        if part_m:
            body = body[: part_m.start()]
        out[m.group(1)] = (m.group(2), body)
    return out


def extract_chapter(source: str, chapter_roman: str) -> tuple[str, str, str]:
    """Return (chapter_number, chapter_title, inner_html) for one chapter."""
    chapters = extract_all_chapters(source)
    if chapter_roman not in chapters:
        raise ValueError(f"Chapter {chapter_roman} not found")
    title, inner = chapters[chapter_roman]
    return chapter_roman, title, inner


def extract_parts(source: str) -> list[dict]:
    """Return [{roman, description, chapter_romans: [...]}, ...].

    Chapters are assigned to the Part whose header most recently
    preceded them in the source.
    """
    part_matches = list(_PART_FULL.finditer(source))
    chapter_matches = list(_CHAPTER_START.finditer(source))
    parts: list[dict] = []
    for i, pm in enumerate(part_matches):
        start = pm.end()
        end = (
            part_matches[i + 1].start()
            if i + 1 < len(part_matches)
            else len(source)
        )
        members = [
            cm.group(1)
            for cm in chapter_matches
            if start <= cm.start() < end
        ]
        parts.append({
            "roman": pm.group(1),
            "description": (pm.group(2) or "").strip(),
            "chapter_romans": members,
        })
    return parts


# Matches the chapter's alphabetical-list block:
#   <h4 class="c016">ALPHABETICAL LIST OF ARTICLES ...</h4>
#   [optional note div]
#   <ul class="index"> ... </ul>
_INDEX_LIST_RE = re.compile(
    r'<h4 class="c016">\s*([^<]*?(?:ALPHABETICAL LIST|LIST OF[^<]*?ARTICLES|PRINCIPAL ARTICLES)[^<]*?)</h4>'
    r'(?P<between>.*?)'
    r'<ul class="index[^"]*">(?P<items>.*?)</ul>',
    flags=re.DOTALL | re.IGNORECASE,
)


def find_chapter_article_list(chapter_html: str) -> str | None:
    """Return the raw HTML of a chapter's alphabetical article list,
    including the <h4> heading and any intervening <div> note, or None
    if the chapter has no such list."""
    m = _INDEX_LIST_RE.search(chapter_html)
    if not m:
        return None
    return m.group(0)


def wrap_list_in_accordion(list_block_html: str) -> str:
    """Wrap a chapter's article-list block in a <details>/<summary> so
    it's collapsed by default — keeps chapters from feeling intimidating
    while the list stays one click away."""
    m = _INDEX_LIST_RE.search(list_block_html)
    if not m:
        return list_block_html
    heading = re.sub(r"\s+", " ", m.group(1)).strip()
    items = m.group("items")
    item_count = items.count('<li class="c018">')
    # Rebuild: <details class="article-list"><summary>...</summary>
    #   <div class="note">...</div>   <ul class="index">...</ul>
    # </details>
    # Everything between the h4 and the <ul> (note/preamble) survives.
    between = m.group("between")
    ul_open_end = list_block_html.find("<ul", m.start("between") + len(between))
    ul_tag_end = list_block_html.find(">", ul_open_end) + 1
    ul_class_match = re.search(
        r'<ul class="(index[^"]*)"', list_block_html
    )
    ul_class = ul_class_match.group(1) if ul_class_match else "index"
    summary = (
        f"<summary><span class=\"list-title\">{heading}</span>"
        f"<span class=\"list-count\"> ({item_count} articles)</span></summary>"
    )
    return (
        f'<details class="article-list">{summary}'
        f"{between}"
        f'<ul class="{ul_class}">{items}</ul>'
        f"</details>"
    )


# Cross-reference paragraph inside a chapter pointing to another
# chapter's list, e.g.:
#   <p class="c007">[<i>See list of articles ... at the end of
#   Chapter III of this Guide.</i>]</p>
_XREF_LIST_RE = re.compile(
    r'<p[^>]*>\s*\[\s*<i>\s*See list of articles[^<]*?at the end of '
    r'Chapter\s+([IVXLCDM]+)[^<]*?</i>\s*\]\s*</p>',
    flags=re.DOTALL | re.IGNORECASE,
)


# --- Cleanup / transforms --------------------------------------------

def _name_variant_patterns(canonical: str) -> list[str]:
    """Generate regex alternatives matching common text forms of a
    canonical contributor name.

    "Donald Francis Tovey" -> ["Donald Francis Tovey",
       "Donald F. Tovey", "D. F. Tovey", "Donald Tovey", "D. Tovey"]
    The last-name-only form is NOT included here — that decision is
    made at the call site since it depends on whether the surname is
    unique among the contributors established in this chapter.
    """
    stripped = re.sub(
        r"^(?:(?:Prof(?:essor)?\.?|Dr\.?|Mr\.?|Mrs\.?|Miss|Sir|Rev(?:erend)?\.?|The)\s+)+",
        "",
        canonical.strip(),
        flags=re.IGNORECASE,
    )
    parts = stripped.split(" ")
    if len(parts) < 2:
        return []
    first = parts[0]
    middles = parts[1:-1]
    last = parts[-1]
    first_i = first[0] + "."
    middle_inits = [m[0] + "." for m in middles if m]
    variants: list[str] = []
    # Full spelled-out
    variants.append(" ".join([first, *middles, last]))
    if middles:
        # Middle as initial: "Donald F. Tovey"
        variants.append(" ".join([first, *middle_inits, last]))
        # All initials: "D. F. Tovey"
        variants.append(" ".join([first_i, *middle_inits, last]))
        # Dropped middle: "Donald Tovey"
        variants.append(f"{first} {last}")
    else:
        # No middle — the spelled-out "Donald Tovey" is already the full
        pass
    # First initial only: "D. Tovey"
    variants.append(f"{first_i} {last}")
    # Dedupe while preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


# Spans whose inner text we must NOT touch when linking subsequent
# contributor mentions: existing anchors and SC article-ref spans.
_PROTECTED_SPANS_RE = re.compile(
    r'<a\b[^>]*>.*?</a>|<span class="sc"[^>]*>.*?</span>',
    re.DOTALL,
)


# Table cells that begin with a (Title Case) contributor name. Used
# for "Contributors | Articles" tables (Chapter LXV "For Women" and
# any similar layout). Name runs from the cell open up to the end
# of the person's name — bounded by a parenthetical affiliation, a
# comma (e.g. trailing post-nominal letters), or the cell close.
# Leading honorifics (Mr., Mrs., Dr., Mme., Lady, …) are captured
# as part of the name so the resolver can strip them itself.
_CELL_CONTRIBUTOR_RE = re.compile(
    r'<td[^>]*>\s*'
    r"(?P<name>"
    r"(?P<hon>(?:Mr|Mrs|Ms|Miss|Dr|Prof(?:essor)?|Sir|Rev(?:erend)?"
    r"|Lady|Mme|Mlle|The)\.?\s+)?"
    # First name word: an initial ("W.") or a full name part.
    r"(?:[A-Z]\.(?=\s)|[A-Z][A-Za-zé'’\-]+)"
    # Zero or more additional tokens. Zero is OK only when a
    # honorific precedes (e.g. "Mrs. Craigie" — the honorific
    # plus surname alone is enough).
    r"(?:\s+(?:de|du|van|von|der|la|le|el|[A-Z]\.|[A-Z][A-Za-zé'’\-]+))*"
    r")"
    r"(?=\s*\(|\s*\.\s*</td>|\s*</td>|,)",
    re.UNICODE,
)


def _protect_and_run(html: str, transform) -> str:
    """Pull protected spans out of `html`, run `transform(text)`, then
    stitch the spans back in. Ensures contributor-name linking never
    overlaps with an existing anchor or article-ref."""
    protected: list[str] = []

    def stash(m: re.Match[str]) -> str:
        protected.append(m.group(0))
        return f"\x00P{len(protected) - 1}\x00"

    cleaned = _PROTECTED_SPANS_RE.sub(stash, html)
    transformed = transform(cleaned)
    return re.sub(
        r"\x00P(\d+)\x00",
        lambda m: protected[int(m.group(1))],
        transformed,
    )


def link_contributors(
    html: str,
    resolver: ContributorResolver,
) -> tuple[str, int]:
    """Two-pass contributor linking.

    Pass 1: match "by <Name>" citations, resolve via the
      ContributorResolver, and link each occurrence.
    Pass 2: for every contributor identified in pass 1, find and link
      their other mentions in the chapter (surfaces like "article by
      Donald Tovey on…" whose tail doesn't fit the pass-1 lookahead,
      or bare references like "Donald Tovey illustrates").
    """
    linked = 0
    established: dict[str, str] = {}  # canonical -> URL query string

    def pass1(m: re.Match[str]) -> str:
        nonlocal linked
        prefix = m.group(0)[: m.start("name") - m.start()]
        name = m.group("name").strip()
        clean = re.sub(r"\s+", " ", name).rstrip(".,;")
        canonical = resolver.resolve(clean)
        if not canonical:
            return m.group(0)
        linked += 1
        query = quote_plus(canonical)
        established[canonical] = query
        return f'{prefix}<a href="/contributors.html?q={query}">{name}</a>'

    html = _BY_AUTHOR_RE.sub(pass1, html)

    # Pass 1b: table cells whose leading text is a contributor name —
    # used by the "Women Contributors" table in Chapter LXV and any
    # similar "Name | Article" layouts. The name runs from the cell
    # open up to a parenthetical (their title/affiliation) or the
    # cell close.
    def pass1b(m: re.Match[str]) -> str:
        nonlocal linked
        head = m.group(0)[: m.start("name") - m.start()]
        name = m.group("name").strip().rstrip(".,;")
        # Reject single-word, un-honorific names (e.g. "Author of X")
        # — they're almost never contributor names, and the regex
        # allows them to support "Mrs. Craigie" / "Mme. Duclaux".
        if not m.group("hon") and " " not in name:
            return m.group(0)
        canonical = resolver.resolve(name)
        if not canonical:
            return m.group(0)
        linked += 1
        established[canonical] = quote_plus(canonical)
        return (
            f'{head}<a href="/contributors.html?q={established[canonical]}">'
            f"{name}</a>"
        )

    html = _CELL_CONTRIBUTOR_RE.sub(pass1b, html)

    if not established:
        return html, linked

    # Build per-contributor replacement patterns for pass 2.
    # Surname bucket: only link bare surname if unique among established.
    surname_bucket: dict[str, list[str]] = {}
    for canonical in established:
        last = canonical.strip().split(" ")[-1]
        surname_bucket.setdefault(last.lower(), []).append(canonical)
    unique_surnames = {
        last for last, names in surname_bucket.items() if len(names) == 1
    }

    # Build one combined regex per contributor: longer variants first
    # so "Donald Francis Tovey" wins over "Donald Tovey" at the same
    # start position.
    compiled: list[tuple[re.Pattern[str], str]] = []
    for canonical, query in established.items():
        variants = _name_variant_patterns(canonical)
        last = canonical.strip().split(" ")[-1]
        if last.lower() in unique_surnames and last not in variants:
            variants.append(last)
        if not variants:
            continue
        variants.sort(key=len, reverse=True)
        # Word-boundary on both sides. Use (?:Mr\.|Dr\.|…\s+)? as
        # optional leading honorific so "Dr. Tovey" and "Prof. Tovey"
        # also link.
        alt = "|".join(re.escape(v) for v in variants)
        pattern = re.compile(
            r"(?:(?:Prof(?:essor)?\.?|Dr\.?|Mr\.?|Mrs\.?|Miss|Sir|Rev(?:erend)?\.?)\s+)?"
            r"(?:" + alt + r")"
            r"(?!\w)"
        )
        compiled.append((pattern, query))

    def pass2(text: str) -> str:
        nonlocal linked
        for pattern, query in compiled:
            def link(m: re.Match[str]) -> str:
                nonlocal linked
                linked += 1
                return (
                    f'<a href="/contributors.html?q={query}">{m.group(0)}</a>'
                )
            text = pattern.sub(link, text)
        return text

    html = _protect_and_run(html, pass2)
    return html, linked


def transform_content(
    html: str,
    title_map: dict[str, str],
    chapter_lists: dict[str, str] | None = None,
    contributor_resolver: ContributorResolver | None = None,
    by_volume: dict[int, list[dict]] | None = None,
) -> tuple[str, list[tuple[str, str]]]:
    """Clean Gutenberg markup and resolve article references to links.

    Returns (transformed_html, toc_entries) where toc_entries is a list
    of (anchor_id, visible_text) for each sidenote / shoulder heading —
    the caller builds a TOC from these, matching the preface page's
    pattern.
    """
    linked = 0
    missed = 0
    missed_titles: set[str] = set()
    toc_entries: list[tuple[str, str]] = []

    # Splice in cross-referenced article lists before article resolution,
    # so their <li class="c018"> entries also get linked.
    if chapter_lists:
        def splice_list(m: re.Match[str]) -> str:
            target = m.group(1).upper()
            block = chapter_lists.get(target)
            if not block:
                return m.group(0)
            note = (
                f'<p style="color:#6b5e4f;font-style:italic;margin-top:2em;'
                f'padding-top:0.6em;">'
                f"This list of related articles appears at the end of "
                f"Chapter {target} in the original, where it's printed "
                f"once for this chapter and its neighbours."
                f'</p>'
            )
            return note + wrap_list_in_accordion(block)

        html = _XREF_LIST_RE.sub(splice_list, html)

    # Inline article references: <span class="sc">Name</span> or <b>Name</b>.
    # The Guide follows many references with "(Vol. N, p. M)" —
    # sometimes right after the span, sometimes with intervening
    # quotes / pseudonyms / parentheticals ("Wind Instruments (mouth
    # blown) (Vol. 28, p. 709)"). We scan ~140 chars forward to catch
    # those. The <b> variant covers section-header-style article refs
    # like "<b>Stringed Instruments</b> (Vol. 25, p. 1038)".
    _tail_vol_page = re.compile(
        r'^.{0,140}?\(Vol\.\s*(\d+),\s*pp?\.\s*(\d+)[^)]*\)',
        re.DOTALL,
    )

    def repl_ref(m: re.Match[str]) -> str:
        nonlocal linked, missed
        inner = m.group(1).strip()
        tag = m.group(0)[1:3] if m.group(0).startswith("<b") else "sc"
        plain = re.sub(r"<[^>]+>", "", inner)
        plain = plain.replace("&amp;", "&").replace("&mdash;", "—")
        plain = re.sub(r"\s+", " ", plain).strip()
        tail = m.string[m.end():m.end() + 180]
        vp_match = _tail_vol_page.match(tail)
        # 1. Exact title (most definitive when present)
        fn = title_map.get(plain.upper())
        # 2. (Vol, page) annotation — authoritative structural pointer
        if not fn and by_volume is not None and vp_match:
            try:
                vol = int(vp_match.group(1))
                page = int(vp_match.group(2))
                fn = lookup_by_vol_page(by_volume, vol, page, plain)
            except (ValueError, TypeError):
                pass
        # 3. Fuzzy title match (heuristic, last resort)
        if not fn:
            fn = resolve_article_title(plain, title_map)
        if fn:
            url = filename_to_url(fn)
            if url:
                linked += 1
                if tag == "sc":
                    return f'<span class="sc"><a href="{url}">{inner}</a></span>'
                else:
                    return f'<b><a href="{url}">{inner}</a></b>'
        missed += 1
        missed_titles.add(plain)
        return m.group(0)

    # Run SC and <b> separately so the capture group semantics stay
    # simple (both put the inner text at group 1).
    html = re.sub(
        r'<span class="sc">(.*?)</span>', repl_ref, html, flags=re.DOTALL,
    )
    html = re.sub(
        r'<b>(.*?)</b>', repl_ref, html, flags=re.DOTALL,
    )

    # Alphabetical-list items: <li class="c018">Name</li>
    def repl_li(m: re.Match[str]) -> str:
        nonlocal linked, missed
        name = re.sub(r"\s+", " ", m.group(1)).strip()
        # Handle "Name or Alias" format — try main before alias
        parts = re.split(r"\s+or\s+", name, maxsplit=1)
        for p in parts:
            fn = resolve_article_title(p.strip(), title_map)
            if fn:
                url = filename_to_url(fn)
                if url:
                    linked += 1
                    return f'<li class="c018"><a href="{url}">{name}</a></li>'
        missed += 1
        missed_titles.add(name)
        return m.group(0)

    html = re.sub(r'<li class="c018">([^<]+)</li>', repl_li, html)

    # Collapse any native alphabetical list in the chapter into an
    # accordion (so chapters that have their own list don't scroll
    # forever either).
    html = _INDEX_LIST_RE.sub(
        lambda m: wrap_list_in_accordion(m.group(0)), html
    )

    # Strip Gutenberg page-number spans (numbered internal to source)
    html = re.sub(
        r'<span class="pageno"[^>]*>[^<]*</span>', "", html,
    )

    # Rewrite Gutenberg image tags: strip their classes/ids, rewrite
    # the path (images/X -> readers-guide-X), and inline explicit width
    # + style so the browser can't render at native 2000+px even if CSS
    # fails.
    def rewrite_img(m: re.Match[str]) -> str:
        attrs = m.group(1)
        alt_m = re.search(r'alt="([^"]*)"', attrs)
        src_m = re.search(r'src="images/([^"]+)"', attrs)
        alt = alt_m.group(1) if alt_m else ""
        src_file = src_m.group(1) if src_m else ""
        return (
            f'<img src="readers-guide-{src_file}" alt="{alt}" width="560" '
            f'style="max-width:100%;height:auto;display:block;'
            f'margin:1.2em auto;border:1px solid #d4cab8;'
            f'background:#fdfcf9;padding:6px;">'
        )

    html = re.sub(r"<img([^>]*)>", rewrite_img, html)

    # Merge each sidenote into the START of the following <p>, as an
    # inline <span class="shoulder-heading">. This matches the article
    # viewer's pattern (viewer.html): <p> is the positioning context,
    # so the shoulder floats in the margin next to the paragraph it
    # annotates.
    def repl_sidenote_merge(m: re.Match[str]) -> str:
        text = re.sub(r"\s+", " ", m.group(1)).strip()
        p_attrs = m.group(2)
        anchor_id = f"sh-{len(toc_entries) + 1}"
        toc_entries.append((anchor_id, text))
        return (
            f'<p{p_attrs}>'
            f'<span class="shoulder-heading" id="{anchor_id}">{text}</span>'
        )

    html = re.sub(
        r'<div class="sidenote">(.*?)</div>\s*<p([^>]*)>',
        repl_sidenote_merge,
        html,
        flags=re.DOTALL,
    )
    # Any sidenote that wasn't followed by a <p> stays as its own block.
    def repl_sidenote_fallback(m: re.Match[str]) -> str:
        text = re.sub(r"\s+", " ", m.group(1)).strip()
        anchor_id = f"sh-{len(toc_entries) + 1}"
        toc_entries.append((anchor_id, text))
        return f'<p><span class="shoulder-heading" id="{anchor_id}">{text}</span></p>'

    html = re.sub(
        r'<div class="sidenote">(.*?)</div>',
        repl_sidenote_fallback,
        html,
        flags=re.DOTALL,
    )

    # Strip Gutenberg "nf-center" wrapper divs — keep inner content
    html = re.sub(
        r'<div class="nf-center-c0">\s*<div class="nf-center c003">\s*'
        r'<div>(.*?)</div>\s*</div>\s*</div>',
        r'<div class="cross-ref">\1</div>',
        html,
        flags=re.DOTALL,
    )

    # Drop Gutenberg class names on paragraphs (keep tag)
    html = re.sub(r'<p class="[^"]*">', "<p>", html)

    # Drop drop-cap span wrapping — original drop-cap-by-span is fragile
    html = re.sub(r"<p><p>", "<p>", html)

    # Contributor link-ups (pass by-author citations through the DB)
    contrib_linked = 0
    if contributor_resolver is not None:
        html, contrib_linked = link_contributors(html, contributor_resolver)

    print(
        f"  resolved {linked} refs, unresolved {missed} "
        f"({len(missed_titles)} unique); "
        f"{contrib_linked} contributor citations linked",
        file=sys.stderr,
    )
    if missed_titles and len(missed_titles) <= 30:
        print("  unresolved samples:", sorted(missed_titles)[:10], file=sys.stderr)

    return html, toc_entries


# --- Page template ---------------------------------------------------

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} &mdash; Reader's Guide &mdash; Encyclop&aelig;dia Britannica, 11th Edition</title>
  <style>
    :root {{
      --bg: #f5f1eb; --panel: #fdfcf9; --text: #2c2416;
      --muted: #6b5e4f; --border: #d4cab8; --link: #7b3f00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", "Cambria Math", "Segoe UI Symbol", "Noto Sans Symbols 2", serif;
      background: var(--bg); color: var(--text); line-height: 1.7;
    }}
    .page {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    .card {{
      background: var(--panel); border: 1px solid var(--border);
      border-radius: 2px; padding: 20px 24px; margin-bottom: 20px;
    }}
    h1 {{
      margin-top: 0; font-size: 1.8rem; font-variant: small-caps;
      letter-spacing: 0.06em; color: #2c2416;
    }}
    h1 .chap-num {{ display: block; font-size: 0.6em; color: var(--muted);
      font-variant: normal; letter-spacing: 0.2em; margin-bottom: 6px; }}
    h4 {{ font-size: 1rem; font-variant: small-caps;
      letter-spacing: 0.04em; color: #5c4a32; margin-top: 2em; }}
    a {{ color: var(--link); text-decoration: none; }}
    a:hover {{ text-decoration: underline;
      background: rgba(139, 115, 85, 0.08); border-radius: 2px; }}
    /* Layout copied verbatim from viewer.html's .body-text pattern. */
    .body-text {{
      font-size: 1.08rem;
      margin-right: 160px;
      position: relative;
    }}
    .body-text p {{
      text-indent: 1.5em;
      margin: 0 0 0.5em 0;
      position: relative;
    }}
    .body-text p:first-of-type {{ text-indent: 0; }}
    .shoulder-heading {{
      position: absolute;
      right: -170px;
      width: 150px;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 0.8rem;
      font-style: italic;
      color: var(--muted);
      text-align: left;
      text-indent: 0;
      scroll-margin-top: 20px;
    }}
    @media (max-width: 900px) {{
      .body-text {{ margin-right: 0; }}
      .shoulder-heading {{
        position: static; display: block; width: auto;
        margin: 0.5em 0 0.2em; font-weight: 600; color: var(--text);
      }}
    }}
    .toc {{
      background: var(--bg); border: 1px solid var(--border);
      border-radius: 8px; padding: 12px 16px;
      margin: 0 0 20px; font-size: 0.9rem;
    }}
    .toc h3 {{
      margin: 0 0 8px; font-size: 0.95rem;
      color: var(--muted); font-variant: small-caps;
      letter-spacing: 0.04em;
    }}
    .toc ol {{
      margin: 0; padding-left: 20px;
      columns: 2; column-gap: 24px;
    }}
    .toc li {{ margin-bottom: 3px; }}
    .toc a {{ color: var(--text); font-size: 0.88rem; }}
    .sc {{ font-variant: small-caps; }}
    ul.index {{
      columns: 3; column-gap: 32px; padding-left: 1.4em;
      font-size: 0.92rem; line-height: 1.5;
    }}
    ul.index li {{ margin-bottom: 2px; break-inside: avoid; }}
    details.article-list {{
      margin: 1.5em 0; border: 1px solid var(--border);
      border-radius: 2px; background: #faf6ed;
    }}
    details.article-list > summary {{
      cursor: pointer; padding: 12px 18px; list-style: none;
      user-select: none; display: flex; align-items: baseline;
      gap: 0.6em; font-family: Georgia, serif;
    }}
    details.article-list > summary::-webkit-details-marker {{ display: none; }}
    details.article-list > summary::before {{
      content: "▸"; display: inline-block; color: var(--muted);
      font-size: 0.9em; transition: transform 0.15s ease;
    }}
    details.article-list[open] > summary::before {{ transform: rotate(90deg); }}
    details.article-list > summary:hover {{ background: rgba(139, 115, 85, 0.05); }}
    details.article-list .list-title {{
      font-variant: small-caps; letter-spacing: 0.04em;
      color: #5c4a32; font-size: 0.95rem;
    }}
    details.article-list .list-count {{
      color: var(--muted); font-size: 0.85rem; font-style: italic;
    }}
    details.article-list > ul.index,
    details.article-list > div,
    details.article-list > p {{
      padding: 0 18px 16px;
    }}
    .cross-ref {{
      font-style: italic; color: var(--muted); text-align: center;
      margin: 0.8em 0 1.2em; font-size: 0.95rem;
    }}
    .body-text img {{
      display: block; max-width: min(100%, 560px); height: auto;
      margin: 1.2em auto; border: 1px solid var(--border);
      background: #fdfcf9; padding: 6px;
    }}
    .figcenter {{ text-align: center; margin: 1.2em 0; }}
    .header-divider {{
      text-align: center; color: #8b7355; font-size: 1.6rem;
      margin: -6px 0 14px; letter-spacing: 0.3em; user-select: none;
    }}
  </style>
  <script>
    (function() {{
      var isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
      var base = isLocal ? "/tools/viewer/" : "/";
      document.write('<link rel="icon" type="image/svg+xml" href="' + base + 'favicon.svg">');
    }})();
  </script>
</head>
<body>
<div class="page">
  <div class="card">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
      <h1 style="margin: 0; font-size: 1.15rem; color: #5c4a32;"><a href="/home.html" style="color: inherit; text-decoration: none;"><svg viewBox="0 0 32 32" width="28" height="28" style="vertical-align: middle; margin-right: 10px;" aria-hidden="true"><rect x="1" y="1" width="30" height="30" fill="none" stroke="currentColor" stroke-width="1"/><rect x="3.5" y="3.5" width="25" height="25" fill="none" stroke="currentColor" stroke-width="0.6"/><text x="16" y="22" text-anchor="middle" font-family="Georgia, serif" font-size="16" fill="currentColor" style="letter-spacing:-0.3px">EB</text></svg><span style="font-variant: small-caps; letter-spacing: 0.04em;">Reader's Guide</span> <span style="font-variant: normal; font-style: italic; letter-spacing: 0.01em;">&mdash; 11th Edition</span></a></h1>
      <div style="font-size: 0.9rem;">
        <a href="/ancillary.html">Ancillary</a>
        &nbsp;&middot;&nbsp;
        <a href="/index.html">Articles</a>
      </div>
    </div>
  </div>
  <div class="header-divider">&#x223C;&#x25C6;&#x223C;</div>
  <div class="card">
    <h1><span class="chap-num">Chapter {chap_num}</span>{title}</h1>
{toc_html}
    <div class="body-text">
{body_html}
    </div>
  </div>
</div>
</body>
</html>
"""


PART_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Part {roman} &mdash; Reader's Guide &mdash; Encyclop&aelig;dia Britannica, 11th Edition</title>
  <style>
    :root {{
      --bg: #f5f1eb; --panel: #fdfcf9; --text: #2c2416;
      --muted: #6b5e4f; --border: #d4cab8; --link: #7b3f00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", "Cambria Math", "Segoe UI Symbol", "Noto Sans Symbols 2", serif;
      background: var(--bg); color: var(--text); line-height: 1.6;
    }}
    .page {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    .card {{
      background: var(--panel); border: 1px solid var(--border);
      border-radius: 2px; padding: 20px 24px; margin-bottom: 20px;
    }}
    h1 {{
      margin: 0; font-size: 1.8rem; font-variant: small-caps;
      letter-spacing: 0.06em; color: #2c2416;
    }}
    h1 .part-num {{
      display: block; font-size: 0.6em; color: var(--muted);
      font-variant: normal; letter-spacing: 0.2em; margin-bottom: 6px;
    }}
    a {{ color: var(--link); text-decoration: none; }}
    a:hover {{
      text-decoration: underline;
      background: rgba(139, 115, 85, 0.08); border-radius: 2px;
    }}
    .description {{
      font-style: italic; color: var(--muted); margin: 12px 0 0;
      font-size: 1.05rem;
    }}
    ul.chapters {{
      list-style: none; padding: 0; margin: 0;
      columns: 2; column-gap: 32px;
    }}
    ul.chapters li {{
      padding: 4px 0; break-inside: avoid;
      border-bottom: 1px dotted var(--border);
    }}
    ul.chapters .chap-num {{
      color: var(--muted); font-size: 0.85em; letter-spacing: 0.1em;
      margin-right: 0.6em;
    }}
    @media (max-width: 600px) {{
      ul.chapters {{ columns: 1; }}
    }}
    .header-divider {{
      text-align: center; color: #8b7355; font-size: 1.6rem;
      margin: -6px 0 14px; letter-spacing: 0.3em; user-select: none;
    }}
  </style>
  <script>
    (function() {{
      var isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
      var base = isLocal ? "/tools/viewer/" : "/";
      document.write('<link rel="icon" type="image/svg+xml" href="' + base + 'favicon.svg">');
    }})();
  </script>
</head>
<body>
<div class="page">
  <div class="card">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
      <h1 style="margin: 0; font-size: 1.15rem; color: #5c4a32;"><a href="/readers-guide.html" style="color: inherit; text-decoration: none;"><svg viewBox="0 0 32 32" width="28" height="28" style="vertical-align: middle; margin-right: 10px;" aria-hidden="true"><rect x="1" y="1" width="30" height="30" fill="none" stroke="currentColor" stroke-width="1"/><rect x="3.5" y="3.5" width="25" height="25" fill="none" stroke="currentColor" stroke-width="0.6"/><text x="16" y="22" text-anchor="middle" font-family="Georgia, serif" font-size="16" fill="currentColor" style="letter-spacing:-0.3px">EB</text></svg><span style="font-variant: small-caps; letter-spacing: 0.04em;">Reader's Guide</span> <span style="font-variant: normal; font-style: italic; letter-spacing: 0.01em;">&mdash; 11th Edition</span></a></h1>
      <div style="font-size: 0.9rem;">
        <a href="/ancillary.html">Ancillary</a>
        &nbsp;&middot;&nbsp;
        <a href="/index.html">Articles</a>
      </div>
    </div>
  </div>
  <div class="header-divider">&#x223C;&#x25C6;&#x223C;</div>
  <div class="card">
    <h1><span class="part-num">Part {roman}</span>{title}</h1>
  </div>
  <div class="card">
    <ul class="chapters">
{chapter_items}
    </ul>
  </div>
</div>
</body>
</html>
"""


INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Reader's Guide &mdash; Encyclop&aelig;dia Britannica, 11th Edition</title>
  <style>
    :root {{
      --bg: #f5f1eb; --panel: #fdfcf9; --text: #2c2416;
      --muted: #6b5e4f; --border: #d4cab8; --link: #7b3f00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", "Cambria Math", "Segoe UI Symbol", "Noto Sans Symbols 2", serif;
      background: var(--bg); color: var(--text); line-height: 1.6;
    }}
    .page {{ max-width: 960px; margin: 0 auto; padding: 24px; }}
    .card {{
      background: var(--panel); border: 1px solid var(--border);
      border-radius: 2px; padding: 20px 24px; margin-bottom: 20px;
    }}
    h1 {{
      margin-top: 0; font-size: 1.8rem; font-variant: small-caps;
      letter-spacing: 0.06em; color: #2c2416;
    }}
    a {{ color: var(--link); text-decoration: none; }}
    a:hover {{
      text-decoration: underline;
      background: rgba(139, 115, 85, 0.08); border-radius: 2px;
    }}
    .intro {{
      color: var(--muted); font-size: 0.95rem; margin-bottom: 8px;
    }}
    .part {{
      border: 1px solid var(--border); background: var(--panel);
      border-radius: 2px; padding: 18px 22px; margin-bottom: 16px;
    }}
    .part h2 {{
      margin: 0 0 6px; font-size: 1.15rem;
      font-variant: small-caps; letter-spacing: 0.04em;
    }}
    .part h2 .part-num {{
      color: var(--muted); font-variant: normal;
      letter-spacing: 0.15em; font-size: 0.85em; margin-right: 0.6em;
    }}
    .part p {{
      margin: 0 0 10px; font-size: 0.95rem; font-style: italic;
      color: var(--muted);
    }}
    .part .meta {{
      font-size: 0.88rem; color: var(--muted);
    }}
    .header-divider {{
      text-align: center; color: #8b7355; font-size: 1.6rem;
      margin: -6px 0 14px; letter-spacing: 0.3em; user-select: none;
    }}
    .footer {{
      color: var(--muted); font-size: 0.85rem; margin-top: 20px;
      text-align: center;
    }}
  </style>
  <script>
    (function() {{
      var isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
      var base = isLocal ? "/tools/viewer/" : "/";
      document.write('<link rel="icon" type="image/svg+xml" href="' + base + 'favicon.svg">');
    }})();
  </script>
</head>
<body>
<div class="page">
  <div class="card">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
      <h1 style="margin: 0; font-size: 1.3rem; color: #5c4a32;"><a href="/home.html" style="color: inherit; text-decoration: none;"><svg viewBox="0 0 32 32" width="32" height="32" style="vertical-align: middle; margin-right: 10px;" aria-hidden="true"><rect x="1" y="1" width="30" height="30" fill="none" stroke="currentColor" stroke-width="1"/><rect x="3.5" y="3.5" width="25" height="25" fill="none" stroke="currentColor" stroke-width="0.6"/><text x="16" y="22" text-anchor="middle" font-family="Georgia, serif" font-size="16" fill="currentColor" style="letter-spacing:-0.3px">EB</text></svg><span style="font-variant: small-caps; letter-spacing: 0.06em;">Reader's Guide</span> <span style="font-variant: normal; font-style: italic; letter-spacing: 0.02em;">&mdash; 11th Edition</span></a></h1>
      <div style="font-size: 0.9rem;">
        <a href="/ancillary.html">Ancillary</a>
        &nbsp;&middot;&nbsp;
        <a href="/index.html">Articles</a>
      </div>
    </div>
    <div class="intro">
      A guide to the 11th edition of the Encyclop&aelig;dia Britannica &mdash;
      organised as courses of reading for different occupations,
      fields of study, and interests, with citations pointing into
      the main work.
    </div>
  </div>
  <div class="header-divider">&#x223C;&#x25C6;&#x223C;</div>
{part_cards}
  <div class="footer">
    Transcription from the Project Gutenberg edition (ebook&nbsp;#74039).
    Article and contributor citations are linked to the main encyclop&aelig;dia.
  </div>
</div>
</body>
</html>
"""


def build_part_page(
    part: dict,
    all_chapters: dict[str, tuple[str, str]],
) -> None:
    roman = part["roman"]
    description = part["description"] or ""
    # Part I-VI don't have their own source text beyond the header,
    # so the landing page is essentially a chapter index.
    items = []
    for ch_roman in part["chapter_romans"]:
        if ch_roman not in all_chapters:
            continue
        ch_title_up, _ = all_chapters[ch_roman]
        pretty = ch_title_up.title()
        url = _chapter_url(ch_roman, pretty)
        items.append(
            f'<li><span class="chap-num">Chapter {ch_roman}</span>'
            f'<a href="{url}">{pretty}</a></li>'
        )
    chapter_items = "\n".join(items)
    # Part's bare numeral fills both title and roman spots when no
    # description is present (shouldn't happen for our 6 parts).
    title = description or f"Part {roman}"
    out = PART_TEMPLATE.format(
        roman=roman,
        title=title,
        description=description,
        chapter_items=chapter_items,
    )
    out_path = OUT_DIR / _part_filename(roman)
    out_path.write_text(out, encoding="utf-8")
    print(f"  wrote {out_path}", file=sys.stderr)


def build_guide_index(
    parts: list[dict],
    all_chapters: dict[str, tuple[str, str]],
) -> None:
    cards = []
    for p in parts:
        roman = p["roman"]
        desc = p["description"] or f"Part {roman}"
        chapter_count = len(
            [r for r in p["chapter_romans"] if r in all_chapters]
        )
        noun = "chapter" if chapter_count == 1 else "chapters"
        cards.append(
            f'<div class="part">'
            f'<h2><a href="/{_part_filename(roman)}">'
            f'<span class="part-num">Part {roman}</span>{desc}'
            f"</a></h2>"
            f'<div class="meta">{chapter_count} {noun}</div>'
            f"</div>"
        )
    out = INDEX_TEMPLATE.format(part_cards="\n".join(cards))
    out_path = OUT_DIR / "readers-guide.html"
    out_path.write_text(out, encoding="utf-8")
    print(f"  wrote {out_path}", file=sys.stderr)


def main() -> int:
    if not SOURCE_HTML.is_file():
        print(f"missing source: {SOURCE_HTML}", file=sys.stderr)
        return 1
    if not INDEX_JSON.is_file():
        print(f"missing article index: {INDEX_JSON}", file=sys.stderr)
        return 1

    source = SOURCE_HTML.read_text(encoding="utf-8")
    title_map, by_volume = load_article_indexes()
    contributor_resolver = load_contributor_resolver()
    print(
        f"loaded {len(title_map)} article titles, "
        f"{len(contributor_resolver._canonical)} contributors",
        file=sys.stderr,
    )

    all_chapters = extract_all_chapters(source)
    chapter_lists = {
        roman: block
        for roman, (_, html) in all_chapters.items()
        if (block := find_chapter_article_list(html))
    }
    print(
        f"{len(all_chapters)} chapters, {len(chapter_lists)} with article lists",
        file=sys.stderr,
    )

    # Accept chapter roman numerals on the command line; default to Chapter I.
    # Pass "all" to build every chapter.
    args = [r for r in sys.argv[1:]]
    if not args:
        requested = ["I"]
    elif args == ["all"]:
        requested = list(all_chapters.keys())
    else:
        requested = [r.upper() for r in args]
    for roman in requested:
        if roman not in all_chapters:
            print(f"  (skip) Chapter {roman} not found", file=sys.stderr)
            continue
        build_chapter(
            roman, all_chapters, chapter_lists, title_map,
            contributor_resolver, by_volume,
        )

    # Build the Part landing pages and the top-level Guide TOC when
    # we're doing a full rebuild. Individual-chapter invocations skip
    # this so iterating on one chapter stays fast.
    if args == ["all"]:
        parts = extract_parts(source)
        print(
            f"building {len(parts)} part landing pages + top-level index",
            file=sys.stderr,
        )
        for part in parts:
            build_part_page(part, all_chapters)
        build_guide_index(parts, all_chapters)

    return 0


def build_chapter(
    roman: str,
    all_chapters: dict[str, tuple[str, str]],
    chapter_lists: dict[str, str],
    title_map: dict[str, str],
    contributor_resolver: ContributorResolver,
    by_volume: dict[int, list[dict]],
) -> None:
    title_up, inner = all_chapters[roman]
    print(f"Chapter {roman}: {title_up}", file=sys.stderr)

    # Strip stray leading </div> from the Gutenberg source — each
    # chapter heading is wrapped in an outer <div> whose closing tag
    # lands at the start of our extracted content and would otherwise
    # close the .body-text wrapper prematurely.
    inner = re.sub(r"^\s*</div>", "", inner, count=1)
    transformed, toc_entries = transform_content(
        inner, title_map, chapter_lists, contributor_resolver, by_volume,
    )

    # Pretty-case the chapter title (source is uppercase)
    pretty_title = title_up.title()

    if toc_entries:
        items = "".join(
            f'<li><a href="#{anchor}">{text}</a></li>'
            for anchor, text in toc_entries
        )
        toc_html = f'<div class="toc"><h3>Contents</h3><ol>{items}</ol></div>'
    else:
        toc_html = ""

    out = PAGE_TEMPLATE.format(
        title=pretty_title,
        chap_num=roman,
        toc_html=toc_html,
        body_html=transformed,
    )

    out_path = OUT_DIR / _chapter_filename(roman, pretty_title)
    out_path.write_text(out, encoding="utf-8")
    print(f"  wrote {out_path}", file=sys.stderr)


def _chapter_filename(roman: str, pretty_title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", pretty_title.lower()).strip("-")
    return f"readers-guide-ch{roman.lower()}-{slug}.html"


def _chapter_url(roman: str, pretty_title: str) -> str:
    return "/" + _chapter_filename(roman, pretty_title)


def _part_filename(roman: str) -> str:
    return f"readers-guide-part-{roman.lower()}.html"


if __name__ == "__main__":
    raise SystemExit(main())

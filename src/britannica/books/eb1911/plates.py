"""EB1911's plates: which leaves are plate inserts, and what each is called.

A plate is an UNPAGINATED leaf that carries an image, and is not a volume
title page.  EB1911 is wholly paginated — every body page prints its folio
in the running head — so the missing folio is the book's own signal; the
title-page exclusion reads EB1911's title-page templates and its ELEVENTH
EDITION banner.  A plate is titled from its page heading and its
``Plate N.`` label: "AEGEAN CIVILIZATION, PLATE I".

The Britannica's rules, not the engine's: moved out of pipeline/stages/
detect_boundaries.py (wikikit step 5).  The engine lifts whatever the book
calls a plate into its own article (``Corpus.is_plate`` /
``Corpus.plate_title``).
"""
from __future__ import annotations

import re

from britannica.pipeline.stages.detect_boundaries import folio_of
from britannica.util.strings import until_stable
from britannica.wikitext import first_template_body, page_head_fields

# Raw wikitext section-begin tag.
def _match_section_begin(text):
    """Find all section-begin markers, handling both quoted and unquoted forms."""
    # Quoted: <section begin="Foo Bar" />
    # Unquoted: <section begin=Foo/>
    pattern = re.compile(
        r'<section\s+begin=(?:"([^"]+)"|([A-Za-z][^/>\s]*))\s*/?>', re.IGNORECASE)
    results = []
    for m in pattern.finditer(text):
        name = m.group(1) if m.group(1) is not None else m.group(2)
        results.append((m.start(), m.end(), name))
    return results

# WIKITEXT bold/italic, still in its RAW form here.  Boundary detection reads the
# page's raw text, where emphasis is `'''…'''` and not yet the `«B»` markers the
# quote-run conversion makes downstream — so stripping only the markers left the
# quotes standing, and they reached the rendered title: vol 1 p944 shipped as
# `'''AMPHITHEATRE''', PLATE I`.  Worse on its facing page, where the wrapper hid
# the label from the "this field is a Plate number, skip it" test — `'''Plate
# II.'''` does not match `^Plate\b` — so the LABEL became the title and the real
# name, one slot over, was never read.  Two or more quotes are markup; a single
# one is an apostrophe in a name (M'DOUALL) and is left alone.
_WIKI_QUOTES = re.compile(r"'{2,}")

# One unwrap pass over a title field: a styling template keeping its last slot.
# Two patterns because the inner slot may or may not itself hold a pipe.
_STYLER_1 = re.compile(r"\{\{[^{}|]*\|([^{}|]*)\}\}")
_STYLER_N = re.compile(r"\{\{[^{}]*\|([^{}|]*)\}\}")


def _unwrap_styler(t: str) -> str:
    return _STYLER_N.sub(r"\1", _STYLER_1.sub(r"\1", t))


def _title_plaintext(text: str) -> str:
    """Project a TITLE field to plain text — the title path's own minimal need, NOT a
    general template sweeper.

    UNWRAPS styling-template wrappers keeping their content ({{mono|{{fs|108%|TITLE}}}}
    → TITLE, last param), and drops the drop-cap / size HTML tags (<big>S</big>UCCINIC →
    SUCCINIC) and «B»/«I» markers that mustn't leak into a rendered title.

    It does NOT silently delete unhandled templates: the old `_strip_templates` sweeper's
    content-destroying `{{…}}`→'' pass is gone, so a raw title-furniture template stays
    visible rather than vanishing.  (Honest title recursion via the TITLE element is a
    later step; this is the scoped field projection the boundary pass needs now.)"""
    text = until_stable(text, _unwrap_styler)
    text = re.sub(
        r"</?(?:big|small|sub|sup|span|font)\b[^>]*>",
        "", text, flags=re.IGNORECASE,
    )
    text = re.sub(r"«/?[BI]»", "", text)
    text = _WIKI_QUOTES.sub("", text)
    return text.strip()

# A `Plate` heading, read by PEELING its wrappers instead of naming how many
# there are.  The size wrapper used to be one optional level written into the
# pattern (`(?:\{\{(?:smaller|larger)\|)?`), which is a cap of one: a heading
# wrapped twice would not be a plate heading at all, and the plate would take an
# ordinary article's title.  Nothing about "this line says Plate" depends on how
# many size wrappers the transcriber stacked ([[feedback_recursion_is_recognition]]).
_SIZE_WRAPPER_RE = re.compile(r"\{\{\s*(?:smaller|larger)\s*\|", re.IGNORECASE)
_SMALLCAPS_OPEN_RE = re.compile(r"\{\{\s*(?:sc|uc|small-caps)\s*\|", re.IGNORECASE)
# The tail is a genuine three-way choice, not a nesting: the Roman may sit inside
# the small-caps, after it, or be absent (vol 2 ANTHROPOLOGY is a single plate).
_PLATE_TAIL_RE = re.compile(
    r"Plate(?:\s+([IVX]+)\.?\}\}|\s*\}\}\s*([IVX]+)\.?|\s*\}\})", re.IGNORECASE)


def _plate_field(text: str) -> "str | None":
    """The plate's Roman numeral, `""` when it states none, `None` when this is
    not a plate heading at all."""
    pos = len(text) - len(text.lstrip())
    while (w := _SIZE_WRAPPER_RE.match(text, pos)):
        pos = w.end()
    sc = _SMALLCAPS_OPEN_RE.match(text, pos)
    if not sc:
        return None
    m = _PLATE_TAIL_RE.match(text, sc.end())
    if not m:
        return None
    return (m.group(1) or m.group(2) or "").upper()


# Non-anchored variant of ``_plate_field`` — matches a
# ``{{sc|Plate …}}`` / ``{{uc|Plate …}}`` token *anywhere* on the page,
# not just at the start of a heading-template field.  Used by
# ``_plate_label_from_content`` for the title suffix of heuristic-
# detected plates whose ``Plate N.`` label sits in a layout-table cell.
_PLATE_LABEL_ANY_RE = re.compile(
    r"\{\{(?:sc|uc|small-caps)\|"
    r"Plate"
    r"(?:"
    r"\s+([IVX]+)\s*\.?\s*\}\}"           #   …I.}}  /  …I}}
    r"|"
    r"\s*\.?\s*\}\}\s*([IVX]+)\.?"        #   }} II. /  .}} II
    r"|"
    r"\s*\.?\s*\}\}"                      #   }} alone /  .}}  (single-plate)
    r")",
    re.IGNORECASE,
)


def _plate_label_from_content(raw: str) -> str | None:
    """Return a plate's Roman numeral (or ``""`` for a bare ``Plate.``
    with no numeral) from a ``{{sc|Plate …}}`` / ``{{uc|Plate …}}``
    token appearing *anywhere* on the page.

    Used only as a title-suffix fallback for heuristic-detected plates
    (ROUND TOWERS, TAPESTRY, EGYPT, INDIA, …): their page heading is
    ``{{c|{{x-larger|TITLE}}}}`` rather than ``{{rh|…|{{sc|Plate N.}}}}``,
    so ``_extract_plate_number`` (heading-fields only — deliberately
    narrow, since it also gates plate *detection* via
    ``_heading_names_plate``) finds nothing.  The ``Plate N.`` label
    still exists, just inside a layout-table cell instead.  Since this
    only runs once a page is already known to be a plate, a stray
    ``{{sc|Plate}} III`` cross-reference is the worst it can pick up — a
    cosmetic title-suffix slip, never data loss."""
    m = _PLATE_LABEL_ANY_RE.search(raw)
    if not m:
        return None
    return (m.group(1) or m.group(2) or "").upper()


def _extract_plate_number(raw: str) -> str | None:
    """Return the Roman-numeral plate number from a page's heading
    template, or None if the page heading carries no `Plate N.` token.

    This is the same walk as `_heading_names_plate`; it returns the
    numeral instead of a bool so the boundary detector can compose a
    title like "DOG, PLATE I" and the slug derived from it stays
    deterministic across rebuilds (the plate number is the only
    field guaranteed to be unique per plate).

    Searches the whole raw page rather than only the
    ``<noinclude>…</noinclude>`` block: transcribers vary on whether
    the page-heading template lives inside the noinclude (DOG vol 8,
    SHAKESPEARE vol 24) or outside it (AEGEAN CIVILIZATION vol 1).
    """
    for f in page_head_fields(raw):
        # Strip cosmetic wrappers transcribers add around the plate-label field
        # (vol 1 AMPHITHEATRE: `<small>'''{{sc|Plate}} I.'''</small>`);
        # `_plate_field` knows only the bare and `{{(smaller|larger)|…}}` forms.
        cleaned = re.sub(r"</?(?:big|small|sub|sup)\b[^>]*>",
                         "", f, flags=re.IGNORECASE)
        cleaned = _WIKI_QUOTES.sub("", re.sub(r"«/?[BI]»", "", cleaned))
        # "" for a bare `{{sc|Plate}}` (single-plate articles), so the gate
        # fires while the title-composer can still tell "PLATE I" from a
        # "PLATE" with no number; None when it is not a plate heading.
        roman = _plate_field(cleaned)
        if roman is not None:
            return roman
    return None


def plate_title(raw: str, volume: int, page_number: int) -> str:
    """Build the title for a plate-insert page: the parent article's
    name (from the page heading or, failing that, the ``<section
    begin="…"/>`` name) suffixed with the plate's ``PLATE N.`` label.

    Priority for the base name:
      1. ``{{x-larger|TITLE}}`` / ``{{larger|TITLE}}`` in the
         ``<noinclude>`` heading (``{{c|{{x-larger|ROUND TOWERS}}}}``).
      2. The first plain-text field of a ``{{rh|…}}`` /
         ``{{EB1911 Page Heading|…}}`` heading (the article-name slot).
      3. The ``<section begin="X"/>`` name (REGALIA's plate carries
         ``<section begin="Regalia"/>`` but a layout-template heading).
      4. ``PLATE (VOL. n, P. m)`` — last resort, no recognizable title.

    The plate number comes from the heading's ``{{sc|Plate N.}}``
    side-header (``_extract_plate_number``) or, when the label sits in a
    layout-table cell instead, from anywhere on the page
    (``_plate_label_from_content``).  A bare ``Plate.`` (no numeral)
    yields the ``, PLATE`` suffix so the plate's slug stays distinct
    from its parent article's."""
    plate_title: str | None = None
    header_match = re.search(r"<noinclude>(.*?)</noinclude>", raw, re.DOTALL)
    if header_match:
        hdr = header_match.group(1)
        # {{x-larger|TITLE}} / {{larger|TITLE}} — walk braces so a
        # nested {{uc|SHAKESPEARE}} inside {{x-larger|…}} doesn't
        # truncate the field at the inner `}`.
        inner = first_template_body(hdr, "x-larger")
        if inner is None:
            inner = first_template_body(hdr, "larger")
        if inner is not None:
            plate_title = _title_plaintext(inner).rstrip(",.")
        else:
            # {{rh|…|TITLE|…}} / {{EB1911 Page Heading|…|TITLE|…}} —
            # split on top-level pipes (brace-depth aware) for fields.
            for f in page_head_fields(hdr):
                clean = _title_plaintext(f)
                # A field that did NOT project to plain text is not a
                # headword — it is furniture the projection deliberately
                # refuses to delete (`{{gap}}`, the running-header's empty
                # left slot).  Rejecting it here moves on to the field that
                # DOES carry the name (`{{fs|180%|BOOKBINDING}}`); stripping
                # its braces instead manufactured the title `{{gap`.
                if "{{" in clean or "}}" in clean:
                    continue
                clean = clean.rstrip("}]")
                if (clean and len(clean) > 2 and not clean.isdigit()
                        and not re.match(r"^Plate\b", clean)
                        and re.search(r"[A-Za-z]{3,}", clean)):
                    plate_title = clean
                    break
    if not plate_title:
        secs = _match_section_begin(raw)
        if secs:
            name = (secs[0][2] or "").strip()
            if (name and not re.fullmatch(r"s\d+", name, re.IGNORECASE)
                    and re.search(r"[A-Za-z]{3,}", name)):
                plate_title = name.upper()
    if not plate_title:
        plate_title = f"PLATE (VOL. {volume}, P. {page_number})"

    plate_num = _extract_plate_number(raw)
    if plate_num is None:
        plate_num = _plate_label_from_content(raw)
    if plate_num:
        plate_title = f"{plate_title}, PLATE {plate_num}"
    elif plate_num is not None:
        plate_title = f"{plate_title}, PLATE"
    return plate_title

# A plate's content IS an image — bracket form OR the layout-template forms.
_PLATE_IMAGE = re.compile(
    r"\[\[(?:File|Image):|\{\{\s*(?:Css image|raw image|FIS?|framed image)\b",
    re.I)
_FRONT_TITLE_TMPL = re.compile(
    r"\{\{\s*eb1911\s+(?:half\s+)?title\s+page|\{\{\s*eb1911\s+\w+\s+copyright"
    r"|\{\{\s*eb1911\s+contributor\s+table", re.I)
_FRONT_BANNER = re.compile(r"ELEVENTH\s+EDITION", re.I)

def _is_front_matter_title(raw: str) -> bool:
    """A volume front page: a title-page template, or the ENCYCLOPÆDIA
    BRITANNICA / ELEVENTH EDITION banner standing BEFORE any image.  (A title
    page leads with the banner; a plate carries the same words only in an
    engraved credit AFTER its image — so position, not the substring, decides.)"""
    if _FRONT_TITLE_TMPL.search(raw):
        return True
    m = _FRONT_BANNER.search(raw)
    if not m:
        return False
    img = _PLATE_IMAGE.search(raw)
    return img is None or m.start() < img.start()


def is_plate(raw: str) -> bool:
    """A plate is an UNPAGINATED leaf that carries an image — its content IS the
    image.  A paginated leaf is article body; a text-only unpaginated leaf is
    front matter; a banner title page is front matter.  No prose heuristics."""
    return (folio_of(raw) is None
            and bool(_PLATE_IMAGE.search(raw))
            and not _is_front_matter_title(raw))

"""The Encyclopaedia Britannica, Eleventh Edition, as a book this engine builds.

Moved out of the engine's corpora.py (wikikit step 4): the engine defines what a
book IS; this module says what this book is.  Selected by the setting
``WIKIKIT_CORPUS=eb1911:EB1911`` (see book.env).
"""
from __future__ import annotations

import importlib

from wikikit.corpora import Corpus

# --- how many scanned pages each volume has ----------------------------------
# The fetch range.  EB1911's numbers were a bash array inside fetch_all.sh, a
# poor home for a manifest: it could not be tested, imported, or checked against
# anything.  They are reproduced here VERBATIM, not re-derived from
# _ARTICLE_PAGES below, which is a DIFFERENT fact — the span holding articles — and
# disagrees for volumes 20 and 29 (volume 29, the index, is not in it at all).

_EB1911_PAGES = {
    1: 1029, 2: 1027, 3: 1015, 4: 1031, 5: 1002, 6: 1017,
    7: 1008, 8: 1027, 9: 997, 10: 967, 11: 968, 12: 985,
    13: 985, 14: 953, 15: 994, 16: 1016, 17: 1039, 18: 1000,
    19: 1034, 20: 1054, 21: 1019, 22: 993, 23: 1069, 24: 1100,
    25: 1090, 26: 1104, 27: 1092, 28: 1091, 29: 982,
}


# --- where each volume's ARTICLES lie -------------------------------------
# Each volume opens with front matter (half-title, title page, copyright, the
# contributor / "initials and headings" list) and closes with the last article;
# some carry trailing blank or plate leaves.  The walk processes ONLY the
# article span, so front matter never enters it.  A STATIC fact about a fixed
# source: the first and last article LEAF of every volume were verified by eye
# against the page scans (2026-06-16, via ``tools/viewer/leaf_check.html``).
# Vol 29 (the Index) is not an article volume and has no entry.  Moved verbatim
# from the engine's volumes.py (wikikit step 5).

# volume -> (first_article_ws, last_article_ws), inclusive — ws/djvu page space
# (``SourcePage.page_number``).  Pages outside the span are front matter (before
# first) or trailing blank/plate/back matter (after last) and are NOT walked.
# Trailing comment = the verified IA-scan leaf pair (leaf_check.html).
_ARTICLE_PAGES: dict[int, tuple[int, int]] = {
    1:  (32, 1029),   # leaves 39..1044
    2:  (12, 1027),   # leaves 19..1048
    3:  (15, 1015),   # leaves 21..1026
    4:  (14, 1031),   # leaves 23..1048
    5:  (12, 1002),   # leaves 21..1024
    6:  (14, 1017),   # leaves 23..1032
    7:  (14, 1008),   # leaves 21..1016
    8:  (15, 1027),   # leaves 21..1034
    9:  (13, 997),    # leaves 21..1020
    10: (13, 967),    # leaves 23..984
    11: (13, 968),    # leaves 21..982
    12: (14, 985),    # leaves 21..994
    13: (14, 985),    # leaves 21..998
    14: (13, 953),    # leaves 19..980
    15: (14, 994),    # leaves 21..1030
    16: (15, 1016),   # leaves 21..1024
    17: (15, 1039),   # leaves 21..1058
    18: (15, 1000),   # leaves 19..1018
    19: (15, 1034),   # leaves 21..1062
    20: (19, 1048),   # leaves 21..1048
    21: (15, 1019),   # leaves 21..1034
    22: (15, 993),    # leaves 21..1002
    23: (14, 1069),   # leaves 21..1088
    24: (15, 1100),   # leaves 19..1118
    25: (15, 1090),   # leaves 21..1112
    26: (17, 1104),   # leaves 21..1118
    27: (15, 1092),   # leaves 21..1110
    28: (16, 1091),   # leaves 21..1106
}


# --- the hooks: the book's rules, imported on call ------------------------------
# The profile is read by every tool that asks where the book's files live, and
# none of those should load the heading classifier to find out.  Importing on
# call also keeps the profile out of an import cycle: the engine modules a hook
# lives in read `current_corpus()` at import, which is this module.

def _hook(module: str, name: str):
    """``module.name``, imported when first called."""
    def call(*args):
        return getattr(importlib.import_module(module), name)(*args)
    call.__name__ = call.__qualname__ = name
    return call


# --- the Britannica -----------------------------------------------------------
# Every value below is the constant that was already in the tree, moved here
# unchanged.  Phase 0's gate is a full rebuild that diffs to ZERO bytes, and
# that is only provable if this profile reproduces the old behaviour exactly.

EB1911 = Corpus(
    key="eb1911",
    title="Encyclopædia Britannica, Eleventh Edition",
    scan_name=lambda v: f"EB1911 - Volume {v:02d}.djvu",
    pages=_EB1911_PAGES,
    raw_dir="wikisource",
    # Where articles start: a caps-set bold headword at a block start.
    article_starts=_hook("eb1911.boundaries", "article_starts"),
    # Plates: an unpaginated leaf carrying an image; "AEGEAN CIVILIZATION, PLATE I".
    is_plate=_hook("eb1911.plates", "is_plate"),
    plate_title=_hook("eb1911.plates", "plate_title"),
    # Extra names for articles, merged in this order (a later source wins).
    alias_sources=(
        _hook("eb1911.aliases", "build_alias_map"),
        _hook("wikikit.xrefs.alias_table", "build_section_alias_map"),
        _hook("eb1911.aliases", "build_vol29_index_aliases"),
    ),
    # Who wrote what: initials-only signatures, bound through the front-matter
    # tables and the vol-29 master index.
    bind_contributors=_hook(
        "eb1911.contributors.resolve_contributors_post",
        "bind_contributors"),
    # Front matter: To This Edition · the 1910 Editorial Preface · the
    # Historical Preface, then the Reader's Guide.
    ancillary=_hook("eb1911.front_matter", "ancillary"),
    # Listed, not `KNOWN_DATA`: when the engine learns a new file, no book
    # should be found to "have" it by default.
    data_files=frozenset({
        "corrections.json", "hyphen_map.json", "contributor_aliases.json",
        "xref_adjudications.json", "maps.json", "link_exceptions.json",
        "genealogy_images.json", "mdx_sample.json", "tei_odd.xml",
        "templates/tei_readme.md", "templates/tei_source.xml",
        "templates/tei_corpus_source.xml", "epub_cover.jpg",
        "templates/mdx_description.html", "templates/mdx_description_sample.html",
        "templates/mdx_about.html", "templates/mdx_help_sample.html",
        "mdx_phrases.json", "reference_link_overrides.json",
    }),
    site="https://britannica11.org",
    short_name="Britannica 11",
    file_stem="Britannica11",
    slug="eb1911",
    key_prefix="EB1911:",
    urn="urn:britannica11",
    source_url="https://en.wikisource.org/wiki/1911_Encyclop%C3%A6dia_Britannica",
    search_name="Britannica title search",
    concept_doi="10.5281/zenodo.22072145",
    cover_volumes=frozenset({1}),
    derived_dir="data/derived",
    images_dir="data/images",
    subtitle="A Dictionary of Arts, Sciences, Literature and General Information",
    years="1910–1911",
    article_volumes=28,
    article_pages=_ARTICLE_PAGES,
    # The source leaves this plate empty; the dictionary excludes it.
    empty_records={"25-0483-dc502a":
                   "Empty source plate, also excluded by the corpus download"},
    sampler_volume=1,                # the free vol-1 sampler EPUB
)

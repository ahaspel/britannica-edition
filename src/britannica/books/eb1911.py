"""The Encyclopaedia Britannica, Eleventh Edition, as a book this engine builds.

Moved out of the engine's corpora.py (wikikit step 4): the engine defines what a
book IS; this module says what this book is.  Selected by the setting
``BRITANNICA_CORPUS=britannica.books.eb1911:EB1911`` (see book.env).
"""
from __future__ import annotations

from britannica.corpora import Corpus

# --- how many scanned pages each volume has ----------------------------------
# The fetch range.  EB1911's numbers were a bash array inside fetch_all.sh, a
# poor home for a manifest: it could not be tested, imported, or checked against
# anything.  They are reproduced here VERBATIM, not re-derived from
# ARTICLE_WS_RANGE, which is a DIFFERENT fact — the span holding articles — and
# disagrees for volumes 20 and 29 (volume 29, the index, is not in it at all).

_EB1911_PAGES = {
    1: 1029, 2: 1027, 3: 1015, 4: 1031, 5: 1002, 6: 1017,
    7: 1008, 8: 1027, 9: 997, 10: 967, 11: 968, 12: 985,
    13: 985, 14: 953, 15: 994, 16: 1016, 17: 1039, 18: 1000,
    19: 1034, 20: 1054, 21: 1019, 22: 993, 23: 1069, 24: 1100,
    25: 1090, 26: 1104, 27: 1092, 28: 1091, 29: 982,
}


# --- the Britannica -----------------------------------------------------------
# Every value below is the constant that was already in the tree, moved here
# unchanged.  Phase 0's gate is a full rebuild that diffs to ZERO bytes, and
# that is only provable if this profile reproduces the old behaviour exactly.

EB1911 = Corpus(
    key="eb1911",
    title="Encyclopædia Britannica, Eleventh Edition",
    scan_name=lambda v: f"EB1911 - Volume {v:02d}.djvu",
    boundary_style="typographic",
    pages=_EB1911_PAGES,
    raw_dir="wikisource",
    # Listed, not `KNOWN_DATA`: when the engine learns a new file, no book
    # should be found to "have" it by default.
    data_files=frozenset({
        "corrections.json", "hyphen_map.json", "contributor_aliases.json",
        "xref_adjudications.json", "maps.json", "link_exceptions.json",
        "genealogy_images.json", "mdx_sample.json",
        "templates/tei_readme.md", "templates/tei_source.xml",
        "templates/tei_corpus_source.xml", "epub_cover.jpg",
        "templates/mdx_description.html", "templates/mdx_description_sample.html",
        "templates/mdx_about.html", "templates/mdx_help_sample.html",
        "mdx_phrases.json", "fake_recursion_exceptions.json", "reference_link_overrides.json",
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
)

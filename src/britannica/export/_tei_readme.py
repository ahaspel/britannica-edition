"""The README that ships inside the TEI bundle.

Its own module because it is prose, not code: keeping a 40-line document inside
a function makes the function unreadable and the document unreviewable.
"""

TEI_README = """# Encyclopaedia Britannica, 11th Edition — a TEI P5 edition

{n:,} articles, one TEI document each, named by the article's stable id — the
same id as its URL: https://britannica11.org/article/<id>

`teiCorpus.xml` is a CATALOG: a TEI corpus header plus an XInclude for every
member. Every member validates on its own against the TEI Consortium's `tei_all`
schema. That is checked for all {n:,} on every build, and the build fails if any
one of them does not.

## Ids are document-scoped

Each document is self-contained — it declares its own `respStmt` and its own
`rendition` set — so it can be read, validated and cited alone. The consequence
is that `xml:id`s are unique WITHIN a document and not across the corpus:
resolving every XInclude into a single tree produces duplicate ids (`wikisource`
once per file, and `section-history` in every article that has such a section).

This is ordinary for a file-per-member TEI corpus. Process members individually,
or rewrite ids on assembly.

`eb1911.odd.xml` is the TEI customisation: which part of TEI this edition uses,
what each rendition means, and how identifiers are scoped. It is derived from the
emitted corpus rather than from intention, and is itself valid TEI.

## What is encoded

Only what the source marks. There is no `persName`, `placeName` or `date` markup:
EB1911 does not mark its persons and places, so emitting them would mean
inferring them, and an inferred entity is an assertion in the editor's voice
about a source that made no such claim.

Presentational distinctions the source does make — small caps, centring, floats,
rules — are carried with `@rendition`, declared once per document in `tagsDecl`.
Mathematics is `<formula notation="TeX">`. Tables, figures, footnotes and
cross-references are encoded structurally rather than as prose.

## Provenance has three parties, and they are distinguished

The text is EB1911's. The transcription is the Wikisource contributors', credited
in every `respStmt`. Where the transcribers added something the printed page does
not contain — chiefly transliterations of Greek — it is carried as
`<note type="transliteration" resp="#wikisource">`, attributed rather than merged
silently into the text, so a reader can tell the 1911 page from a later editor.

Pages whose Wikisource transcription is unproofread carry a warning in
`<editorialDecl>`; mathematics on those pages in particular may be corrupt.

## Citing this edition

Archived at Zenodo. Cite the CONCEPT DOI, which always resolves to the current
version:

    https://doi.org/10.5281/zenodo.22072145

    Haspel, A. (2026). Encyclopædia Britannica, Eleventh Edition: a TEI-P5
    edition. Zenodo. https://doi.org/10.5281/zenodo.22072145

To pin one release instead, use its version DOI — 2026.1 is
`10.5281/zenodo.22072146`. Every document also carries the concept DOI in its
own `<publicationStmt>`, so a single article that has travelled away from this
bundle still says where it came from.

## Licence

CC BY-SA 4.0, following the Wikisource transcription this is encoded from.
The underlying 1911 text is in the public domain.
"""

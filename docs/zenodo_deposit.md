# Zenodo deposit — the TEI edition

**Status: deposited 2026-08-23**, DOI `10.5281/zenodo.22072146`, against the
tagged tree `tei-2026.1`. Later versions can go through the API, which inherits
this metadata.

The DOI above is the one Zenodo reserved before publishing, which is the VERSION
DOI — fixed to this deposit. Publishing also mints a CONCEPT DOI that always
resolves to the newest version; record it below when it appears, because that is
the one the website should cite.

| DOI | value |
|---|---|
| **concept** (all versions — cite this on the site) | `10.5281/zenodo.22072145` |
| **version** (this deposit, 2026.1) | `10.5281/zenodo.22072146` |

Published 2026-08-23 and verified against the live record: licence `cc-by-sa-4.0`,
creator `Haspel, Aaron` with the ORCID attached, file `eb1911-tei.tar.gz`
105,428,653 bytes, `md5:5aaf18d8b5b4eae2c3553b150646c5fb` — identical to the
local bundle and to the copy the website serves.

Citation:

> Haspel, A. (2026). *Encyclopædia Britannica, Eleventh Edition: a TEI-P5
> edition* (Version 2026.1) [Dataset]. Zenodo.
> https://doi.org/10.5281/zenodo.22072146

## Do the first one by hand

A published Zenodo record **cannot be deleted, and its files cannot be replaced** —
you can only publish a new version beside it. The DOI is a permanent public
promise. That is the whole argument for filling the form in once, carefully,
rather than discovering afterwards that an API call put the wrong string in a
field nobody can now edit.

Only the TEI is deposited. The corpus bundle's audience is machine learning and
text mining, and it already has HuggingFace; the TEI's audience is scholarly, and
this is the artifact someone cites in a footnote. A second deposit can always be
added later — an over-broad first one cannot be narrowed.

## The record

| field | value |
|---|---|
| **DOI** | `10.5281/zenodo.22072146` — reserved 2026-08-23 |
| **Upload type** | Dataset |
| **Title** | Encyclopædia Britannica, Eleventh Edition: a TEI-P5 edition |
| **Version** | `2026.1` |
| **Language** | English (eng) |
| **License** | Creative Commons Attribution-ShareAlike 4.0 International |
| **File** | `eb1911-tei.tar.gz` — `data/derived/eb1911-tei.tar.gz`, 105,428,653 bytes, sha256 `c629bb566d4bd607bd86960a40f1251dc3c1a1abbf802dc3b2e649ae1cfc4d6b` (verified identical to the copy at britannica11.org/download/, 2026-08-23) |

### Creators

The delicate field, because three parties are involved and only one of them is
you. The Encyclopædia's 1,507 signed contributors wrote the text; the Wikisource
contributors transcribed it; this edition encoded it.

- **Creator** — **Aaron Haspel**, ORCID **0009-0005-2497-5739**
  (https://orcid.org/0009-0005-2497-5739). Enter it family-name-first —
  `Haspel, Aaron` — which is the form Zenodo expects and what makes the
  generated citation read "Haspel, A. (2026)". Check digit verified. It is a permanent
  identifier for the person — the same idea as this edition's own contributor
  signatures, a key that survives a name being spelled differently. It makes the
  DOI resolve to a person rather than a string, and the deposit will appear on the
  ORCID record.
- **Contributor** (type: Other, role *transcription*) — **Contributors to
  Wikisource**, as a single corporate name.

**Not Hugh Chisholm, and not the 1911 contributors.** The record describes the
DEPOSITED RESOURCE — this encoding — not the Encyclopædia. Listing Chisholm as
creator makes every generated citation read "Chisholm, H. (2026). Encyclopædia
Britannica … [Data set]. Zenodo.", which attributes a 2026 dataset to a man who
died in 1924 and implies he made it. It is wrong twice over: even for the print
work he was editor-in-chief, not author. The print work has its own bibliographic
identity and does not need this DOI; that identity belongs in the description and
in the `isDerivedFrom` relation, which is exactly how a scholarly edition cites
the work it edits.

Naming yourself as creator is not a claim over the text. It is what makes the
citation resolve to the right object.

**The transcribers are credited as a corporate body**, not individually: there are
thousands, many pseudonymous, and the roster changes. "Contributors to Wikisource"
is the form academic citation already uses for wiki-sourced work, and together
with the `isDerivedFrom` link it satisfies CC BY-SA's attribution requirement —
a licence obligation, not a courtesy.

### Description

> A TEI-P5 encoding of the complete eleventh edition of the Encyclopædia
> Britannica (Cambridge, 1910–1911), edited by Hugh Chisholm and written by
> some 1,500 signed contributors: 37,225 articles, one TEI document each,
> named by a stable identifier that is also the article's address at
> britannica11.org.
>
> Unlike a plain-text or Markdown release, this encoding carries what the printed
> page carried — small capitals, centring, rules and floats, tables and figures
> as structure rather than as prose, mathematics as TeX, footnotes attached where
> they belong. Every document validates against the TEI Consortium's own
> `tei_all` schema; that is checked for all 37,225 on every build, and the build
> fails if any one of them does not. The customisation is included as
> `eb1911.odd.xml`.
>
> Provenance is distinguished rather than flattened. The text is the
> Encyclopædia's; the transcription is the work of the contributors to
> Wikisource, credited in every document; the encoding is this edition's. Where
> the transcribers added something the printed page does not contain — chiefly
> transliterations of Greek — it is carried as an attributed note rather than
> merged silently into the text, so a reader can tell the 1911 page from a later
> editor. Pages whose transcription is unproofread are marked as such.
>
> No entity markup is asserted. The Encyclopædia does not mark its persons and
> places, so producing `persName` or `placeName` would mean inferring them, and
> an inferred entity is an assertion in the editor's voice about a source that
> made no such claim.

### Related identifiers

These are how the record joins the rest of the world, and they are easy to skip:

| relation | identifier |
|---|---|
| is derived from | `https://en.wikisource.org/wiki/1911_Encyclopædia_Britannica` |
| is part of / is published in | `https://britannica11.org` |
| is identical to (other format) | `https://huggingface.co/datasets/britannica11/eb1911` |
| is documented by | `https://britannica11.org/download.html` |

### Keywords

TEI, TEI P5, Encyclopædia Britannica, Encyclopaedia Britannica,
Encyclopedia Britannica, Eleventh Edition, 1911, digital edition,
reference works, history of knowledge, XML, public domain

All three spellings on purpose. The TITLE keeps the ligature, because that is how
the work prints its own name; keywords are a finding aid, not a claim about the
work, and nobody types `æ` into a search box. The `ae` digraph is the common
scholarly form and the bare `e` is what most people will actually search for.

## Cadence

Deposit **editions, not builds**. The corpus is rebuilt several times a week and
every published version is permanent; nobody wants two hundred of them. Deposit
when a citer would care — a corrections campaign, a structural improvement, new
content — and tag the commit so the DOI corresponds to a known tree. Realistically
a few times a year.

Zenodo issues a *concept* DOI that always resolves to the latest version plus a
version DOI for each release. Cite the concept DOI on the site; the version DOI
is what a paper pins.

## After depositing

- Put the DOI on the download page and in the bundle README.
- Add it to the TEI header as an `idno`, so a document carries its own citation.
- Consider listing the edition with the TEI Consortium's "Projects Using the TEI",
  which is where that audience browses.

# Zenodo deposit — the TEI edition

**Status: 2026.2 published 2026-09-21**, DOI `10.5281/zenodo.22876664`, against
the tagged tree `tei-2026.2` (`651981c`). The first deposit, 2026.1, was
published 2026-08-23 as `10.5281/zenodo.22072146` against `tei-2026.1`; both
sit under one concept DOI. Later versions can go through the API, which inherits
this metadata — or through the web form's "New version", which is how 2026.2 was
made.

The DOI above is the one Zenodo reserved before publishing, which is the VERSION
DOI — fixed to this deposit. Publishing also mints a CONCEPT DOI that always
resolves to the newest version; record it below when it appears, because that is
the one the website should cite.

| DOI | value |
|---|---|
| **concept** (all versions — cite this on the site) | `10.5281/zenodo.22072145` |
| **version** — 2026.1 | `10.5281/zenodo.22072146` |
| **version** — 2026.2 | `10.5281/zenodo.22876664` (published 2026-09-21) |

Published 2026-09-21 and verified against the live record: version `2026.2`,
licence `cc-by-sa-4.0`, creator `Haspel, Aaron` with the ORCID attached, and
exactly ONE file — `eb1911-tei.tar.gz`, 105,497,636 bytes,
`md5:3c1d7a71a3a892497f62316158dcdd80`, matching the local bundle byte for byte.
(Zenodo reports MD5 where we record SHA-256, so the comparison has to be made in
its terms; the SHA-256 is `0f9967a4…94ae7`. The single-file check matters because
a new version INHERITS the previous version's files, and a second copy could not
be removed after publishing.)

The concept DOI never changes and is the only one the site should cite; each
deposit mints its own version DOI, which is what a paper pins. Neither is ever
typed into the form — Zenodo assigns them, and the reserved value IS the version
DOI for the deposit being prepared.

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

### Is one warranted yet?

"When a citer would care" is the right test and a hard one to apply months later
with a long commit log in front of you. It comes down to a single question: **did
anything in the TEI BUNDLE change?** Most work on this project does not touch it.

Deposit when, since the last deposit tag, **any** of these is true:

1. **Source corrections landed** — `data/corrections.json` gained entries. These
   change the TEXT, which is what a citer quotes, and they are the clearest case
   of the doc's "corrections campaign".
2. **The encoding changed** — `src/britannica/export/tei.py`, or a producer whose
   markers TEI carries. Note that TEI carries more than the declared
   `RENDITIONS`: anything parametrised rides as a literal `@style`, so a producer
   change can reach the bundle without touching `tei.py` at all.
3. **The article inventory changed** — articles added, removed or re-bounded, so
   a citation by filename could resolve to something else.

Do NOT deposit for: viewer CSS, EPUB or MDX packaging, search ranking or speed,
topic placement, download-page copy, reader tooling. None of it is in the bundle.
A rebuild alone is not a reason either — the bundle is rebuilt every time.

The evidence, all measurable, none of it requiring the old bundle on disk:

```
git rev-list --count <last-tag>..HEAD
git diff --stat <last-tag>..HEAD -- src/britannica data/corrections.json
git show <last-tag>:data/corrections.json      # entry count then, vs now
ls -l data/derived/eb1911-tei.tar.gz           # size vs the deposited figure above
```

**Worked example — 2026-09-19, warranted (criteria 1 and 2).** 29 commits since
`tei-2026.1`; `corrections.json` 150 → 258 entries (+72%); bundle 105,428,653 →
105,504,389 bytes; 227 figure placements adjudicated against the scans and 58
captionless figures that carried no placement at all now carrying one — which
reaches the bundle as `@style`, not `@rendition` (checking only the declared
renditions says "no float in the TEI", and that is wrong). Also the mojibake
repairs, DNB citation unlinking, and table borders taken from the source.

## 2026.2 — ready to deposit (2026-09-21)

The 2026-09-19 example above was written when a deposit became warranted; none
was made, so its changes belong to THIS version along with everything since.
Zenodo's "New version" on record `10.5281/zenodo.22072146` inherits the metadata
— change the version string, the file, and the description of what moved.

| field | value |
|---|---|
| **Version** | `2026.2` |
| **DOI** | `10.5281/zenodo.22876664` — reserved 2026-09-21 |
| **File** | `eb1911-tei.tar.gz` — 105,497,636 bytes, sha256 `0f9967a444ee94d880252592679dc985df868cd6707f65e584c20881cf194ae7` (verified byte-identical to the copy at britannica11.org/download/, 2026-09-21) |
| **Tag** | `tei-2026.2`, on `651981c` — the tree the rebuild that produced this bundle ran from, NOT HEAD (the word-count and release-default commits landed after it and are not in the bundle) |

Evidence, by the criteria above — **1 and 2 met, 3 not**:

* **Source corrections** (criterion 1): `corrections.json` 135 → 235 entries
  (+74%) since `tei-2026.1`. 105 of them make `align=right` explicit on figures
  whose side was read off the scan.
* **The encoding changed** (criterion 2): paragraph structure. The book sets
  prose FLUSH where a display block cut a sentence in half and INDENTS it where
  a new paragraph starts; we indented both, because the transcription does not
  record the difference and Wikisource renders EB1911 with no `text-indent` at
  all. 1,051 articles now carry different `<p>` structure — 999 paragraph opens
  removed where a sentence ran on, 2,161 added after a note. Also `br_stack`,
  which restored a line break dropped from 8 structural formulae.
* **The inventory did NOT change** (criterion 3): 37,225 articles, the same as
  2026.1, all valid against `tei_all`.

38 commits since the tag; bundle 105,428,653 → 105,497,636 bytes (+68,983).

A citer who quoted a paragraph boundary, or the text of a corrected page, would
get a different answer from the two versions — which is the test the cadence
section sets, and why this is a version rather than a silent replacement.

## After depositing

- Put the DOI on the download page and in the bundle README.
- Add it to the TEI header as an `idno`, so a document carries its own citation.
- Consider listing the edition with the TEI Consortium's "Projects Using the TEI",
  which is where that audience browses.

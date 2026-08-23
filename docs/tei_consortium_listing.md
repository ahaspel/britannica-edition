# TEI Consortium — "Projects Using the TEI" listing

**Status: drafted 2026-08-23, submission pending authorisation.** The form is
moderated; account approval came first. Everything below is ready to paste.

## Fields

| field | value |
|---|---|
| **Project name** | Encyclopædia Britannica, Eleventh Edition — a TEI-P5 edition |
| **Project URL** | `https://britannica11.org` |
| **Implementation** | TEI P5 uncustomized |
| **Language of the data set** | `en` |
| **Language of the framework** | `en` |
| **Period of the project** | begun March 2026, ongoing (stated in the description) |
| **Contact** | Aaron Haspel · ahaspel@gmail.com · https://orcid.org/0009-0005-2497-5739 |

The project URL is the SITE, not the DOI: someone browsing the directory wants
to read the edition, and the site leads to every download. The DOI belongs in a
data/download field if the form offers one.

## Description of the project

> **Content.** A complete TEI-P5 encoding of the eleventh edition of the
> Encyclopædia Britannica (Cambridge, 1910–1911): 37,225 articles, one TEI
> document each, named by a stable identifier that is also the article's address
> on the web. The TEI is generated from the edition's own marker stream, the
> same source that produces the website and the EPUB, rather than converted from
> finished HTML. Every document validates against the TEI Consortium's `tei_all`
> schema on every build and the build fails if a single one does not.
> Presentational distinctions the printed page makes are carried with
> `@rendition`, declared per document in `tagsDecl`. No entity markup is
> asserted: the Encyclopædia does not mark its persons and places, so `persName`
> or `placeName` would mean inferring them, and an inferred entity is an
> assertion in the editor's voice about a source that made no such claim.
>
> **Purpose.** The eleventh edition has long circulated as plain text and as
> unstructured scans, forms in which its tables, mathematics, figures and
> typography are simply lost. The purpose here is to publish it as an edition
> rather than a text dump — one that carries what the printed page carried, and
> that distinguishes its three hands: the text is the Encyclopædia's, the
> transcription is the work of the contributors to Wikisource (credited in every
> `respStmt`), and the encoding is this edition's. Transcriber additions,
> chiefly transliterations of Greek, are carried as attributed notes rather than
> merged silently, and unproofread pages are flagged in `editorialDecl`. The
> project began in March 2026 and is ongoing, with the corpus rebuilt
> continuously and editions deposited at Zenodo a few times a year; the current
> release is 2026.1, DOI 10.5281/zenodo.22072145. Freely available under
> CC BY-SA 4.0.

The ODD is deliberately NOT mentioned here — it lives in "details of
implementation" below. Saying "the customisation is published with the corpus"
in the same submission that answers "uncustomized" reads as a contradiction to
exactly the audience that would notice.

## Details of implementation

> Every document validates against the TEI Consortium's unmodified `tei_all`
> schema; all 37,225 are checked on every build and the build fails if one does
> not. A project ODD (`eb1911.odd.xml`) ships with the corpus, but it is
> descriptive rather than constraining — derived by scanning the emitted
> documents rather than written from intention, it records which subset of TEI
> the edition actually uses. The external standard does the checking.
>
> One TEI document per article, named by a stable identifier that is also the
> article's URL. A `teiCorpus` catalogue binds them with XInclude, but members
> are self-contained and meant to be processed individually: each declares its
> own `respStmt` and its own renditions, so `xml:id` values are unique within a
> document and not across the corpus — resolving every XInclude into one tree
> produces duplicates by design.
>
> Presentational distinctions are carried with `@rendition`, declared once per
> document in `tagsDecl` so the set is enumerable in the header rather than
> scattered through the corpus; distinctions carrying a value rather than a
> class — a font size, a transform — ride in `@style` as CSS. Section
> identifiers take the form `section-slug` and are the same anchors the website
> uses, so a TEI identifier and a URL fragment name the same place.
>
> No entity markup is asserted — no `persName`, `placeName`, `orgName` in the
> text, or `date`. The Encyclopædia does not mark its persons and places, so
> producing them would mean inferring them, and an inferred entity is an
> assertion in the editor's voice about a source that made no such claim.
>
> The TEI is generated from the edition's own marker stream — the same source
> that produces the website and the EPUB — rather than converted from finished
> HTML.

## Other related resources

> The TEI edition is archived at Zenodo with a citable DOI:
> https://doi.org/10.5281/zenodo.22072145 (concept DOI, resolving to the current
> version). All formats are listed at https://britannica11.org/download.html —
> the TEI corpus, a plain-text corpus with knowledge graphs, and an EPUB. The
> edition is encoded from the Wikisource transcription of the eleventh edition,
> https://en.wikisource.org/wiki/1911_Encyclopædia_Britannica, which is also why
> it is distributed under CC BY-SA 4.0. A machine-learning mirror of the same
> corpus, in plain text and Markdown rather than TEI, is at
> https://huggingface.co/datasets/britannica11/eb1911.

The Payhip EPUB is deliberately absent: a paid link in a scholarly directory
entry reads as promotional, and the download page leads there anyway.

## Licence

> Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
> https://creativecommons.org/licenses/by-sa/4.0/ — The underlying 1911 text is
> in the public domain; the ShareAlike terms follow the Wikisource transcription
> the edition is encoded from.

The second sentence stays even where the field is short. Without it a reader
wonders why a public-domain work carries a copyleft licence, and the answer —
that it follows the transcription, not the text — is the honest one.

## Keywords

    Encyclopædia Britannica, Encyclopaedia Britannica, Encyclopedia Britannica,
    Eleventh Edition, 1911, encyclopaedias, reference works, history of
    knowledge, digital edition, scholarly editing, ODD, TEI P5, public domain

Not the Zenodo keyword list: `TEI` and `XML` are noise in a directory where
everything is TEI, so that space goes to subject terms, which is what people
browse by. `ODD` stays — in this audience it signals a real customisation
document, which most listings cannot point at. All three spellings of
Encyclopaedia, because nobody types `æ` into a search box.

## After it is listed

- The TEI-L mailing list is where this audience actually notices new work, and a
  37,225-document corpus that validates against `tei_all` on every build, with a
  DOI and a published ODD, is a more substantial announcement than most.
- Consortium membership is separate and paid, and is not required for this
  listing.

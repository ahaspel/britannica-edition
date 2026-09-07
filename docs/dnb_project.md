# The DNB — a sister project on the same code

**Status: PHASES 0 AND 1 DONE (2026-09-07).**  The seam is in and proven inert;
the whole corpus is imported.
Everything below marked MEASURED was run against real Wikisource pages through
the real pipeline; everything marked UNKNOWN has not been tested.  The
2026-08-29/30 session in [`status.md`](status.md) carries the raw numbers and
the mistakes made getting them.

The framing is the user's: **a new corpus is a different BUILD, not a different
codebase — its closest analogue is the EPUB build or the markdown build.**  One
repository, one pipeline, a second corpus and a second site.

---

## Why this is cheap

Not because the code was written to be general.  Because we implemented
*Wikisource*, and the DNB is written in it: `{{sc}}`, `{{hws}}`/`{{hwe}}`,
`{{rule}}`, `<section begin=>`, `<pagequality>`, and
`{{X footer initials|Name|Initials}}` are conventions of the platform, not of
the Britannica.

And because the DNB is a plainer book: no plates, no mathematics, no foldout
maps, no two-column tables, no front-matter contributor rolls to parse, and
article boundaries the transcribers marked explicitly instead of leaving to
typography.  Both facts are load-bearing; neither alone would give this result.

## What was measured

| | |
|---|---|
| scale | 63 volumes, **29,186 pages, ~25M words** (EB1911: 28 vols, 40M) |
| article titles | **28,299**, enumerated from mainspace; 27.9% carry a disambiguator |
| render fidelity | 100 pages across vols 1/20/45/63: **0 crashes, 0 leaks** except `{{DNB XX}}` |
| end-to-end build | **88 articles** detected → walked → exported → rendered, **0 failures** |
| content preservation | 432,588 chars out vs 428,923 in — **ratio 1.01** |
| contributors | **1,112 people**; 87 of 88 articles signed, **exactly one signature each** |
| cross-references | `[q. v.]` resolves **71.7%** on our own `NameIndex`, ~2% error on the labelled control |
| images | `[[File:` on **exactly one page** in the whole corpus (a 1901 Supplement frontispiece) |

## The five corpus-specific pieces

Everything else — `SegmentInfo`, `DetectedArticle`, `persist_articles`,
`walk_article`, `export_articles_to_json`, `render_article`, `NameIndex`,
`ContributorIndex` — ran unmodified.

| # | piece | status |
|---|---|---|
| 1 | page-title pattern | one string; same shape, same zero-padding |
| 2 | boundary detection | **written** (~40 lines); `<section>` runs, not typography |
| 3 | headword shape | **the one genuine extension** — see below |
| 4 | contributor binding | template-name → roster; a different MECHANISM, not a parameter |
| 5 | running-header template | one string; feeds the printed-page map |

### 3 is the only real code change

EB1911 always puts the whole headword inside the bold:

    «B»STEVENSON, ROBERT LEWIS BALFOUR«/B» (1850-1894), British essayist
    [[Author:…|«B»{{uc|Colenso, John William}}«/B»]] (1814-1883), bishop

The DNB ends the bold at the comma:

    «B»JOHNSON,«/B» SAMUEL (1709-1784), lexicographer

`_title_span`'s rule is "first «B» through the LAST «B» reachable across
connective gaps" — it extends bold-to-bold and cannot reach plain text.  So the
DNB needs `_title_span` to RECOGNISE MORE, not a policy override.

Do **not** fix this by writing `article.title = section_name`.  That was tried
in the probe: it corrects the field and leaves the `<h1>` reading `JOHNSON` with
`SAMUEL` stranded at the head of the body, because the H1 renders from the
in-stream «TITLE» node.  It is also the exact override that was DELETED for
EB1911, for manufacturing ALGEBRAB out of continuation sections.
[[feedback_recursion_is_recognition]]

### 4 is a different mechanism, not a parameter

EB1911 writes `{{EB1911 footer initials|Name|Initials}}` INLINE in the article,
so the name is in the text.  The DNB writes a bare `{{DNB AWW}}`; the name lives
in the TEMPLATE.  DNB binding is therefore template-name → roster lookup.

Our `ContributorIndex` was pointed at the DNB roster as a control: **69 of 87
bound by initials alone, 18 abstained, 0 wrong** — the never-guesses design
holding on a corpus it has never seen.  But 98 DNB initials strings have more
than one owner, and reducing `{{DNB TS Smith}}` to `T. S.` throws away a key
that Wikisource already disambiguated.  **The DNB does not exercise the
resolver; it hands us the answer.**  Template → person is 87/87 once `#ifeq` is
handled.

Roster accounting, all 1,295 `Template:DNB *` pages:

| shape | n | meaning |
|---|---|---|
| simple `footer initials` | 1,164 | direct |
| `Ambiguous DNB initials` | 87 | Wikisource itself marks these unresolved |
| `#REDIRECT` alias | 39 | follow the redirect |
| `#ifeq` conditional | 5 | two people, switched by supplement |

## What the DNB does not need at all

No image store, no image download, no plate detection, no plate-parent binding,
no map recovery, no image-coverage gate, no math measurement, no wide-table or
wide-math handling, no classified TOC or topic index, no Reader's Guide.
Several have no input whatsoever: `_split_out_plates` will find nothing.

## The page map is arithmetic

EB1911 needs a monotonic-anchor algorithm because plates are unnumbered pages
that displace every printed number after them.  The DNB has no plates, so
`printed = ws - k`, one k per volume.  Probing 12 pages in each of 63 volumes:
**54 of 60 volumes have every probe agreeing with the modal offset**, and the 6
strays are transcription typos rather than shifts — vol 10 types `371` for `271`
on a page whose neighbours all sit at offset 8.  A mode absorbs them.

## Phases

### Phase 0 — the seam.  ALL of the risk lives here.

One `Corpus` profile carrying the five values, threaded to the sites that need
them.  The hazard is not the DNB: it is the **37,225 live EB1911 articles**, and
every site touched is shared code.

**GATE: a full EB1911 rebuild that snapshot-diffs to ZERO byte changes, before
any DNB work builds on it.**  If the profile cannot be introduced without moving
EB1911 output, stop and rethink the seam rather than rebaselining.
[[feedback_regression_mass]] [[feedback_no_wholesale_rebaseline]]

### Phase 1 — import

29,186 pages, roughly 75 minutes at a polite rate, into its own database.  Low
risk; the fetcher is one pattern away.

### Phase 2 — build

The detector is written.  Headword recognition is the one code extension.  Then
the full-corpus run.  Existing gates apply: mangled-marker (the `{{DNB XX}}`
count should fall to zero once bound), content-preservation ratio, TEI
validation.  **UNKNOWN: everything measured so far is 0.3% of the corpus.  Scale
surprises, if there are any, surface here.**

### Phase 3 — resolution

Contributors (dict lookup, plus redirects and `#ifeq`).  `{{DNB lkpl}}` through
`LinkResolver` against the DNB title index.  `[q. v.]` via the prototyped
extractor, with the fisher for the ~19% that come back ambiguous.

### Phase 4 — site

The viewer ENGINE ports nearly free — `viewer.html` carries 3 EB1911 mentions,
`index.html` 1, `search.html` 1.  The EB1911-specific files are all CONTENT
pages, which a sister site needs its own of anyway.

### Phase 5 — deploy

New bucket, distribution, Meilisearch index.  The CloudFront `stable_id` router
is corpus-independent.  `deploy.sh` hardcodes `britannica11.org` throughout and
needs the same parameterisation as Phase 0.

### Phase 6 — artifacts

Corpus bundle, TEI, EPUB and HuggingFace are corpus-agnostic exporters.  A
separate Zenodo deposit and DOI if it should be citable.

## Open decisions

1. **Scope — DECIDED 2026-09-07: everything.**  63 volumes + all three
   supplements + the Errata.  ~31,150 biographies over 71 scan volumes.  The
   supplements are fully transcribed (1901: 1,037 articles; 1912: 1,641; 1927:
   477), each carries its own **List of Writers** — a second, independent
   contributor roster — and they are where the five `#ifeq` conditionals point,
   so importing 63 alone leaves those unresolvable by construction.
2. **Domain.**
3. **Scans** — the DjVu page images exist at the Internet Archive.  EB1911 ships a
   scan viewer; the DNB could skip it.
4. **Citability** — its own Zenodo deposit, or not.

## Probe artifacts

The scratch database `dnb_probe` (Postgres, separate from `britannica`) holds
the 81 loaded pages and 88 detected articles.  Every probe script asserts on
`engine.url` before touching anything.  The probe scripts themselves live in the
session scratchpad and are not part of the repository.


---

# What Phase 0 established (2026-09-07)

`src/britannica/corpora.py` — a `Corpus` profile selected by `Settings.corpus`,
beside the `database_url` that selects the same book's pages.  **No shared
signature changed**, so EB1911's code path is byte-identical by construction and
the gate proves it rather than hoping.

**GATE PASSED.**  A full 58-minute rebuild, every artifact compared against what
production is serving: `articles.jsonl` 270,006,037 bytes, plus contributors,
xref edges, topics and schema — all IDENTICAL.  All build gates green (TEI: every
one of 37,225 articles validates; link census 203 to 203, net +0).

## Three things this plan had wrong

**The page-title pattern is not "one string, same zero-padding".**  That fits the
63 main volumes and silently mis-addresses every supplement.  There are FIVE
naming conventions across 71 scan volumes: zero-padded for the main series,
ROMAN numerals for 1901, unpadded arabic for 1912, no number at all for 1927,
and the Errata.  The profile carries a FUNCTION, and the volume numbers are ours
(1-63 main, 64-66 the 1901 supplement, 67-69 the 1912, 70 the 1927, 71 Errata),
which keeps the pipeline's `volume: int` working untouched.

**Two of the five "pieces" need no parameterising at all.**  `PAGE_HEAD_RE` is
already the union `rh|running header|eb1911 page heading`; the DNB uses the first
two and the third simply never occurs in its text, so a narrower copy would
invent a difference and leave two patterns to drift.  And the contributor footer
is not a pattern difference: EB1911 puts the name INSIDE the template, the DNB
puts it in the template's NAME.  A regex swap would hand the DNB a reader hunting
a field it does not have.  It arrives in Phase 3 with the roster lookup that
reads it — a field arrives when its consumer does.

**The gate needed a better baseline than a local snapshot.**  Article JSONs carry
a database autoincrement `id`, reassigned on every rebuild, so hashing whole
files reports total change no matter what code did.  Production IS the previous
build's output; the corpus bundle gives complete coverage in one request; and the
commits since the last deploy touch only serve tooling, the TEI README and the
EPUB build.  Compare against the live artifact, not against a snapshot of your
own making.

# The 1904 Errata — a source in its own right

There is no 1920s revised edition to import.  The DNB was reissued in **1908-09**
in 22 volumes, incorporating the 1904 Errata, and **Wikisource has no separate
transcription of it**.  The 1920s item is the 1927 supplement: new biographies,
not a revision.

The reissue's value reaches us through the Errata volume, which IS fully
transcribed — **314 pages, 3,469 corrections keyed to 3,413 distinct articles**,
each already bound to its article by a `<section begin="Name">` its transcribers
wrote.  Binding is a dictionary lookup, not a matching problem.

**Append, do not rewrite.**  That is Wikisource's own model and it is verifiable:
in the rendered article for `Abbot, George (1562-1633)`, the phrase "Early in
1614" appears TWICE — once in the body as 1885 printed it, once in the apparatus
reading *for Early in 1614 read In March 1611-12*.  Rewriting the body would
destroy the distinction between what the first edition said and what its editors
later corrected.

Wikisource has annotated 3,231 of the 3,413 by hand.  **Bind all 3,469 ourselves**
rather than inherit a merge that is still in progress: importing the partial
state gives a corpus where coverage depends on the date we imported, and one
mechanism beats half-trusting a second.


# Phase 1 — done (2026-09-07)

**33,824 pages, 71 volumes, 179,350,869 characters** in a `dnb` database of its
own.  Zero volumes disagreed with the manifest, zero absent, 73 blank scans
(0.2%), no rate-limits.  Roughly 40 minutes.

The fetcher is now BATCHED — 50 titles per request, `maxlag=5` — because one
page per request with a 3s delay is 28 hours for this corpus and 24 for the
Britannica.  Verified byte-identical to the single-page method by fetching the
same pages both ways.  The per-volume page counts moved from a bash array in
`fetch_all.sh` into the corpus profile, EB1911's reproduced verbatim, so
`--all` walks either book.  `tools/pipeline/fetch_all.sh` is now redundant.

**The manifest is what would have caught a wrong scan name.**  All 71 volumes
returned exactly the page count measured from their DjVu file — the check that
matters most for the eight supplement volumes, whose five naming conventions
were the likeliest thing to be silently wrong.

# A finding about EB1911, from asking how stale it is

Sampled 972 pages: **21.7% edited since our April 2026 fetch**; of a 576-page
sample, **12.2% substantively** (~3,600 corpus-wide), 5.7% whitespace only,
1.7% proofread-status only.

The dominant substantive edit is a MARKUP MIGRATION with a visible-text
consequence:

    -the <span title="amended from 'lire'">life</span> exactly
    +the {{SIC|lire|life}} exactly

    before: the reader sees "life" (the emendation), hover shows the original
    after:  the reader sees "lire" (as printed),      hover shows the emendation

Wikisource is moving to show the page AS PRINTED and carry the correction as
apparatus — the same principle we chose for the DNB errata.

**We are currently inconsistent, and `sic` is miscategorised.**  Our corpus holds
1,240 hand-rolled spans (we display the emendation, tooltip preserved by
`_handle_title_spans`) and 111 `{{SIC}}` (we display the printed text and DROP
the correction).  `_content.py` groups `sic` with `lang`/`dropinitial` as
"metadata genuinely droppable" — but `{{SIC}}` expands to `{{tooltip|as-printed|
[sic] 'correction'}}`, so its second argument is the editorial correction, not
metadata.  It belongs with `tooltip`/`abbr`, which we already carry as
`«SPAN[title:…]»`.

**Order matters:** land the `sic` fix BEFORE any refetch.  In that order a
refetch is a straight gain (1,351 corrections preserved); in the other there is
a window where 1,240 preserved corrections become dropped ones.  A refetch is
now ~10 minutes, but it changes visible text in ~1,240 places and 3,600 pages
have unmeasured substantive edits, so it needs a tagged diff and sign-off, not a
shrug.  [[feedback_no_wholesale_rebaseline]]

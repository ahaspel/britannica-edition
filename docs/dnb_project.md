# The DNB — a sister project on the same code

**Status: PROBED, not started.**  Nothing in `src/` has been changed for it.
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

1. **Scope** — the 63 main volumes only, or also the 1901/1912 supplements?  They
   are separately named on Wikisource, they are where the `#ifeq` contributor
   conditionals point, and they hold the corpus's only image.  Recommend 63 first.
2. **Domain.**
3. **Scans** — the DjVu page images exist at the Internet Archive.  EB1911 ships a
   scan viewer; the DNB could skip it.
4. **Citability** — its own Zenodo deposit, or not.

## Probe artifacts

The scratch database `dnb_probe` (Postgres, separate from `britannica`) holds
the 81 loaded pages and 88 detected articles.  Every probe script asserts on
`engine.url` before touching anything.  The probe scripts themselves live in the
session scratchpad and are not part of the repository.

# Britannica Edition — Status

**Last updated:** 2026-05-17.  Single source of truth for project state.  Snapshot
audit reports live in `docs/reports/`; long-form per-topic notes live in the
agent's memory directory and are not duplicated here.

---

## Current focus (2026-05-17) — Phase A recovery shipped

The 2026-05-16 V2 deploy shipped marker-contaminated titles (`«B»X«/B»` in
the `title` field) plus a separately-broken xref resolver and contributor
linker — both downstream consequences of the same root cause.  Today's
Phase A recovery reverts the title contract and ships clean.

**Root cause:** an in-session edit to `_clean_extracted_title` kept the
`«B»/«I»/«SC»` formatting markers in the returned title so the viewer's
H1 could render typography.  Eight surfaces read `title` as plain text
(volume index, search, xref resolver, contributor linker, Meilisearch,
Reader's Guide, topics page, URL-slug builder); only the H1 was patched.
Every other surface either rendered raw `«B»` characters or failed
string-equality matching.  Net result: ~98% of titles displayed garbage
in the volume index, ~89% of cross-references unresolved (28,613 lost),
~70 contributors orphaned.

**Phase A fixes shipped today:**
- `detect_boundaries.py::_clean_extracted_title` — strips `«B»/«I»/«SC»`
  markers, returns plain title.  Single chokepoint.
- `detect_boundaries.py` multi-line bold extension — when first content
  line ends with `«/B»` and the next starts with `«B»`, the extractor
  joins them.  Fixes ROBESPIERRE, MAXIMILIEN FRANÇOIS MARIE ISIDORE DE
  (title's bold span spans two physical lines in source).
- `clean_pages.py::_convert_quote_runs` — applies quote-run conversion
  inside `<ref>...</ref>` blocks before masking, so italics in citations
  (`''Ency. Bib.''`) get marked correctly.  `stray_wiki_italic` 2,159 → 15.
- `tools/rebuild_all.sh` — quality report moved to Phase 6f (pre-deploy)
  for visibility.  Gate-style blocking deferred to a follow-up.
- 6 corrupted quality-report baselines deleted from
  `data/derived/quality_reports/` (post-stacked-DB-rebuild artifacts).
- `data/contributor_aliases.json` — three pairs added so `_clean_name`
  collapses them on next rebuild: Lawrence F. Abbott / Laurence Abbott
  (the one visible-on-page dup), H. Hamilton Fyfe / Hamilton Fyfe,
  Ralph Stockman Tarr / Ralph Stockman.  Only Abbott is currently
  visible (the others have one empty side).

**Tests recovered:** the 2026-05-16 boundary rewrite broke 24 unit tests
(fixtures fed raw `'''X'''` to `detect_boundaries`, which now consumes
cleaned `«B»X«/B»`).  Plus 9 regression/integration tests in the same
fixture-shape family.  All 33 updated to call the real
`_convert_quote_runs` before passing to the boundary parser.  Test
suite is back to being a real signal: 286 passing, 8 remaining red —
each one a documented production bug (image-legend extraction +
chemistry layout), not a stale fixture.

---

## Last full rebuild

**2026-05-17 — Phase A recovery deployed to britannica11.org.**
- 36,671 articles (+8 vs 2026-05-14 baseline)
- 31,815 xrefs resolved (vs 31,954 baseline — close to parity)
- 5,219 xrefs unresolved (vs 5,131 baseline)
- 0 titles contain `«B»/«I»/«SC»` in the JSON `title` field
- stray_wiki_italic: 15 (was 2,159 yesterday, 2 on 2026-05-14)
- stray_close_braces: 9 (unchanged from baseline)
- 1,501 contributors created, ~48 unlinked after Phase 3b → ~7 after Phase 3b2

---

## Queued (next session)

- **Phase B**: restore H1 typography via a `title_html` field rendered at
  export time in Python, emitted alongside plain `title` in the article
  JSON.  Single chokepoint (Python), every JS surface drops `title_html`
  into innerHTML.  No marker contamination, no per-surface helpers.
- **Wire `dedup_contributors.py --apply` into `rebuild_all.sh`** as a phase
  (probably 3b3) so duplicate-contributor regressions can't ship silently.
- **Pre-deploy quality gate** with hard thresholds + a title-shape check
  (`«` in any title → abort) + a (vol, page)-level pair diff against
  baseline.  Currently the quality report runs pre-deploy but doesn't
  block; harden it into a gate.
- **Architectural cleanup**:
  - Split `clean_pages` into `clean_for_articles` (the `page.wikitext`
    path consumed by the main pipeline) and `clean_for_front_matter`
    (the `page.cleaned_text` path consumed by `export_front_matter.py`).
    One function doing two unrelated jobs.
  - Decompose `detect_boundaries.py` (~900 lines): letter-article handler,
    bold extractor, glue check, fallback path → each its own module
    with focused tests.
- **Inline images rendered as block** — corpus-wide bug.  Source has
  `[[File:foo.svg|14px]]` mid-prose (letter articles use these for
  variant glyphs of A/B/C in Phoenician, Greek, Latin scripts; ARENIG
  GROUP and similar use them for taxonomic ornament).  Pipeline strips
  the size hint (`_image.py:34` skips `\d+px` parts) and wraps the
  resulting `{{IMG:fn}}` with `\n\n`, turning inline images into
  standalone block-level images at default size.  Fix is multi-file:
  preserve size in `_process_image` (and the ~10 other IMG-emit sites
  in `_layout.py`/`_tables.py`/etc.); extend marker schema to
  `{{IMG[size=14px]:fn|caption}}` mirroring `«MATH[fs=N]:`; stop the
  `\n\n` framing for inline images; teach the viewer to render the
  size-hinted form inline.

- **Letter-article simplification — LANDED 2026-05-17**.  Replaced
  ~70 lines of brace-walker + body-keyword check with ~25 lines of
  regex + brace-aware helper.  Validated 26/26 on corpus (one per
  letter A–Z), zero false positives.  See
  `tools/_scratch/verify_letter_articles_simplified.py`.

---

## Known issues (open)

- **Bare-label legend bundling** — SPINAL CORD (vol 25 Fig 3) / MALLOW (vol 17
  5-part botanical legend).  Single-bare-label paragraphs render as body prose;
  needs a figure-pass that collects consecutive single-entry paragraphs.
  Styling, not content loss.
- **Two-column legend variants — RESOLVED for canonical cases 2026-05-15.**
  The MULTICOL_LEGEND layout subclass now handles multi-row continuation
  entries via column-major reconstruction (ARACHNIDA Figs 7, 12, 14, 47,
  54, 65 all clean).  Trailing single-cell colspan annotations break the
  legend at the right boundary; pre-existing LEGEND blocks are preserved
  through the figure walker so trailing credits still fold into the IMG
  caption.  Remaining sub-patterns within the same systemic class:
    * **`rowspan=N` continuation cells** (ARACHNIDA Fig 31) — col-1 cell
      spans 2 rows of col-0; the rowspan row has only one source cell so
      legend parsing terminates early.  Need rowspan-aware row expansion
      before column-major build.
    * **Prime-marked labels** (`7′`, `I′ to V′` — ARACHNIDA Fig 47) —
      `_MULTICOL_FULL_ENTRY_RE` doesn't accept prime characters in the
      label, so labelled-with-prime cells get folded into the prior entry.
      Extend label regex to include `′″‴` etc.
    * **Hanging-indent entries in wide-column cells** (ARACHNIDA Fig 26)
      — legend laid out as one `{{Hi|1em|…}}`-wrapped entry per template,
      multiple per cell, no `||` separator.  Different shape from the
      standard 2-col legend; needs its own detector that walks `{{Hi}}`
      templates as legend entries.
    * **Side-by-side image cells losing caption + legend** (ARACHNIDA Figs
      57–58) — two figures laid out in a 2-column wikitable, each cell
      containing `[[File:…]]` + caption + `<br>`-stacked legend; pipeline
      lifts the IMG markers but drops the cell text.  Distinct extraction-
      time issue.
- **Fig 7 editorial note in trailing PRE** — a wikitable that follows the
  figure containing an editorial annotation `[According to the system…]`
  classifies as PRE; the figure walker doesn't recurse into PRE for an
  enclosed credit line.  Both an extraction-time classification miss
  (the trailing wikitable's actual structure is annotation + credit)
  and a walker miss.
- **BRITISH EMPIRE India-acquisitions table** — multi-line cell continuation
  + `|+` caption attribute leak; separate single-article residual.
- **`{{c|…}}` Roman-numeral subsections** (24 articles) — flatten to inline
  prose; no clean single-block distinguisher, only Roman-numeral progression
  across blocks.
- **Tall-brace taxonomic grouping** — print-typographic device using a tall
  `\left\{ \begin{matrix} \\ \end{matrix} \right .` (no math content, pure
  ornament) to group preceding-or-following items as members of a single
  category.  Currently renders as a stray vertical brace splitting the
  surrounding prose.  Examples: ARACHNIDA (Eurypteromorpha sub-orders;
  scorpion families with Carboniferous bracket), ARENIG GROUP, ATMOSPHERIC
  ELECTRICITY — ~8 instances corpus-wide.  Real fix: detect the
  empty-matrix brace pattern, parse the grouped items, emit as an OUTLINE
  block.  The outline renderer is general-purpose and we underexploit it;
  this is one of several patterns that ought to route there.
- **IMG-caption credit-glue missing space** — when a figure's descriptive
  caption and its `(From …)` credit live in the same source cell separated
  only by structural markup that gets stripped (`{{center|{{Fs|N%|…}}}}`,
  `<br>`, etc.), the IMG caption emerges with `).(From X)` — no space at
  the join.  Sample: ARACHNIDA Figs 13, 63, 74.  Narrow extraction-time
  fix: normalise `.(` → `. (` when assembling the caption (in
  `clean_caption` or the caption-build path of the layout subclasses).
- **Italic-marker inversion (residual)** — pre-existing class.  Post-Phase-A
  `stray_wiki_italic` counter is at 15 (vs baseline 2 on 2026-05-14, and a
  catastrophic 2,159 on the broken 2026-05-16 V2 deploy).  Ref-internal
  italics fixed today; the remaining 15 are the unfixed pre-existing edge
  cases in the 5-quote bold-italic handler.
- **8 unit-test failures** = 8 documented production bugs:
  - 7× `test_image_layout_unwrap.py` — the legend-extraction sub-patterns
    listed above (rowspan, prime marks, hanging-indent `{{Hi}}`,
    side-by-side image cells, sponges/hydromedusae figures).
  - 1× `test_elements.py::test_fulminic_acid_competing_formulae` —
    chemistry-layout doesn't emit `«CHEM:` marker for the
    competing-formulae 2-D table shape.
- **Contributor duplicates (1 visible, 2 invisible)** — Abbott pair
  visible on contributors page; Fyfe + Stockman pairs have one orphan side
  filtered out of the contributors page.  All three queued for merge via
  `data/contributor_aliases.json` on next rebuild.
- **Lower priority:** ~7 unlinked contributors after Phase 3b2 (down from
  ~88 in yesterday's broken deploy); ~3,633 unproofread Wikisource pages;
  Meilisearch port 7700 open to all (should be CloudFront-only).

See `docs/reports/` for historical audit snapshots.

---

## Overview

A scholarly digital edition of the 1911 *Encyclopædia Britannica* — the first
hyperlinked, searchable, fully annotated edition with proper rendering of Greek,
Hebrew, hieroglyphics, mathematical notation, chemical formulas, footnotes,
images, verse quotations, and contributor attribution.  Live at
**britannica11.org**.

---

## Architecture

### Boundary detection

Article boundaries are determined by `<section>` tags in the Wikisource
wikitext — not heuristic heading detection.  Plate pages are split off first
in a stateless PASS 1 (`_split_out_plates`), then the article state machine
runs over the plate-free pages in PASS 2.

### Element pipeline

Extract-process-reassemble per segment (`pipeline/stages/elements/` +
`transform_articles/_transform_text_v2`):

1. Wiki tables (balanced matching) → HTML elements (ref, html_table, poem,
   math, score) → wiki markup (image_float, image).
2. Each element processed recursively.
3. Body text transforms (~11 explicit functions: hieroglyphs, links, content
   templates, small caps, shoulder headings, layout templates, sub/sup,
   bold/italic, strip templates, strip HTML, decode entities).
4. Reassembly with `\x01PAGE:N\x01` markers.

### Marker formats (internal)

| Marker | Meaning |
|---|---|
| `«B» / «I» / «SC»` | Bold / italic / small caps |
| `«LN:filename\|target\|display«/LN»` | Resolved link |
| `«LN:target\|display«/LN»` | Unresolved link (falls back to search) |
| `«MATH:…«/MATH»` | LaTeX, plain |
| `«MATH[fs=N]:…«/MATH»` | LaTeX, render at N% font-size |
| `«MATH[popout]:…«/MATH»` | LaTeX, render click-to-pop-out link |
| `«FN:…«/FN»` | Footnote |
| `«HTMLTABLE:…«/HTMLTABLE»` | Complex table preserved as HTML |
| `«CHEM:…«/CHEM»` | Chemistry valence-bracket grid |
| `«PRE:…«/PRE»` | Preformatted block |
| `«SH»…«/SH»` | Shoulder heading |
| `{{TABLE:…}TABLE}` | Wiki-table block |
| `{{VERSE:…}VERSE}` | Verse block |
| `{{LEGEND:…}LEGEND}` | Figure-legend block |
| `{{IMG:filename\|caption}}` | Image with caption |

### Cross-reference resolution

Multi-strategy resolver: exact title, alias table, plural/singular, name
inversion, trailing article/period, qualified prefix.  Resolved targets are
rewritten as direct links at export time so the viewer routes to
`/article/{page}/{slug}` instead of search.

### Stack

Python 3.12, SQLAlchemy, Typer, Postgres, Meilisearch, KaTeX, Playwright (for
math measurement).  pytest (265 tests).

---

## Pipeline phases (`tools/rebuild_all.sh`)

1. Truncate DB, clear exports.
1b. Build contributor table.
1c. Apply vol 29 contributor linker.
2. Per-volume: import → clean → detect boundaries → transform → classify →
   extract xrefs → resolve xrefs (intra-vol) → extract images → extract
   contributors → export.
3a. Resolve xrefs across all volumes.
3b. Link contributors from front matter.
3b2. Link vol 29 article attributions.
3c. Rebuild printed-page mapping.
4. Re-export (with cross-vol xrefs resolved).
**4b. Measure math widths (refresh scale-hint cache).**
**4c. Annotate math markers from refreshed cache.**
5. Export front matter.
6b. Parse classified TOC; 6b2. apply cached disambiguations; 6c. detect fm
   first-content pages; 6d. rebuild generated site pages; 6e. build Reader's
   Guide.
7. Deploy (S3 sync articles + images + scans + JSON + viewer; CloudFront
   invalidate; index search on EC2).
8. Quality report.
9. Deploy preflight (check_deploy_refs.py).

---

## Scripts

- `tools/rebuild_all.sh` — full corpus rebuild + deploy (`--no-deploy` for
  local-only).  ~2 hours.
- `tools/pipeline/rebuild_article.py <vol> <TITLE>` — single-article rebuild
  for fast iteration.
- `tools/render_article.py <TITLE>` — re-render one article from existing DB
  state (~3 s).  Fastest iteration loop.
- `tools/diagnostics/quality_report.py` — body-wide metrics (run before every
  deploy).
- `tools/diagnostics/measure_math_widths.py` — refresh math-width cache.
- `tools/pipeline/annotate_math_markers.py` — re-annotate exported MATH
  markers from refreshed cache.
- `tools/deploy_html.sh` — upload viewer HTML + invalidate CloudFront.
- `tools/pipeline/start_services.sh` — start/stop local Postgres, Meilisearch,
  web server.

---

## Data model

`Article` (title, volume, page range, body, article_type, section_name) ·
`ArticleSegment` (text ↔ source page) · `CrossReference` · `ArticleImage` ·
`Contributor` · `ArticleContributor`.  Stable IDs: `{vol:02d}-{page:04d}-{slug}`.

---

## Viewer

- `home.html` — title-page landing.
- `index.html` — volume tabs, title / full-text / contributor search,
  alphabetic navigation.
- `viewer.html` — articles with volume:page citations, shoulder headings,
  images, footnotes, tables (inline + complex), TOC, in-article search,
  KaTeX math (with fs= scaling + popout modal for wide expressions),
  bold/italic/small-caps/hieroglyph rendering, direct cross-reference
  links.
- `search.html` — Meilisearch full-text, exact-substring filter, dedup,
  match-count sort, per-occurrence links to `viewer.html?…&match=N`.
- `contributors.html`, `preface.html`, `topics.html`, `ancillary*.html`,
  `readers-guide*.html`.

---

## Production

- **britannica11.org** — single S3 bucket + CloudFront (dist
  `E24BJKH0IB4I6`).  CloudFront function `article-rewrite` maps
  `/article/{page}/{slug}` → `viewer.html`; `strip-search-prefix` proxies
  `/search-api/*` to Meilisearch on EC2.
- **Meilisearch** — Docker on EC2 `t3.small`
  (`ec2-44-222-119-72.compute-1.amazonaws.com`), port 7700.
- **Raw wikitext** backed up to `s3://britannica11.org/raw/` (28 zips, 139 MB).
- **IA page scans** — 29 volumes (~30 GB), `data/raw/ia_scans/`.

---

## Topics page (Vol 29 classified TOC)

Category-bounded OCR (`tools/ocr_vol29_classified.py`) +  two-phase walker
(`tools/parse_classified_toc.py`).  23,050 articles across 24 categories.
Per-cat refinement: edit `data/derived/cat_ocr/<slug>.txt` or rerun
`ocr_vol29_classified.py --only='<Cat>'`.  Ambiguity disambiguation via
Haiku batch (`tools/vol29/disambiguate_toc.py`), cached.

---

## File / directory conventions

- `tools/_scratch/` — disposable.  Promote keepers to `tools/diagnostics/`
  with a real name and docstring.
- `data/corrections.json` — source-text typos by `vol:page`; never edit raw
  wikisource page JSONs directly.
- `docs/reports/` — dated snapshot audit reports.
- `docs/status.md` — this file.  Source of truth for current state.

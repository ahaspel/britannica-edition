# Britannica Edition — Status

**Last updated:** 2026-05-16.  Single source of truth for project state.  Snapshot
audit reports live in `docs/reports/`; long-form per-topic notes live in the
agent's memory directory and are not duplicated here.

---

## Current focus (2026-05-16)

**Article detection overhaul** — replaced the uppercase-run title-extraction
regex with a bold-delimited rule that captures the full multi-bold title from
the first `«B»` to the last `«/B»` belonging to it.  Surface improvements
corpus-wide: full names where baseline truncated to surname only (AARSSENS, or
Aarssen, FRANCIS VAN), accented characters preserved (BARÈRE, GRÉTRY),
typography preserved (`«SC»`/`«I»`/`«B»` markers kept in title for viewer
rendering).  Pattern-1 cleanup: NITRIC ACID-class titles shorten to just the
bold-delimited heading; the parenthetical etymology falls into the body
naturally.

**24 letter articles recovered** (A through Z; baseline had only 15 of them).
Source uses six different drop-cap template shapes (`{{dropinitial|X}}`,
`{{di|X}}`, `{{Serif|{{di|X|5em}}}}`, `{{di|{{serif|J}}|4em}}`,
`{{dropinitial|'''{{serif|K}}'''|6em}}`, bold-wrapped `«B»{{di|T}}«/B»`); the
new `_detect_letter_article` special handler identifies them by drop-cap
template at section start plus letter-article body keywords ("letter",
"alphabet", "phoenician", etc.).

**Multi-page article splits fixed** — AIR-ENGINE (481-483), AIRY (483-485),
ALECSANDRI (578-579), ALSTRÖMER (801-802) were each being split into two
articles by a fallback that fired on continuation pages whose `<section
begin="X">` name matched the article but had no bold heading.  Removed the
fallback; bold heading is now a strict requirement for a new article (except
for letter articles via the special handler).

**Body-rendering fixes (deploy regressions from 2026-05-16 V2):**
- Line-scoped quote-run conversion prevents one-line typos (`''The
  Fishmongers'''` on vol 28 p403) from cascading through the rest of the page
  and eating downstream articles.  Recovered WATER-SCORPION, WATERSHED,
  WATERSPOUT, WHEAT, plus ~35 other articles V2 dropped.
- Fixed-point template-unwrap loop in `body_text.py` resolves nested
  `{{nowrap|N{{tfrac|M}}}}` patterns without losing the content or leaving
  stray `}}` (~166 stray-close-brace regressions cleared).
- `<ref>` masking before line-split — multi-line footnotes inside bold
  headings (ODO OF BAYEUX) no longer break quote-run conversion.
- HTML comment peeling in section first-line detection (MARRYAT vol 17 p776).
- `{{bold|…}}` template handling (SPARKS, JARED vol 25 p629 and 6 others).
- Bracket-balance: titles like `«B»MARS, MLLE«/B» [«B»ANNE … BOUTET«/B»]`
  now include the closing `]` (ALBERT, AMYNTAS II have same pattern).
- detect-boundaries body-slice uses a non-destructive `first_line` rather
  than the template-stripped `clean_first`, preserving nested templates in
  body content.

**Corrections.json entries:**
- `28:403` — Fishmongers' Company genitive apostrophe (line-scoping makes
  this safe but the fix renders the line cleanly).
- `28:269` — Waldeck-Rousseau surname misspelled `WALDECK-ROUSSSAU` (3 S's)
  in the bold heading.

**Article-list verification:** row-by-row diff against
`article_index_baseline_full.tsv` shows 27 truly-new articles in current
(real wins) and 13 unmatched-baseline entries that are all matcher artifacts
(accent / curly-apostrophe differences, name-order, etc.) — zero real losses.
Net article delta vs baseline: +14 across 28 vols.

Next: full rebuild + deploy in progress (`tools/rebuild_all.sh`).

---

## Queued for next rebuild

### Math infrastructure (this session)
- `src/britannica/math_widths.py` (new) — `scale_hint` lookup, fs=80 floor.
- `tools/diagnostics/measure_math_widths.py` (new) — KaTeX width measurement.
  Cache: `data/derived/math_widths.json`.
- `tools/pipeline/annotate_math_markers.py` (new) — post-export re-annotation.
- `_process_math` (`elements/_leaf.py`) and `_math_layout.py` — whitespace
  canonicalisation + `scale_hint` bake.
- `tools/viewer/viewer.html` — `«MATH[hint]:` parser, fs=N scaling, popout
  link + natural-size scrollable modal.
- `tools/rebuild_all.sh` — new Phase 4b (measure) + Phase 4c (annotate).

### Quality / regression fixes (this session)
- `transform_articles/__init__.py` — JESUS CHRIST layout-strip refined with
  `\n(?!\s*\|)` lookahead (preserves real data tables in BEAUFORT, PROBABILITY,
  ROME, ROOT, TROCHAIC, TURKEY, ZEUXIS); `{{word-spacing|N|…}}` strip before
  `unfold_folded_rows` (FISHERIES).
- `transform_articles/body_text.py` — `{{Fs|N|…}}` template strip (HYDROMECHANICS).
- `elements/_tables.py` + `elements/__init__.py` — inline nested `{{TABLE:}TABLE}`
  inside HTMLTABLE blocks (ORNITHOLOGY-style).
- `data/corrections.json` — WEIGHTS AND MEASURES `{{ditto|{India:` entry.
- `tools/diagnostics/quality_report.py` — improved marker stripping, added
  HTMLTABLE/CHEM/PRE to known markers.

### Prior session work also queued
- Chemistry rendering: `_process_chemistry_layout` self-contained parser
  (FULMINIC ACID, ALDEHYDES, SUGAR verified).
- ROBES PLATE captions: `parsers/plate/captions.py::is_image_adjacent` allows
  `<br>` between image and caption.
- JESUS CHRIST page-layout wrapper strip (`_strip_page_layout_noinclude_wrappers`).
- Viewer LN dedup removed — every `{{EB1911 article link|…}}` linkifies.

---

## Last full rebuild

**2026-05-14 — deployed to britannica11.org.**  Snapshot: 36,663 articles + 398
plate inserts = 37,061 entries; 31,953 (86%) cross-references resolved.

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
- **Italic-marker inversion** — paragraphs render with close-italic *before*
  open-italic on substrings that should be italic, implying italic state
  has been flipped "on" by an unclosed `''` somewhere earlier.  A single
  upstream defect cascades through every subsequent balanced italic pair
  in the same section — many visible instances, one underlying cause per
  cascade.  Visible at multiple points in ARACHNIDA (Sub-order/Families
  lists, Architarbus, Tyroglyphidae→Eriophyidae block).  Class is
  `stray_wiki_italic`; the 5-quote bold-italic handler in
  `_convert_bold_italic` likely misses some edge case.  Post-rebuild
  quality report will quantify; pre-existing class, not a new regression.
- **13 missing image files on disk** (`tools/diagnostics/find_missing_images.py`)
  — ALPHABET plate, CASTLE Fig 9, RIGGING, several `.djvu/NNN` refs.
- **Small residual quality counters** (2026-05-12 baseline, may shift):
  `unhandled_marker_in_htmltable` ≈ 16 (driven to 0 by this session's HTMLTABLE
  marker work; verify post-rebuild); `stray_close_braces` 9 / `stray_braces` 7
  (math-vs-template collisions); `html_tag` 1 (POST vol 22).
- **Lower priority:** ~93 unlinked contributors; ~3,633 unproofread Wikisource
  pages; Meilisearch port 7700 open to all (should be CloudFront-only).

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

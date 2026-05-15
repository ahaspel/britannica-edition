# Britannica Edition — Status

**Last updated:** 2026-05-15.  Single source of truth for project state.  Snapshot
audit reports live in `docs/reports/`; long-form per-topic notes live in the
agent's memory directory and are not duplicated here.

---

## Current focus (2026-05-15)

Wide-math rendering is finally solved.  An offline measurement pass renders every
unique display-mode `«MATH:` marker through KaTeX in a headless browser, records
the smallest font-size that fits the body column, and writes a hash-keyed cache.
At pipeline time the marker is rewritten as `«MATH[fs=N]:…«/MATH»` (scaled
in-column) or `«MATH[popout]:…«/MATH»` (unscalable — viewer renders a click-to-
pop-out link that opens a modal with natural-size math and a horizontal scroll).
A readability floor of fs=80 routes anything that would scale smaller to popout.
Verified on ALGEBRAIC FORMS: 1383 plain + 50 fs-hinted + 10 popout.

Next: ship the queued rebuild (below).

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
- **ARACHNIDA** — deferred to a dedicated session (Fig 7 continuation, Fig 26
  caption, Fig 32 legends, BRITISH EMPIRE India-acquisitions table).
- **`{{c|…}}` Roman-numeral subsections** (24 articles) — flatten to inline
  prose; no clean single-block distinguisher, only Roman-numeral progression
  across blocks.
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

# Britannica Edition – Project Status

## Current focus (2026-04-14): Vol 29 Classified TOC refinement

The Topics page (`/topics.html`) was overhauled to use a **category-bounded OCR architecture**. Per-page OCR was abandoned because multi-category pages (e.g. ws 902 holds both Education and Engineering, ws 945 holds Literature + Math + Medical) interleave content unrecoverably when read column-by-column. The new approach:

1. `tools/ocr_vol29_classified.py` — finds every Blackletter cat-header across all body pages (wikitext `{{bl|X}}` markers + low-res OCR + meta-TOC fallback), bounds each category by (start_page, y) → (next_cat_start_page, y), crops each bounded region, 3x-upscales + sharpens + PSM 6 OCRs each crop. Output: one text file per cat in `data/derived/cat_ocr/<slug>.txt` and aggregated `vol29_ocr_by_cat.json`. Per-cat caching — re-run one cat with `--only='Mathematics'`, force all with `--force`.
2. `tools/parse_classified_toc.py` — two-phase walker: Phase A processes wikitext ws-by-ws (cat transitions via `{{bl|X}}`), Phase B processes each cat's per-cat OCR text with `cur_cat` fixed. No cross-cat contamination in Phase B. Match passes: start-anchored → long-title substring → rapidfuzz partial-ratio fuzzy (cutoff 92, limit 2). Output: one file per cat in `data/derived/cat_toc/<slug>.json` and aggregated `classified_toc.json`.

Current attribution: 23,050 articles across 24 categories, 60 empty leaves. Mathematics 198 (target 250), Astronomy 210, Engineering 458, Law 1034, Geography 6150, History 3939. Further gains gated on OCR quality — refinement will happen per-cat.

## Overview

A scholarly digital edition of the 1911 Encyclopedia Britannica — the first hyperlinked, searchable, fully annotated edition with proper rendering of Greek, Hebrew, hieroglyphics, mathematical notation, chemical formulas, footnotes, images, verse quotations, and contributor attribution.

Live at **britannica11.org**.

## Architecture

### Boundary Detection

Article boundaries are determined by `<section>` tags in the Wikisource wikitext — NOT by heuristic heading detection. Every article boundary is explicitly marked. Pages without section markers are pure continuation of the previous article. This cleanly separates structural parsing from text formatting.

Special cases handled:
- **Numbered continuations** (Egypt2, Egypt3, part1) — merged with parent article
- **Single-letter articles** (A, B, C...) — detected only when the content is about the letter itself
- **Link-wrapped headings** — bold headings inside `«LN:...|«B»TITLE«/B»«/LN»` wrappers
- **Mixed-case bold headings** (e.g. `«B»Transvaal,«/B»`) — falls back to section ID for title

### Formatting

All formatting is preserved independently of boundary detection:
- **Bold** — `«B»text«/B»`
- **Italic** — `«I»text«/I»`
- **Small caps** — `«SC»text«/SC»`
- **Subscripts** — Unicode (H₂O, CO₂)
- **Superscripts** — Unicode (x², m³)
- **Fractions** — Unicode (½, ¾, ⅜) or text (1⁄225)
- **Greek** — direct Unicode from `{{Greek|...}}` and `{{polytonic|...}}`
- **Hebrew** — direct Unicode from `{{Hebrew|...}}`
- **LaTeX math** — `«MATH:...«/MATH»` rendered via KaTeX
- **Verse** — `{{VERSE:...}VERSE}` rendered as blockquote
- **Footnotes** — `«FN:...«/FN»` with superscript numbers and Notes section
- **Cross-reference links** — `«LN:filename|target|display«/LN»` (resolved, direct link) or `«LN:target|display«/LN»` (unresolved, search fallback); first-mention only
- **Hieroglyphics** — `[hieroglyph: code]` rendered as Unicode Egyptian Hieroglyphs via Gardiner Sign List mapping, with Manuel de Codage shorthand support

### Cross-Reference Resolution

Multi-strategy resolver:
- Exact title match
- Alias table (canonical + alternative titles)
- Plural/singular normalization
- Name inversion (FIRST LAST ↔ LAST, FIRST)
- Trailing article (UNITED STATES → UNITED STATES, THE)
- Trailing period (EDWARD VII. → EDWARD VII)
- Qualified prefix match (CLIMATE → CLIMATE AND CLIMATOLOGY)

Resolved xrefs are embedded as direct links at export time: the export stage rewrites inline `«LN:target|display«/LN»` markers to `«LN:filename|target|display«/LN»` for resolved targets, so the viewer links directly to `/article/{page}/{slug}` instead of falling back to search. Unresolved xrefs keep the 2-part format and fall back to search.

### Stack

- Python (3.12), SQLAlchemy, Typer, Postgres, Meilisearch, KaTeX
- pytest (119 tests passing)

## Pipeline Stages

1. **Fetch** — Wikisource pages (3s delay, 350-page batches, 15-min cooldown); self-closing refs stripped before content refs; interwiki links (wikt:, w:, Portal:, etc.) reduced to display text
2. **Import** — raw wikitext into SourcePage (wikitext field)
3. **Detect boundaries** — section-marker based on raw wikitext; skips leading tables/images/comments when detecting bold headings; prefers section ID when heading regex truncates title
4. **Transform** — per-segment extract-process-reassemble (`elements.py` + `_transform_text_v2`): extracts embedded elements (tables, images, footnotes, poems, math, scores), transforms body text (11 explicit functions), processes each element recursively, reassembles. Plates have dedicated processor. Joined into article body with `\x01PAGE:N\x01` markers; per-article commits
5. **Classify** — article, front_matter, plate (with grid parser for multi-section plates)
6. **Extract xrefs** — q.v., See, See also, inline link markers, `{{EB1911 article link}}`; targets >200 chars rejected; internal markers stripped from See/See also targets
7. **Resolve xrefs** — unified lookup (canonical + aliases + fuzzy)
8. **Extract images** — from raw wikitext, Wikimedia Commons URLs; page→article mapping from article page ranges
9. **Extract contributors** — footer initials + front matter biographical tables; page→article mapping from article page ranges
10. **Export** — article JSON (page markers embedded in body), index.json, contributors.json (with bio_article_filename), front_matter.json; inline link markers resolved to direct article URLs
11. **Post-process** — safety-net cleanup on exported JSON (leaked attrs, pipe tables, width directives)
12. **Index search** — Meilisearch full-text

## Scripts

- `tools/rebuild_all.sh` — Full rebuild of all 28 volumes (9 phases: reconvert raw wikitext, wipe, pipeline, xref resolve, re-export, front matter, post-process, reindex, quality report)
- `tools/rebuild_article.py` — Piecemeal rebuild: re-converts raw wikitext for an article's pages, then re-runs the full volume pipeline. Usage: `python tools/rebuild_article.py <vol> <TITLE> [--deploy]`
- `tools/start_services.sh` — Start/stop local Postgres, Meilisearch, and web server
- `tools/run_volume.sh <vol> [--skip-fetch]` — Single volume pipeline
- `tools/postprocess.py` — Post-export cleanup for residual markup issues
- `tools/quality_report.py` — Quality analytics with before/after comparison

## Data Model

- **Article** — title, volume, page range, body, article_type
- **ArticleSegment** — provenance (text ↔ source page, with page_number)
- **CrossReference** — see, see_also, qv, link types
- **ArticleImage** — filename, caption, Commons URL
- **Contributor** — initials, full_name, credentials, description
- **ArticleContributor** — maps contributors to articles

## Viewer

- **home.html** — landing page with photograph-style title page and navigation links
- **index.html** — volume tabs (data-driven labels), title/full-text/contributor search, alphabetic page navigation per volume
- **viewer.html** — articles with volume:page citations in left margin, shoulder headings in right margin, inline images, footnotes, tables (including inline single-row tables), two-level TOC (unnumbered "Contents" for major `«SC»` divisions, numbered "Sections" for shoulder headings), in-article search with match navigation, KaTeX math rendering (display mode detection, `\mbox`→`\text`, entity decoding, Unicode whitespace normalization), bold/italic/small-caps/hieroglyph rendering, direct cross-reference links to target articles, contributor initials shown in original citation format
- **search.html** — Meilisearch full-text with highlighted snippets, formatting marker cleanup
- **contributors.html** — sorted by surname, credentials, descriptions, full article lists
- **preface.html** — Hugh Chisholm's 1910 editorial preface with drop caps and shoulder headings

## Current State (2026-04-08)

- **Site live at britannica11.org**
- **28 volumes processed** (vol 29 is end matter, excluded)
- **36,701 articles** in database
- **25,211 cross-references resolved (89%)**
- **3,133 unresolved xrefs** (mostly portal links and literary work references)
- **1,505 unique contributors** from front matter (1,412 linked to articles, 1,030 with credentials, 167 with bio article links)
- **Contributor system**: master table from front matter, `contributor_initials` alias table, footer matching + front matter subject fallback
- **Architecture: extract-process-reassemble** — `elements.py` + `_transform_text_v2`
- **Raw wikitext backed up** to `s3://britannica11.org/raw/` (28 zips, 139 MB)
- **All data fetched** — raw wikitext is static, never changes
- **IA page scans** — all 29 volumes downloaded as JP2 zips (30 GB in `data/raw/ia_scans/`); vol 20 is Edinburgh copy (580 MB, low quality — `univ` copy locked behind IA lending); page_numbers.json + scan_map.json for all volumes
- **Scan viewer** — `scans.html` page-by-page viewer with `«` `‹` `›` `»` navigation; front matter scans extracted for all volumes (except vol 20); `extract_scan.py` for on-demand page extraction using leaf offset mapping
- **Commons images** — download in progress; DjVu crops (208) and chart images (5) complete

## Production Deployment

### Domain
- **britannica11.org** — registered at GoDaddy, DNS via Route 53

### Architecture
- **`britannica11.org`** — single S3 bucket + CloudFront
  - `/` → `home.html` (default root object)
  - `/article/{page}/{slug}` → `viewer.html` (rewritten by CloudFront function)
  - `/data/*.json` — article exports from S3
  - `/search-api/*` → Meilisearch on EC2 (proxied by CloudFront, prefix stripped by CloudFront function)
- **EC2 instance** (`t3.small`, `ec2-44-222-119-72.compute-1.amazonaws.com`) — Meilisearch only

### URL Scheme
- `/` — home page (title page scan + nav)
- `/article/{page}/{slug}` — article viewer (e.g. `/article/367/pharaoh`)
- Stable across rebuilds: derived from Wikisource page number + title

### CloudFront Functions
- `article-rewrite` — rewrites `/article/*` to `/viewer.html` (viewer request, default behavior)
- `strip-search-prefix` — strips `/search-api` prefix before forwarding to Meilisearch origin (viewer request, `/search-api/*` behavior)

### Meilisearch
- Docker container on EC2, port 7700
- Master key: `gibbon-winters-lewis`
- Search-only key: `24e84cf3ca3b70fe166637d797cbbdd0593ba3a27a47a9ed76b552c821199579`

### Deploy Process
Single command: `./tools/rebuild_all.sh` — cleans everything (DB, exports, S3), builds, deploys, indexes search, runs quality report. Use `--no-deploy` for local-only builds. Script auto-starts services if not running.

## Known Issues (remaining)

### File-Level (2026-04-07 build)
- stray_close_braces: 58 (mostly false positives from LaTeX braces in MATH blocks)
- pipe_leak: 30, html_tag: 28, stray_wiki_italic: 15 (increased from layout table unwrapping exposing previously hidden markup)
- stray_braces: 14, leaked_html_attr: 8, stray_control_x06: 4, stray_control_x03: 1

### Queued for next rebuild (staged 2026-04-17)

**Boundary detection (`detect_boundaries.py`)**
- Uppercase char class extended for Œ, Ś, Ḍ, Ḥ, Ṃ, Ṇ, Ṛ, Ṣ, Ṭ, Ẓ (fixes MANŒUVRES truncation to MAN).
- `_QUALIFIER` pattern keeps parenthetical/bracketed qualifiers in titles — "MAP (or Mapes), WALTER", "MORLEY [of Blackburn]".
- Regnal-numeral second words allowed (ALEXANDER I/II/III, GEORGE V, ABBAS I).
- `{{nop}}` / `{{clear}}` / `{{-}}` spacing templates stripped before bold-heading check.
- `<big>`, `<small>`, `<sub>`, `<sup>`, `<span>`, `<font>` stripped in `_strip_templates` (fixes SUCCINIC ACID drop-cap).
- `_is_plate_page` tightened to ≤80 prose words for ≥3 images, ≤30 for 2 (fixes MAP misclassification).

**Transform (`transform_articles.py`)**
- `{{EB1911 tfrac}}` → Unicode vulgar fractions.
- `,,` ditto marks preserved (ROPE table).
- `{{sic|word}}` preserves inner word (fixes BRITAIN Pre-Roman "Geologists").
- `_strip_templates` uses count-aware `_strip_excess_closers` for orphan `}}` (fixes BAG-PIPE score).

**Elements (`elements.py`)**
- `_strip_br` helper handles soft-hyphen `<br>` (`-<br>` → empty, `<br>` → space).
- `«LN:…|…«/LN»` marker strip in `_clean_text`.
- `||` → `\n|` normalization in `_extract_cells` (MediaWiki same-line cell fix).
- `{{Ts|…}}` / `{{ts|…}}` templates stripped before cell parsing (fixes Medieval Abbreviations phantom column).
- `_process_html_table` routes tables with colspan/rowspan to HTMLTABLE, preserving structure (fixes ROPE "Breaking Strain in Tons" double-row header).
- Image patterns extended: `{{img float}}`, `{{figure}}`, `{{FI}}`.

**Export (`article_json.py`)**
- `_find_parent` uses page-range containment for plate parent lookup (fixes title-collision cases like the three MAP articles).

**Contributors (`extract_contributors.py`)**
- Footer-to-article matching now operates on `ArticleSegment` scope, not page scope (fixes MALONIC ACID / J.L.W. misattribution from MALORY).

**Xrefs (`xrefs/extractor.py`)**
- `_is_bibliographic` filter excludes citations with italic journal names, quoted paper titles, "p./pp./vol.", roman-numeral volumes, "by Author" patterns.

**Diagnostics (`quality_report.py`)**
- New `unhandled_marker_in_htmltable` check — flags markers inside HTMLTABLE cells that `formatCell` can't render (MATH/VERSE exempt as known issues).

**Rebuild script (`rebuild_all.sh`)**
- Phase 6c: `tools/diagnostics/detect_fm_blank_pages.py` writes `fm_first_content.json` to skip blank front-matter scans.
- Phase 6d: `tools/viewer/build_about_page.py` + ancillary page generation.
- Paths updated for tools/ subdirectory reorg (pipeline/, vol29/, diagnostics/, viewer/).
- Additional deploy targets: ancillary.html, about.html, transcription pages.

**Viewer (already deployed, no rebuild needed)**
- HTMLTABLE renderer passes each cell through `formatCell` so IMG/FN/hieroglyph markers render (fixes ABBREVIATION images).
- Page markers inside HTMLTABLE cells hoisted to row level, prepended to first cell with existing `.page-marker` float/margin (keeps alignment intact).
- Nav standardized site-wide: Home · Articles · Contributors · Topics · Ancillary.
- Scans page reads `fm_first_content.json` to skip blanks; vol 20 shown with DLI Bengal leaf scans copied as fm01-18.
- Index page: Enter-to-search + result count; FM_LEAVES updated for vol 20.
- Topics page: hierarchical collapsibility, top/bottom nav arrows, subsection level 5 styling.

**Known deferred (not in this rebuild)**
- Wiki-table illustration unwrapping: `_process_table` in `elements.py` has an image+caption unwrapper only for 2-row tables with single-cell rows. Needs extension for 3+ row illustration tables where later rows carry multi-cell legends (e.g. CHAETOPODA vol 5 Fig. 2: row 1 = image, row 2 = "Fig. 2. (from Goodrich).", row 3 = figure description | solenocyte legend). Should emit `{{IMG:filename|caption}}` + the remaining rows as paragraphs/verse rather than a TABLE block.

**Completed during build (viewer-only, already live)**
- `formatCell` extended for MATH (KaTeX inline) and VERSE (newline → `<br>`). Fixed ABBREVIATION `\Bigg}` brace and CHAETOPODA verse legend rendering.
- `{{TABLE:}}` renderer protects `\n` inside `{{VERSE:…}VERSE}` blocks from row-splitting.
- Quality report: MATH/VERSE removed from HTMLTABLE exemptions (they're rendered now; future leaks will be flagged).

### New in 2026-04-09 build
- **Table classification overhaul**: `_is_layout_wrapper` respects border/rules/class; `{{Ts}}` + data signal → COMPLEX_HTML; verse-layout detection (~21 tables); `COMPOUND_TABLE` element type for nested sub-tables (40 tables); `_process_complex_table` uses inner with placeholders (fixes math in complex tables)
- **Commons images complete**: 9,986/9,987 downloaded; `download_images.py` filename sanitization + URL fix; `rebuild_all.sh` syncs images to S3
- **Removed stale `deploy.sh`** — `rebuild_all.sh` is the sole deploy path

### New in 2026-04-08 build
- **DjVu crop images**: `DJVU_CROP` element type in `elements.py` — 208 cropped regions from 108 DjVu pages, pre-cropped by `tools/download_djvu_crops.py`, served locally
- **Chart2 genealogical trees**: `CHART2` element type — 5 family trees rendered as page scan crops
- **Complex HTML tables**: tables with rowspan/colspan now render as proper HTML tables; classification reordered (layout wrapper → complex HTML → equation layout) to prevent false equation detection
- **New template handlers**: `{{...}}` → `...`, `{{ditto}}` → `″`, `{{blackletter}}` → Unicode Fraktur, `{{ne}}` numbered equations, `{{binom}}` → KaTeX, `{{dropinitial}}`, `{{nop}}`, `{{clear}}`, `{{hanging indent}}`, `{{missing table/image/math}}` → editorial notes
- **Image download scripts**: `tools/download_images.py` (Commons via Special:FilePath), `tools/download_djvu_crops.py` (DjVu crops) — rate-limited, skip existing
- **IA page scans**: `tools/fetch/fetch_ia_scans.sh` with correct per-volume identifiers for all 29 volumes
- **Pipe leak reduction**: 30 → 5 (from `{{ts}}` stripping fix and complex table improvements)

### Other
- ~93 contributors in front matter with no article links (no footer initials, no subject fields)
- Some pages have `pagequality level < 3` on Wikisource — 3,633 pages at level 1 (unproofread OCR)
- Portal links and literary work references are legitimately unresolvable xrefs
- Images on shared pages can be assigned to the wrong article — image extractor uses page-level ownership
- Meilisearch EC2 port 7700 currently open to all traffic — should be restricted to CloudFront IPs
- 41 titles with lowercase (Mc/Mac names — correct casing, flagged by quality report)
- ~~Section heading problem~~: resolved by `<section>` tag-based boundary detection

## Architecture

### Element Extraction Pipeline (`elements.py`)
- **Extract-process-reassemble**: one recursive function handles all element types
- **Key law**: once extracted, an element is never tampered with again
- **Extraction order**: wiki tables (balanced matching) → HTML elements (ref, html_table, poem, math, score) → wiki markup (image_float, image)
- **Element types**: TABLE, HTML_TABLE, IMAGE, IMAGE_FLOAT, DJVU_CROP, REF, REF_SELF, POEM, MATH, SCORE, HIEROGLYPH
- **Equation-layout tables**: detected (majority MATH placeholders or >50% empty spacer cells) and processed as own element type — cells joined per row, not pipe-separated
- **Layout wrapper tables**: detected (child TABLE or IMAGE with <200 chars/image non-image text) — unwrapped to sequential content (1,965 tables across encyclopedia)
- **Single-column text blocks**: tables with 1 cell per row rendered as `«PRE:»` preformatted blocks with body font and wrapping
- **Cross-element substitution**: multi-pass to handle table placeholders inside processed refs
- **Plate pages**: dedicated processor — image grid with keyword-matched captions
- **Brace tables**: detected and converted to verse + translation layout

### Body Text Transform (`_transform_body_text`)
11 explicit functions replacing 26 interleaved fetch stages:
1. `_convert_hieroglyphs` — `{{hieroglyph|code}}` → `[hieroglyph: code]`
2. `_convert_links` — `{{EB1911 article link}}`, `[[wikilinks]]` → `«LN:»` markers
3. `_unwrap_content_templates` — Greek, Hebrew, nowrap, lang, abbr, tooltip, sic
4. `_convert_small_caps` — `{{sc|}}`, `{{asc|}}` → `«SC»`
5. `_convert_shoulder_headings` — `{{EB1911 Shoulder Heading}}` → `«SH»`
6. `_unwrap_layout_templates` — center, c, csc, fine block
7. `_convert_sub_sup` — `<sub>`/`<sup>` → Unicode
8. `_convert_bold_italic` — `'''`/`''` → `«B»`/`«I»` (handles 5-quote bold-italic)
9. `_strip_templates` — remaining `{{...}}` and orphaned markup
10. `_strip_html` — remaining HTML tags
11. `_decode_entities` — `html.unescape()`

### Preprocessing (`_transform_text_v2`)
- Strip section tags, noinclude, HTML comments
- Balanced unwrap of deeply nested wrapper templates (fine block, center, etc.)
- Strip `{{nowrap}}` and `{{ts}}` before table extraction
- Wrap orphaned table rows (including single-pipe rows)
- Paragraph reflow after element reassembly

## Next Steps

### Short-term
- About This Edition page (user writing)
- Lock down Meilisearch security group to CloudFront IPs
- Investigate increased file-level issues from layout unwrapping (30 pipe leaks, 28 html tags — markup exposed from inside former table blocks)

### Medium-term
- Address section heading false-split problem (~850 false splits)
- Improve footer initials matching (48 unmatched patterns, 93 unlinked contributors)
- EPUB export
- Complete Commons image download (~5,000 remaining)
- Serve all images locally once download complete (flip `commonsUrl` in viewer)
- Citation export (BibTeX, Chicago style)

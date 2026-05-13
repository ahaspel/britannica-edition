# Britannica Edition – Project Status

## Current focus (2026-05-12): caption-boundary consolidation

After the big `transform_articles` refactor (extract-process-reassemble), the project has been in a post-refactor bug-burndown phase. State as of now:

- **`clean_body` burndown (mostly done):** `clean_body` cut from ~15 passes to 6; `word_count`/`sections` now computed from the *cleaned* body; the `clean_caption` consolidation (canonical caption-cleanup in `elements/_text.py`) is wired into the image + table-around-image paths; INFINITESIMAL CALCULUS's ~5000 missing words restored (a LaTeX `{|` inside `<math>` was being misread as a wiki-table opener — masked in `_extract_balanced_tables`); `bare_wiki_table` line-anchored; FN-as-caption preserved (unwrap to content); `verify_refactor.py --full` built as the shadow-verification harness ("fix a producer + delete the matching `clean_body` patch").
- **Chemistry-reaction layouts (skeleton landed):** `{|…|}` tables with `[[File:Langle*.svg]]` valence brackets are detected (`_is_chemistry_layout`) and emitted as `«CHEM:<table>…</table>«/CHEM»` markers (~33 articles). `quality_report.py` treats `«CHEM:` like `«HTMLTABLE:`. **Viewer rendering of `«CHEM:` as a CSS grid is still TODO** (Langle/Rangle → ⟨/⟩, `||`→bond-lines, `⟶`→arrows).
- **Plate detection restructured into two passes** (`detect_boundaries.py`, 2026-05-12): PASS 1 `_split_out_plates` lifts every plate page out *statelessly* — a `{{sc|Plate N.}}`/`{{uc|Plate N.}}` label *anywhere* on the page is the authoritative signal (`_heading_names_plate` or `_plate_label_from_content`); the `_is_plate_page` image-heavy heuristic is the fallback for the ~20 label-less inserts. PASS 2 = the unchanged article state machine over the plate-free pages, so it never reasons about plates. Net: **328 → 398 plate articles** (the new ones were previously absorbed into neighbouring articles as raw `||`-junk — ROUND TOWERS, TRIUMPHAL ARCH, VAULT, EGYPT×3, TAPESTRY×3, ROBES×3, ROOF, INDIA×2, WOOL, PALAEONTOLOGY p639 now render via `parse_plate`), plus ~89 plate-title fixes (`REGALIA`→`REGALIA, PLATE I` etc.), 36,663 articles unchanged. ~210 net lines of the old tangled plate-handling in `detect_boundaries.py` deleted.

**Next:** caption-boundary consolidation — `britannica/captions.py` with a canonical `clean_caption` + caption-shape regexes + credit predicate, shared by `parsers/plate/` and `legend_promote.py`; tighten `legend_promote`'s shape gates and the IMAGE-extractor's ext-caption regex so prose stops getting wrapped as LEGEND (fixes AFGHANISTAN's run-on caption, INFINITESIMAL CALCULUS §17/§36/§38). Then: chemistry viewer rendering; `clean_body` Phase C/D (move remaining real-leak handling to producers, delete `clean_body`).

## Topics page (Vol 29 Classified TOC)

The Topics page (`/topics.html`) uses a **category-bounded OCR architecture**. Per-page OCR was abandoned because multi-category pages (e.g. ws 902 holds both Education and Engineering, ws 945 holds Literature + Math + Medical) interleave content unrecoverably when read column-by-column. The approach:

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
- pytest (265 tests passing)

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

## Current State (2026-05-12)

- **Site live at britannica11.org** (last *deploy* predates the recent burndown — these rebuilds have been `--no-deploy`)
- **28 volumes processed** (vol 29 is end matter, excluded)
- **37,061 entries** in database: 36,663 articles + 398 plate inserts (`tools/rebuild_all.sh --no-deploy`, 2026-05-12, ~124 min)
- **31,953 cross-references resolved (86%)**
- **5,130 unresolved xrefs** (mostly portal links and literary work references)
- **~1,500 unique contributors** from front matter (most linked to articles)
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

### File-Level (2026-05-12 rebuild)
- unhandled_marker_in_htmltable: 16 (▲1 — needs a look; likely a `«CHEM:` block or HTMLTABLE with an unstripped marker)
- stray_close_braces: 9, stray_braces: 7 (math braces vs templates — QUATERNIONS/WAVE/VALUE; templates with open parens — TANCRED/THEODORE; editor typos — ST LOUIS)
- pipe_leak: 2, leaked_html_attr: 1 (JESUS CHRIST — `{|cellpadding="5" rules="cols"` prefix on the *restored* Gospel paragraph; proper fix is noinclude-layout-table handling in transform), html_tag: 1 (POST vol 22 — pre-existing malformed `«HTMLTABLE:`)

**Landed since 2026-04-17:** the entire "Queued for next rebuild" backlog below (the 2026-04-17 / 2026-04-20 / 2026-05-03 / 2026-05-08 / 2026-05-09 entries) is in the `b7f6t90jz` (2026-05-12, ~130 min) and/or the 2026-05-12 (~124 min) rebuilds. Also landed: the `transform_articles` extract-process-reassemble refactor; the `clean_body` burndown (15→6 passes, word_count/sections from cleaned body, `clean_caption` consolidation, INFINITESIMAL CALCULUS math-mask fix, FN-as-caption); the chemistry-layout skeleton (`«CHEM:` markers, viewer rendering still TODO); the plate-detection two-pass restructure (328→398 plates, `_split_out_plates` stateless PASS 1 + plate-free article state machine). `parse_plate` (the 4-stage plate parser) is done and live. *Open follow-up:* `parse_plate` doesn't pick up `[[Image:…]]<br>{{smaller|caption}}`-after-image captions (ROBES PLATE II's 6 robe images come out uncaptioned — better than the old `||`-junk, but a caption-consolidation item).

### File-Level (historical — 2026-04-07 build, for reference)
- stray_close_braces: 58 (mostly false positives from LaTeX braces in MATH blocks)
- pipe_leak: 30, html_tag: 28, stray_wiki_italic: 15 (increased from layout table unwrapping exposing previously hidden markup)
- stray_braces: 14, leaked_html_attr: 8, stray_control_x06: 4, stray_control_x03: 1

### 2026-04-18: Topic-index cleanup (LLM-assisted)
New infrastructure for improving `classified_toc.json` (Topics page) post-build, without rebuilding the corpus:

- **`tools/vol29/disambiguate_toc.py`** — ambiguous TOC entries (e.g. "ABEL" matches multiple articles) get resolved per category via Haiku 4.5 batch calls with structured output. Candidates include parenthetical-qualifier variants (PAMPHILUS → matches PAMPHILUS (PAINTER), PAMPHILUS (TEACHER)) and Surname,Firstname forms. Cached in `data/derived/toc_disambiguation_cache.json` by (target, path, candidate filenames) — cache survives rebuilds because stable IDs are stable. Two passes delivered **931 corrections**: ABEL (chemist vs. biblical vs. composer vs. mathematician), SWIFT (Jonathan vs. the bird), CAUCHY, MARRYAT, BARERE, CLEMENTI etc., plus PAMPHILUS-family cases after the qualifier-aware fix.
- **`tools/vol29/cleanup_toc.py`** — removes known OCR artifact targets (SEE, GENERAL) and within-node duplicates. Ran once: 15 artifacts + 53 dupes cleared.
- **`tools/vol29/detect_toc_artifacts.py`** — second-pass LLM classifier for short generic-looking targets (1-2 word entries appearing ≥3 times and linked to plain-title articles). Asks Haiku whether the entry is a legitimate cross-reference in its category or OCR bleed. Three-stage workflow: dry-run (free scan) → unbated run (submit batch, print proposed removals, don't modify) → `--apply` (actually remove). Decisions cached in `data/derived/toc_artifact_cache.json`; user can flip any `false` → `true` to override. Removed 41 artifact entries.
- **`data/corrections.json`** — general source-text correction layer applied in `_transform_text_v2` before any other processing. Keys are `"vol:page"`, values are `[{from, to}]` replacement lists. First use: Swift article's `secretary y` typo on vol 26 p244.

**Known deferred for TOC improvement:**
- Expand candidate matching to strip space-word qualifiers ("OTTAWA TRIBE" → also register under OTTAWA; "CONON OF SAMOS" → CONON; "AETIUS OF AMIDA" → AETIUS). Same pattern as the PAMPHILUS (PAINTER) fix but for space-separated suffixes like TRIBE / RIVER / ISLAND / OF X. Currently the LLM removes these bare entries as artifacts; with the fix, they'd route to the more specific articles instead.

### Landed in 2026-04-17 rebuild
- **Boundary & title fixes**: Œ/Ś/Ḍ/Ḥ etc in uppercase class; parenthetical/bracketed qualifiers preserved; regnal numerals allowed; `{{nop}}`/`{{clear}}`/`{{-}}` stripped; `<big>`/`<small>` dropcap tags stripped; plate-detection threshold tightened. +1,162 articles surfaced.
- **Transform**: `{{EB1911 tfrac}}` vulgar fractions; `,,` ditto preservation; `{{sic|word}}` preserves word; count-aware `_strip_excess_closers` for orphan `}}`.
- **Elements**: `_strip_br` soft-hyphen helper; `«LN:»` marker cleanup; `||`→`\n|` cell normalization; `{{Ts|…}}` styling templates stripped; `_process_html_table` colspan/rowspan → HTMLTABLE with structure preserved; extended `{{img float}}`/`{{figure}}`/`{{FI}}` patterns.
- **Export**: `_find_parent` page-range containment for plate lookup.
- **Contributors**: ArticleSegment-scoped footer matching (fixes MALONIC ACID).
- **Xrefs**: `_is_bibliographic` filter drops junk citations. Resolution: 89% → 92%.
- **Stable article IDs** (scholarly link durability): `{vol:02d}-{page:04d}-{section-slug}` format (e.g. `16-0670-lighthouse`). Article model has `section_name` column. Viewer URL routing updated site-wide (`viewer.html`, `index.html`, `contributors.html`, `preface.html`, `topics.html`, `build_about_page.py`). Unicode-aware regex (`\p{Lu}`) for non-ASCII titles like MANŒUVRES.
- **Rebuild script**: Phase 6c/6d added; paths updated for tools/ subdirectory reorg.
- **Quality report**: `unhandled_marker_in_htmltable` check; lowercase-title filter handles parenthetical/bracketed forms + Mc/Mac name prefixes.

### Queued for next rebuild (staged post-2026-04-17 from live debugging)

**Critical: biographical articles missing (pre-existing, not a session regression)**
- `detect_boundaries.py`: the "Title-Case section name = subsection continuation" rule was incorrectly firing on biographical `Surname, Firstname` section names. Added a `_is_bio_section` filter that exempts `^[A-Z][a-z…]+, [A-Z]` patterns. Also extended first-line detection to span multi-line `[[Author:…]]` wrappers (fixes COMTE specifically where the Author wikilink broke across lines).
- Confirmed missing articles include: **COMTE (Auguste), MARRYAT (Captain Frederick), CLEMENTI (Muzio), CANTU (Cesare), BARERE (de Vieuzac, Bertrand), BAANFFY (Dezsö)**, plus ~dozens more — estimated 20–40 biographical articles total across the corpus (diagnostic at `tools/diagnostics/find_missing_sections.py` flags ~43 but includes false positives from middle-name variants). Rerun after rebuild and compare against the "Surname, Firstname" section-name list.

**Critical: stray_close_braces regression (9 → 613) from `{{nowrap|` preprocessing**
- My earlier `{{nowrap|` prefix-strip was too aggressive: it stripped openers of balanced nested nowraps (e.g. AARD-VARK's `{{nowrap|17{{EB1911 tfrac|2}} in.;}}`), leaving orphan `}}`. Replaced with `_strip_unclosed_nowrap` that only strips openers lacking a matching `}}`.
- Also removed speculative `_strip_templates` catch-all `{{name|` opener-strip, which was a safety-net causing similar balanced-template regressions.

**Title-duplication at body start (POPILIA pattern, this-session artifact)**
- `_strip_redundant_title` helper in `article_json.py` now handles multi-bold titles like `«B»POPILIA«/B» (or Popillia), «B»VIA,«/B» the name …` by accumulating consecutive bold+interstitial chunks and matching against the full article title. Old single-bold strip left `(or Popillia), VIA,` duplicated.



**Element extraction leaks found during live inspection**
- `_unwrap_layout_table` (elements.py) — placeholder-containing cells now split on `\x06…\x06` / placeholder boundaries so surrounding text (entities, italic) goes through `text_transform`. Fixes EGYPT hieroglyph table `''ỉb''` italic leak and similar.
- `_unwrap_html_illustration` (elements.py) — same placeholder-split fix. Clears HYDRAULICS `&emsp;` leaks in multi-image table captions.
- `_process_html_table` (elements.py) — no-`<tr>` branch now runs `text_transform` on extracted `<td>` cell content. Fixes HYDRAULICS math-equation cells with `<table><td>…</td></table>` syntax (no tr wrappers).

**Transform fixes**
- `{{nowrap|` unclosed-opener strip (transform_articles.py `_transform_text_v2`) — strips `{{nowrap|` prefix before cell parsing so its inner `|` doesn't leak as a cell separator. Clears attr leaks in CUNEIFORM, EGYPT, NIHILISM, PERSIA, SIAM, ZEUXIS.
- `_strip_templates` unclosed-opener fallback — strips any `{{name|` / `{{name,` prefix surviving the balanced-template pass. Catches other malformed-source templates (watch for regressions).
- `{{EB1911 lkpl|target|display|}}` with empty trailing param — display now falls back to target instead of producing `\x06target|\x06` (empty-display link that `_finalize_markers` can't convert).
- `{{1911link|target|nosc=yes}}` named-arg handling — `nosc=yes`-style positional args dropped; display falls back to target. Fixes `«SH»Aden|nosc=yes«/SH»` leaks.
- `{{abbr}}` / `{{tooltip}}` first-param regex allows embedded `\x06…\x06` link markers as atomic (not bisected on their internal pipe).
- Shoulder-heading extractor (`_convert_shoulder_headings`) treats `\x06…\x06` and `[[…]]` as atomic blocks when finding the last top-level pipe. Fixes SOMALILAND, UNITED KINGDOM `«SH»Iron\x06.«/SH»` / `«SH»Protectorate\x06.«/SH»` leaks.

**Metric wins expected on next rebuild**
- `stray_wiki_italic`: 21 → 12 (HYDRAULICS 62 occ + EGYPT 32 occ cleared; 12 remaining are smaller edge cases in paths the fix didn't touch).
- `leaked_html_attr`: 12 → 8 (the `{{nowrap|` prefix strip cleared ~5 articles).
- `stray_control_x06`: 6 → 1 (LOOM, MAP, ROME, SOMALILAND, UNITED KINGDOM cleared; MENSURATION has deeper math-template issues remaining).

**Viewer (already deployed, no rebuild needed)**
- `formatCell` extended for MATH (KaTeX inline) and VERSE (newline → `<br>`). ABBREVIATION `\Bigg}` brace and CHAETOPODA verse legend now render.
- HTMLTABLE cells pass through `formatCell` — IMG/FN/hieroglyph markers render.
- Page markers inside HTMLTABLE cells hoisted to row level.
- Wide-table modal: HTMLTABLE blocks ≥10 columns get an Expand button opening a resizable/fullscreen modal (LIGHTHOUSE Tables VI, VII).
- Wiki `{{TABLE:}}` renderer protects `\n` inside `{{VERSE:…}VERSE}` blocks from row-splitting.
- Quality report: MATH/VERSE removed from HTMLTABLE exemptions.
- Nav standardized site-wide: Home · Articles · Contributors · Topics · Ancillary.
- Scans page `fm_first_content.json` blank-skip; vol 20 shows DLI Bengal leaf scans.
- Index page Enter-to-search + result count.
- Topics page hierarchical collapsibility, nav arrows.

**Known deferred (not in this rebuild)**
- **Wiki-table illustration unwrapping**: `_process_table` in `elements.py` needs extension for 3+ row illustration tables with multi-cell legends (CHAETOPODA vol 5 Fig. 2; IRON AND STEEL vol 14 Fig. 13 pig-casting). Emit `{{IMG:filename|caption}}` + remaining rows as paragraphs/verse.
- **Wide MATH blocks** (ALGEBRAIC FORMS) — reuse the HTMLTABLE wide-table modal pattern for `.katex-display` blocks that exceed article-column width.
- **html_tag leaks** (76 files, 360 tags total): (a) 218 `<br>` inside image captions from multi-column wiki tables where side-by-side cells zip without re-running `text_transform`; (b) 117 `<sub>`/`<sup>` inside chemistry formula fragments around `{{IMG:Langle.svg}}` brackets; (c) 15 `<td>` + 6 `<tr>` from tables partially escaping extraction. Trace the `|caption ||}}` pattern in `elements.py`.
- **Malformed source: HTML table with wiki-cell-pipes** (HYDRAULICS math equations): `<td>content |rowspan=3|<math>...</math></td>` mixes wiki-table syntax inside HTML. Needs mixed-syntax detector.
- **Remaining stray-italic edge cases** (12 files): scientific names adjacent to IMG markers (BROMELIACEAE, BRYOPHYTA, POLYGONACEAE etc.), single-char variables in math (IRIS figure labels), book-title italics (BEE, MITRE).
- **Remaining `\x06` in MENSURATION**: math-template interleaving produces `\x06V`, `\x06Differences` orphan markers. Deep-math-template issue.
- **stray_close_braces / stray_braces** (9 close + 8 open, 14 articles): math braces colliding with templates (QUATERNIONS, WAVE, VALUE); templates with open parens (TANCRED, THEODORE); editor typos (ST LOUIS).

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

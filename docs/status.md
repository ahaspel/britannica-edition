# Britannica Edition – Project Status

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
- **Cross-reference links** — `«LN:target|display«/LN»` first-mention hyperlinks
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

### Stack

- Python (3.12), SQLAlchemy, Typer, Postgres, Meilisearch, KaTeX
- pytest (119 tests passing)

## Pipeline Stages

1. **Fetch** — Wikisource pages (3s delay, 350-page batches, 15-min cooldown)
2. **Import** — cleaned preview into SourcePage
3. **Clean** — NFC unicode, headers, hyphenation, reflow, whitespace, plate layout, leaked markup cleanup, unclosed marker repair
4. **Detect boundaries** — section-marker based (no heuristic fallback)
5. **Classify** — article, front_matter, plate (with grid parser for multi-section plates)
6. **Extract xrefs** — q.v., See, See also, inline link markers, `{{EB1911 article link}}`
7. **Resolve xrefs** — unified lookup (canonical + aliases + fuzzy)
8. **Extract images** — from raw wikitext, Wikimedia Commons URLs
9. **Extract contributors** — footer initials + front matter biographical tables
10. **Export** — article JSON (with page numbers in segments), index.json, contributors.json, front_matter.json
11. **Post-process** — safety-net cleanup on exported JSON (leaked attrs, pipe tables, width directives)
12. **Index search** — Meilisearch full-text

## Scripts

- `tools/rebuild_all.sh` — Full rebuild of all 28 volumes (8 phases: wipe, pipeline, xref resolve, re-export, front matter, post-process, reindex, quality report)
- `tools/start_services.sh` — Start/stop local Postgres, Meilisearch, and web server
- `tools/deploy.sh` — Upload to S3, invalidate CloudFront, index production Meilisearch
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

- **home.html** — landing page with title page scan and navigation links
- **index.html** — volume tabs (data-driven labels), title/full-text/contributor search, alphabetic page navigation per volume
- **viewer.html** — articles with volume:page citations in left margin, shoulder headings in right margin, inline images, footnotes, tables (including inline single-row tables), sections/TOC, in-article search, bold/italic/small-caps/hieroglyph rendering
- **search.html** — Meilisearch full-text with highlighted snippets, formatting marker cleanup
- **contributors.html** — sorted by surname, credentials, descriptions, full article lists
- **preface.html** — Hugh Chisholm's 1910 editorial preface with drop caps and shoulder headings

## Current State (2026-04-02)

- **Site live at britannica11.org**
- **28 volumes processed** (vol 29 is end matter, excluded)
- **35,075 articles** in database
- **20,977 cross-references resolved** (84%)
- **3,925 unresolved xrefs** (mostly portal links and literary work references — legitimately unresolvable)
- **~1,500 unique contributors** with biographical data
- **119 tests passing** — section boundaries, formatting, integration
- **132 file-level issues** across 35K+ articles (down from 607)
- **All data fetched** — raw wikitext is static, never changes

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
1. Run `tools/rebuild_all.sh` locally
2. `aws s3 sync data/derived/articles/ s3://britannica11.org/data/`
3. Upload HTML files and title_page.jpg to bucket root
4. `aws cloudfront create-invalidation --distribution-id E24BJKH0IB4I6 --paths "/*"`
5. `MEILI_URL=http://44.222.119.72:7700 MEILI_MASTER_KEY=gibbon-winters-lewis uv run python tools/index_search.py`

## Known Issues (remaining)

### File-Level (132 total across 35K articles)
- **pipe_leak (80)** — orphaned pipe-separated data not inside TABLE markers; mostly tabular data (governor lists, statistics) that the fetch stage didn't wrap. Some are legitimate (poetry scansion, math)
- **leaked_html_attr (15)** — residual `nowrap`, `colspan` etc. in edge cases the postprocessor doesn't catch
- **unclosed_footnote (12)** — footnotes spanning table boundaries in complex tabular articles
- **html_tag (12)** — garbled OCR artifacts that look like HTML tags
- **stray_wikilink (11)** — `[[Author:...]]` links and math notation containing `[[`
- **unclosed_table (2)** — tables spanning page boundaries

### Other
- Some pages have `pagequality level="3"` (not fully proofread) on Wikisource
- ~44 structural chemical formulas render as preformatted `«PRE:...«/PRE»` blocks
- Contributor death dates sometimes lost in template stripping
- Portal links and literary work references (CANDIDE, PARADISE LOST) are legitimately unresolvable xrefs
- `_parse_page` heuristic still exists in code but is not called in production
- Garbled text `wisth=7|` in EGYPT shoulder heading (postprocessor fix queued, needs rebuild)
- Title page scan still has faint artifacts from the IA source copy
- Meilisearch EC2 port 7700 currently open to all traffic — should be restricted to CloudFront IPs

## Next Steps

### Needs one more rebuild
- Plate layout cleanup with keyword-matched captions
- Page number in segment export (for margin citations)
- Postprocessor fixes (garbled attrs, orphan table wrapping, width directive stripping)
- Front matter export integrated into rebuild script

### Short-term
- "About This Edition" page (editor's introduction)
- EPUB export
- Image download from Commons (self-contained edition)
- Lock down Meilisearch security group to CloudFront IPs only

### Medium-term
- Typography polish
- Citation export (BibTeX, Chicago style)
- Front matter page scans from IA

# Britannica Edition – Project Status

## Overview

A scholarly digital edition of the 1911 Encyclopedia Britannica — the first hyperlinked, searchable, fully annotated edition with proper rendering of Greek, Hebrew, mathematical notation, chemical formulas, footnotes, images, verse quotations, and contributor attribution.

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
- **Hieroglyphics** — preserved as `[hieroglyph: notation]`

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
3. **Clean** — NFC unicode, headers, hyphenation, reflow, whitespace
4. **Detect boundaries** — section-marker based (no heuristic fallback)
5. **Classify** — article, front_matter, plate (with grid parser for multi-section plates)
6. **Extract xrefs** — q.v., See, See also, inline link markers, `{{EB1911 article link}}`
7. **Resolve xrefs** — unified lookup (canonical + aliases + fuzzy)
8. **Extract images** — from raw wikitext, Wikimedia Commons URLs
9. **Extract contributors** — footer initials + front matter biographical tables
10. **Export** — article JSON, index.json, contributors.json
11. **Index search** — Meilisearch full-text

## Scripts

- `tools/rebuild_all.sh` — Full rebuild of all 28 volumes from cached wikitext (wipe, import, clean, detect, classify, extract, resolve, export, reindex, quality report)
- `tools/start_services.sh` — Start/stop Postgres, Meilisearch, and web server
- `tools/run_volume.sh <vol> [--skip-fetch]` — Single volume pipeline
- `tools/quality_report.py` — Quality analytics with before/after comparison

## Data Model

- **Article** — title, volume, page range, body, article_type
- **ArticleSegment** — provenance (text ↔ source page)
- **CrossReference** — see, see_also, qv, link types
- **ArticleImage** — filename, caption, Commons URL
- **Contributor** — initials, full_name, credentials, description
- **ArticleContributor** — maps contributors to articles

## Viewer

- **index.html** — volume tabs (data-driven labels), title/full-text/contributor search, alphabetic page navigation per volume
- **viewer.html** — articles with inline images, footnotes, tables, sections/TOC, in-article search, bold/italic/small-caps rendering
- **search.html** — Meilisearch full-text with highlighted snippets
- **contributors.html** — sorted by surname, credentials, descriptions, article lists

## Current State (2026-04-02)

- **28 volumes processed** (vol 29 is end matter, excluded)
- **~35,175 articles** in database
- **~21,600 cross-references resolved** (83%+)
- **~1,500 unique contributors** with biographical data
- **119 tests passing** — section boundaries, formatting, integration
- **Quality check: ~600 file-level issues** across all volumes (stray markup, unclosed markers)
- **All data fetched** — raw wikitext is static, never changes

## Known Limitations

- Some pages have `pagequality level="3"` (not fully proofread) on Wikisource
- ~44 structural chemical formulas render as preformatted `«PRE:...«/PRE»` blocks
- Image-legend pairing not yet implemented in viewer
- Contributor death dates sometimes lost in template stripping
- Front matter rendered as text, not as original page scans
- Portal links and literary work references (CANDIDE, PARADISE LOST) are legitimately unresolvable xrefs
- `_parse_page` heuristic still exists in code but is not called in production

## Production Deployment

### Domain
- **britannica11.org** — owned, DNS via Route 53

### Architecture
- **`britannica11.org`** — single S3 bucket + CloudFront, serving everything
  - `/` — HTML viewer files (index, viewer, search, contributors)
  - `/data/` — article JSONs, index.json, contributors.json, volumes.json
  - `/search-api/` — proxied to Meilisearch (EC2 or Fargate) via CloudFront origin

### URL Scheme
- `/` — article index (browse, title search, full-text search, contributor search)
- `/article/{page}/{slug}` — article viewer (e.g. `/article/367/pharaoh`)
- `/search` — dedicated search page
- `/contributors` — contributor index

Article URLs are stable across rebuilds: derived from Wikisource page number + title, both of which are immutable. Verified unique across all 35K+ articles.

### S3 Bucket Contents
- `/index.html`, `/viewer.html`, `/search.html`, `/contributors.html`
- `/data/*.json` — article files, index.json, contributors.json, volumes.json

Same files the local export produces, uploaded with `aws s3 sync`.

### CloudFront Configuration
- ACM certificate for `britannica11.org`
- Default origin: S3 bucket
- Second origin: Meilisearch EC2 for `/search-api/*` path pattern
- CloudFront function to rewrite `/article/*` requests to `/viewer.html`
- No CORS needed — everything served from same domain

### Meilisearch
- Single instance on EC2, ~1GB RAM sufficient for 35K articles
- Production master key (any strong password, set at startup)
- Search-only API key generated from master key, embedded in viewer HTML

### Deploy Process
1. Run `tools/rebuild_all.sh` locally (produces all derived data)
2. Run deploy script to upload `data/derived/` to S3
3. Invalidate CloudFront cache
4. Re-index Meilisearch (point `tools/index_search.py` at production URL)

### Viewer Auto-Detection
All viewer pages detect local vs production via hostname. On localhost they use local file paths and the dev Meilisearch; in production they use `data.britannica11.org` and `search.britannica11.org`.

## Next Steps

### Immediate
- Complete rebuild with all pending fixes (plate layout, page citations, clean stage improvements)
- Deploy to britannica11.org

### Short-term
- EPUB export
- Image download from Commons (self-contained edition)
- Front matter as page scans
- Editorial introduction

### Medium-term
- Subscription-based access
- Typography polish

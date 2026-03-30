# Britannica Edition – Project Status

## Overview

This project produces a scholarly digital edition of the 1911 Encyclopedia Britannica — the first hyperlinked, searchable, fully annotated edition with proper rendering of Greek, Hebrew, mathematical notation, chemical formulas, footnotes, images, and contributor attribution.

## Architecture

### Stack

- Python (3.12)
- SQLAlchemy (ORM)
- Typer (CLI)
- Postgres (Docker, local dev)
- Meilisearch (Docker, full-text search)
- KaTeX (LaTeX math rendering in viewer)
- pytest (unit + integration tests)

## Core Data Model

- **SourcePage** — raw input pages with original and cleaned text
- **Article** — logical encyclopedia entry (title, volume, page range, body, article_type)
- **ArticleSegment** — provenance layer mapping text to source pages
- **CrossReference** — extracted references between articles (see, see_also, qv, link)
- **ArticleImage** — image metadata with Wikimedia Commons URLs
- **Contributor / ArticleContributor** — author attribution from footer initials

## Pipeline

### Stages (in order)

1. **Fetch** — Wikisource pages with rate limiting (3s delay, 350-page batches, 15-min cooldown)
2. **Import** — cleaned preview into SourcePage
3. **Clean** — unicode (NFC), headers, hyphenation, paragraph reflow, whitespace
4. **Detect boundaries** — article/plate/front matter separation with 15+ title filters
5. **Classify** — article, front_matter, plate
6. **Extract xrefs** — q.v., See, See also, inline link markers
7. **Resolve xrefs** — exact match, alias lookup, fuzzy matching (per-volume and cross-volume)
8. **Extract images** — from raw wikitext, Wikimedia Commons URLs
9. **Extract contributors** — from EB1911 footer initials templates
10. **Export** — article JSON, index.json, contributors.json
11. **Index search** — Meilisearch full-text indexing

### Fetcher Features

- Preserves `\n` vs `\n\n` distinction (hard wraps vs paragraph breaks)
- Strips HTML comments without false paragraph breaks
- Strips shoulder headings without false paragraph breaks
- Converts footnotes to `«FN:...»` markers
- Converts images to `{{IMG:...}}` markers (survive pipeline)
- Converts tables to `{{TABLE:...}TABLE}` markers (protected from reflow)
- Converts cross-reference links to `«LN:target|display»` markers
- Converts LaTeX math to `«MATH:...»` markers
- Preserves Greek (`{{Greek|...}}`), Hebrew (`{{Hebrew|...}}`), Polytonic text
- Converts subscripts to Unicode (H₂O, CO₂)
- Converts superscripts to Unicode (x², m³)
- Converts fractions to Unicode (½, ¾, ⅜) or text fractions (1⁄225)
- Preserves `{{nowrap|...}}` content
- Parses HTML plate tables into sectioned image+caption pairs
- Extracts table content as pipe-delimited text

### Boundary Detection Features

- Multiple articles per page, multi-page articles
- Plate page detection with grid parsing (images paired with section labels and captions)
- Paragraph-structure preservation through parsing
- Table-block awareness (no heading detection inside tables)

### Title Extraction Filters

- Strips parenthetical content (etymologies, dates, alternate names)
- Strips trailing mixed-case descriptors (Greek, Grand Master)
- Strips 2-letter formula fragments after comma (CH)
- Rejects author initials, wikitext artifacts, chemical formulas
- Rejects lines starting with digits, pure Roman numerals, numbered section headings
- Rejects lines containing bare pipes (table content)
- Rejects titles where text runs directly into lowercase
- Strips trailing periods
- Pulls trailing dates into title (WAR OF 1812)
- Supports accented characters (É, À, etc.)
- Max 40 chars for all-caps-only lines
- 2-letter title allowlist

### Xref Resolution

- Unified lookup: canonical titles + aliases + fuzzy matching
- Aliases harvested from `{{EB1911 lkpl|Target|Display}}` templates
- Fuzzy: plural/singular normalization, name inversion (FIRST LAST ↔ LAST, FIRST)

## Viewer

### Pages
- **index.html** — article index with volume tabs (historical spine labels), search, filters
- **viewer.html** — article display with inline images, footnotes, tables, sections, in-article search
- **search.html** — full-text search via Meilisearch with highlighted snippets
- **contributors.html** — contributor index sorted by surname

### Rendering Features
- Paragraphs with text-indent
- Section headings (`h3`) detected from em-dash pattern
- Table of contents for articles with 3+ sections
- Inline images from Wikimedia Commons
- Footnotes with superscript numbers and Notes section
- Tables rendered as HTML
- First-mention hyperlinks (Wikipedia-style)
- Cross-reference links with navigation
- Plate links from articles to plate pages
- In-article text search with highlighting
- Volume-ordered display (original encyclopedia sequence)
- KaTeX rendering for LaTeX math

## Batch Scripts

- `./tools/run_volume.sh <volume> [--skip-fetch]` — full pipeline for one volume (page counts built in for all 29 volumes)
- `./tools/fetch_all.sh` — fetch all 29 volumes sequentially with rate limiting
- `uv run britannica resolve-xrefs-all` — cross-volume xref resolution with aliases
- `uv run python tools/index_search.py` — reindex Meilisearch

## Testing

89 tests passing — unit tests for all cleaners, heading detection, xref extraction/resolution, fuzzy matching; integration tests for full pipeline, boundary detection, article export.

## Current State

- **14 volumes processed** (~15,000 articles)
- **Remaining volumes fetching** via fetch_all.sh
- **36% xref resolution** (improving with each volume added)
- **~1,100 aliases** harvested from wikitext link templates

### Unicode/Script Support
- Greek text (ἅκαρι, καταλαμβάνειν, προσῳδία)
- Hebrew text
- Chemical subscripts (H₂O, CO₂, CH₃COOH)
- Superscripts (x², m³)
- Fractions (½, ¾, ⅜, 1⁄225)
- LaTeX math (rendered via KaTeX)
- Accented characters in titles (AUTO-DA-FÉ)

## Known Limitations

- Some internal section headings may still create false articles
- Not all plate pages use HTML table format (some use wiki tables)
- `<math>` rendering requires internet (KaTeX CDN)
- ACETIC ACID body missing "CH" prefix (title extraction artifact)
- Some front matter pages (contributor tables) produce empty articles
- Stale export files not cleaned automatically on re-export

## Next Steps

### Immediate
- Complete fetch of all 29 volumes
- Full reprocess with all accumulated fixes
- Verify xref resolution rate with complete data

### Short-term
- EPUB export (the distribution format)
- Image download from Commons (self-contained edition)
- Editorial introduction

### Medium-term
- Web hosting with stable URLs
- Subscription-based access
- Editorial review workflow
- Citation support
- Typography polish

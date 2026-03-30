# Britannica Edition – Project Status

## Overview

This project ingests, cleans, structures, and links content from the 1911 Encyclopedia Britannica into a normalized, queryable format — aiming for a proper scholarly edition publishable as an ebook and website.

Current focus:
- deterministic parsing
- inspectable intermediate stages
- incremental enrichment (source pages → articles → segments → xrefs → graph)
- real-page ingestion from Wikisource-backed transcriptions
- full-text search
- scholarly apparatus (footnotes, contributor attribution, images)

## Architecture

### Stack

- Python (3.12)
- SQLAlchemy (ORM)
- Typer (CLI)
- Postgres (Docker, local dev)
- Meilisearch (Docker, full-text search)
- pytest (unit + integration tests)

### Project Layout

src/britannica/
cli/
cleaners/
db/
models/
pipeline/
stages/
review/
xrefs/
export/
tools/

## Core Data Model

### SourcePage
- raw input pages
- stores original and cleaned text

### Article
- logical encyclopedia entry
- title, volume, page range
- aggregated body text
- `article_type`: `article`, `front_matter`, or `plate`

### ArticleSegment
- provenance layer
- maps portions of articles to source pages
- ordered (`sequence_in_article`)

### CrossReference
- extracted references between articles
- fields:
  - `surface_text`
  - `normalized_target`
  - `xref_type` (`see`, `see_also`, `qv`)
  - `target_article_id` (nullable)
  - `status` (`resolved`, `unresolved`)

### ArticleImage
- image metadata extracted from raw wikitext
- filename, caption, Commons URL
- linked to article and source page

### Contributor / ArticleContributor
- contributor names and initials from `{{EB1911 footer initials}}` templates
- maps contributors to articles

---

## Pipeline (Working)

### 1. Fetch raw pages from Wikisource
uv run python tools/fetch/fetch_wikisource_pages.py --volume <n> --start <page> --end <page> --outdir <dir>

- fetches Page:EB1911 - Volume XX.djvu/<page> from Wikisource
- stores raw wikitext + cleaned preview JSON per page
- preserves link text from `{{EB1911 lkpl|Target}}` cross-reference templates
- preserves subscript/superscript digits (chemical formulas stay recognizable)
- strips HTML comments (`<!-- column 2 -->` column markers) without false paragraph breaks
- strips shoulder headings without false paragraph breaks
- preserves `\n` vs `\n\n` distinction (hard wraps vs paragraph breaks)
- preserves `{{nowrap|...}}` content
- converts footnotes to `«FN:...»` markers (survive pipeline, rendered in viewer)
- converts images to `{{IMG:...}}` markers (survive pipeline, rendered inline)
- converts tables to `{{TABLE:...}TABLE}` markers (protected from reflow)
- 3s polite delay between requests; 350-page batches with 15-min cooldown
- exponential backoff on 429; skips already-fetched pages

### 2. Import fetched pages into SourcePage
uv run python tools/fetch/import_wikisource_pages.py --indir <dir> --volume <n>

- imports cleaned Wikisource page text into `SourcePage.raw_text`
- leaves `cleaned_text` null for normal pipeline cleaning
- supports overwrite/re-import workflow

### 3. Clean
uv run britannica clean-pages <volume>

- unicode normalization (NFKC)
- header stripping
- hyphenation repair
- paragraph reflow (joins hard-wrapped lines, preserves paragraph breaks, protects table blocks)
- whitespace normalization

### 4. Boundary Detection
uv run britannica detect-boundaries <volume>

Currently supports:
- multiple articles per page
- multi-page articles
- continuation pages (no heading)
- prefix continuation before new heading on same page
- heading/body split when article opener and first sentence share one line
- paragraph-structure preservation through parsing
- plate page detection (images go to plate entry, text flows through)
- table-block awareness (no heading detection inside tables)

Title extraction:
- strips parenthetical content from titles (etymologies, dates, alternate names)
- strips trailing mixed-case descriptors after comma (Greek, Grand Master, etc.)
- strips 2-letter formula fragments after comma (CH, etc.)
- rejects author initials (J., O., F., J. B., M. O. B. C.)
- rejects wikitext artifacts (}}, +T,}})
- rejects chemical formulas (middle-dot, arrow, or digit characters)
- rejects lines starting with digits (figure captions)
- rejects pure Roman numerals and numbered section headings (ORDER I, PART II, etc.)
- rejects lines containing pipe characters (table content)
- rejects titles where text runs directly into lowercase (glued table content)
- strips trailing periods from titles
- pulls trailing standalone dates into title (WAR OF 1812)
- requires 2+ consecutive uppercase letters
- max 40 chars for all-caps-only lines (rejects long figure captions)
- 2-letter title allowlist (AA, AB, AI, etc.)

### 5. Article Classification
uv run britannica classify-articles <volume>

- `article`: regular encyclopedia entries
- `front_matter`: pages before first real headword
- `plate`: detected during boundary detection (pages starting with 3+ images)

### 6. Xref Extraction
uv run britannica extract-xrefs <volume>

Detects:
- `Target (q.v.)` — dominant pattern; extracts proper-noun chain before `(q.v.)`
- `(See Target)` and `(See also Target)` — parenthesized references, splits on "and"
- `See TARGET` / `See also TARGET` — sentence-level all-caps references
- Deduplicates within each article
- Filters noise: broken markup artifacts, bibliographic citations, common-word false positives

### 7. Xref Resolution
uv run britannica resolve-xrefs <volume>
uv run britannica resolve-xrefs-all

- exact match on normalized title (per-volume)
- cross-volume resolution against all loaded articles
- fuzzy matching: plural/singular normalization, name inversion (FIRST LAST ↔ LAST, FIRST)

### 8. Image Extraction
uv run britannica extract-images <volume>

- extracts image metadata from raw wikitext files on disk
- parses filename, caption, generates Wikimedia Commons URL
- links images to articles via source page mapping

### 9. Contributor Extraction
uv run britannica extract-contributors <volume>

- parses `{{EB1911 footer initials|Full Name|Initials}}` templates from raw wikitext
- handles multiple contributors per article (name2, initials2, etc.)
- creates Contributor records and ArticleContributor links

### 10. Reporting

#### Unresolved xrefs
uv run britannica report-unresolved-xrefs <volume>

#### Backlinks
uv run britannica report-backlinks <volume>

### 11. Export
uv run britannica export-articles <volume>

Outputs per article:
- JSON with body, segments, xrefs (with target_filename for resolved links), images, plates, contributors
- index.json: article index with title, body_start, word count, xref counts, article_type
- contributors.json: contributor index sorted by surname with article lists

### 12. Full-Text Search
uv run python tools/index_search.py

- indexes all exported articles into Meilisearch
- searchable attributes: title, body, contributors
- instant search with highlighted snippets

### 13. End-to-end Batch Scripts

./tools/run_volume.sh <volume> [--skip-fetch]

- page counts for all 29 volumes built in
- wipes volume from database
- fetches from Wikisource (or skips with `--skip-fetch`)
- imports, cleans, detects boundaries, classifies, extracts xrefs/images/contributors, resolves, exports

./tools/fetch_all.sh

- fetches all 29 volumes sequentially
- skips complete volumes, resumes partial ones
- continues to next volume if one fails (resilient to rate limiting)

## Testing

### Run all tests
uv run pytest

### Coverage

#### Unit tests
- unicode normalization
- whitespace cleanup
- header stripping
- hyphenation
- paragraph reflow (including table block protection)
- heading detection (initials, artifacts, formulas, parentheticals, periods, descriptors, Roman numerals, section headings, captions, table content)
- page parsing
- roman utility
- xref extraction (q.v., See, See also, deduplication, noise filtering)
- xref resolution (exact match)
- fuzzy matching (plural/singular, name inversion)

#### Integration tests
- page cleanup pipeline (including reflow)
- boundary detection (multi-page + multi-article)
- boundary detection with false-positive initials filtering
- prefix + heading edge case
- xref extraction + resolution
- unresolved xref reporting
- backlinks reporting
- article export (with index.json and contributors.json)

All tests currently passing (87 tests).

---

## Current Capabilities

✔ deterministic parsing
✔ real-page ingestion from Wikisource transcriptions
✔ multi-page article reconstruction
✔ provenance tracking via segments
✔ cross-reference extraction (q.v., See, See also)
✔ exact-match and fuzzy resolution with viewer linking
✔ cross-volume xref resolution
✔ unresolved reference reporting
✔ backlinks (reverse graph)
✔ JSON export for downstream use
✔ inline images from Wikimedia Commons
✔ footnotes with superscript numbers and notes section
✔ tables preserved and rendered
✔ contributor extraction and contributor index
✔ article classification (article, front_matter, plate)
✔ plate page detection with correct text flow
✔ HTML viewer with article index, search, xref links, paragraph rendering
✔ full-text search via Meilisearch (instant, highlighted snippets)
✔ in-article text search with highlighting
✔ contributor index page (sorted by surname)
✔ repeatable batch workflow with --skip-fetch option
✔ title normalization (parentheticals, descriptors, formulas, section headings)
✔ paragraph reflow (hard-wrap joining, paragraph-break preservation)
✔ chemical formula filtering
✔ rate-limited Wikisource fetching with resume support (fetch_all.sh for all 29 volumes)

## Known Limitations

- some internal section headings may still create false articles in later volumes
- plate pages with multiple sections (ALLOYS/GUN-MAKING/IRON AND STEEL) are jumbled
- table header row detection not implemented (all rows rendered uniformly)
- stale export files not cleaned automatically on re-export
- chemical formula subscripts render as plain digits (not subscript characters)
- some names in FIRST LAST order rather than LAST, FIRST (Wikisource source issue)
- Article.body is stored (not yet derived from segments)

## Next Steps (Planned)

### Short-term

1. Complete the fetch of all 29 volumes (overnight job running)
2. Process all fetched volumes through the pipeline
3. Alias system for improved xref resolution

### Medium-term

- section/subsection structure within long articles
- multi-section plate handling
- editorial review workflow
- ebook export (EPUB with hyperlinked xrefs)
- derive `Article.body` from `ArticleSegment`
- image download from Commons for self-contained edition

### Long-term

- web hosting with stable URLs
- API access
- introductory essay and editorial notes
- mobile-responsive design
- citation support

## Development Notes

- Uses `src/` layout (important for imports)
- `.gitattributes` enforces LF line endings
- Docker required for local Postgres and Meilisearch
- tests use SQLite for speed/isolation
- `tools/` contains utility scripts for DB management, fetching, search indexing, and batch processing
- repeatable end-to-end reruns are part of normal parser development workflow
- viewer: `python -m http.server 8000` from project root
- viewer pages: index.html, viewer.html, search.html, contributors.html

## Status

System is stable, test-covered, and operating on real Wikisource page data at scale.

Current state:
- 5 complete volumes processed (7,454 articles)
- volumes 6-29 fetching overnight
- full pipeline: fetch → import → clean → detect → classify → xrefs → resolve → images → contributors → export → search index
- full-text search operational via Meilisearch
- footnotes, tables, inline images all preserved and rendered
- 87 tests passing
- 349 cross-references resolved (23% with 5 volumes)

Immediate focus:

👉 complete overnight fetch of remaining volumes
👉 process all volumes through pipeline
👉 alias system for improved xref resolution
👉 section heading refinement

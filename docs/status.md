# Britannica Edition – Project Status

## Overview

This project ingests, cleans, structures, and links content from the 1911 Encyclopedia Britannica into a normalized, queryable format.

Current focus:
- deterministic parsing
- inspectable intermediate stages
- incremental enrichment (source pages → articles → segments → xrefs → graph)
- real-page ingestion from Wikisource-backed transcriptions

## Architecture

### Stack

- Python (3.12)
- SQLAlchemy (ORM)
- Typer (CLI)
- Postgres (Docker, local dev)
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

---

## Pipeline (Working)

### 1. Fetch raw pages from Wikisource
uv run python tools/fetch/fetch_wikisource_pages.py --volume <n> --start <page> --end <page> --outdir <dir>

- fetches Page:EB1911 - Volume XX.djvu/<page> from Wikisource
- stores raw wikitext + cleaned preview JSON per page
- strips most page-scaffolding/templates/tables/images
- preserves link text from `{{EB1911 lkpl|Target}}` cross-reference templates
- preserves subscript/superscript digits (so chemical formulas stay recognizable)
- strips HTML comments (`<!-- column 2 -->` column markers)
- preserves `\n` vs `\n\n` distinction (hard wraps vs paragraph breaks)
- 2s polite delay between requests; exponential backoff on 429; skips already-fetched pages

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
- paragraph reflow (joins hard-wrapped lines, preserves paragraph breaks)
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

Title extraction:
- strips parenthetical content from titles (etymologies, dates, alternate names)
- rejects author initials (J., O., F., J. B., M. O. B. C.)
- rejects wikitext artifacts (}}, +T,}})
- rejects chemical formulas (middle-dot, arrow, or digit characters)
- strips trailing periods from titles
- requires 2+ consecutive uppercase letters

### 5. Xref Extraction
uv run britannica extract-xrefs <volume>

Detects:
- `Target (q.v.)` — dominant pattern; extracts proper-noun chain before `(q.v.)`
- `(See Target)` and `(See also Target)` — parenthesized references, splits on "and"
- `See TARGET` / `See also TARGET` — sentence-level all-caps references
- Deduplicates within each article
- Filters noise: broken markup artifacts, bibliographic citations, common-word false positives

### 6. Xref Resolution (v1)
uv run britannica resolve-xrefs <volume>

- exact match only (normalized title)
- sets `target_article_id`
- marks `resolved` / `unresolved`

---

### 7. Reporting

#### Unresolved xrefs
uv run britannica report-unresolved-xrefs <volume>

Used for:
- editorial review
- alias detection
- identifying gaps

---

#### Backlinks
uv run britannica report-backlinks <volume>

Shows:
- incoming links to each article

---

### 8. Export
uv run britannica export-articles <volume>

Outputs JSON per article for:
- inspection
- viewer rendering
- downstream search/indexing
- xref review
- includes `target_filename` for resolved xrefs (enables viewer linking)

### 9. End-to-end batch script
./tools/run_volume.sh <volume> <start_page> <end_page> [--skip-fetch]

- wipes volume from database and clears old exports
- fetches from Wikisource (or skips with `--skip-fetch` to use cached pages)
- imports, cleans, detects boundaries, extracts and resolves xrefs, exports
- `--skip-fetch` is useful for re-running pipeline after code changes without re-fetching

## Testing

### Run all tests
uv run pytest

### Coverage

#### Unit tests
- unicode normalization
- whitespace cleanup
- header stripping
- hyphenation
- paragraph reflow
- heading detection (including initials, artifacts, formulas, parentheticals, trailing periods)
- page parsing
- roman utility
- xref extraction (q.v., See, See also, deduplication, noise filtering)
- xref resolution

#### Integration tests
- page cleanup pipeline (including reflow)
- boundary detection (multi-page + multi-article)
- boundary detection with false-positive initials filtering
- prefix + heading edge case
- xref extraction + resolution
- unresolved xref reporting
- backlinks reporting
- article export

All tests currently passing (72 tests).

---

## Current Capabilities

✔ deterministic parsing
✔ real-page ingestion from Wikisource transcriptions
✔ multi-page article reconstruction
✔ provenance tracking via segments
✔ cross-reference extraction (q.v., See, See also)
✔ exact-match resolution with viewer linking
✔ unresolved reference reporting
✔ backlinks (reverse graph)
✔ JSON export for downstream use
✔ HTML viewer with article display, xref links, and paragraph rendering
✔ repeatable batch workflow with --skip-fetch option
✔ title normalization (parenthetical stripping, false-positive rejection)
✔ paragraph reflow (hard-wrap joining, paragraph-break preservation)
✔ chemical formula filtering
✔ rate-limited Wikisource fetching with resume support

## Known Limitations

- xref resolution is exact-match only (8.8% resolution rate on partial volume 1)
- no alias/variant title handling yet
- no fuzzy matching
- Article.body is stored (not yet derived from segments)
- front matter pages (title page, dedication) produce false articles
- chemical formula subscripts render as plain digits (not subscript characters)
- only ~591 of ~1029 pages fetched for volume 1 (Wikisource rate limiting)

## Next Steps (Planned)

### Short-term

1. Viewer article index
   - browse all exported articles without typing filenames
   - navigate between articles (next/prev)
   - surface suspicious entries (very short body, unresolved xrefs)

2. Scale to full volume 1
   - fetch remaining pages (592-1029)
   - validate pipeline at scale
   - measure xref resolution improvement with complete data

3. Alias system
   - map variant names → canonical titles
   - improve xref resolution
   - populate from stripped parentheticals (alternate names)

### Medium-term

- fuzzy xref resolution
- front matter detection/exclusion
- editorial tooling (review issues)
- diffing pipeline outputs
- derive `Article.body` from `ArticleSegment`
- search index (Meilisearch / Typesense)
- image metadata preservation
- multi-volume processing

## Development Notes

- Uses `src/` layout (important for imports)
- `.gitattributes` enforces LF line endings
- Docker required for local Postgres
- tests use SQLite for speed/isolation
- `tools/` now contains utility scripts for:
  - DB reset / wipe by volume
  - Wikisource fetch/import
  - end-to-end batch reruns
- repeatable end-to-end reruns are now part of normal parser development workflow
- viewer: `python -m http.server 8080` from project root, open at localhost:8080/tools/viewer/viewer.html

## Status

System is stable, test-covered, and operating on real Wikisource page data at scale (591 pages, 982 articles).

Current state:
- full pipeline working: fetch → import → clean → detect → xref extract → resolve → export
- title extraction is clean across tested ranges (pages 1-591)
- paragraph reflow produces readable flowing text with proper paragraph breaks
- cross-references extracted and resolved with viewer navigation
- 72 tests passing

Immediate focus:

👉 viewer article index for browsing
👉 complete volume 1 fetch
👉 alias system for improved xref resolution

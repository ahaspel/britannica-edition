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
  - `xref_type` (`see`, `see_also`)
  - `target_article_id` (nullable)
  - `status` (`resolved`, `unresolved`)

---

## Pipeline (Working)

### 1. Fetch raw pages from Wikisource
uv run python tools/fetch/fetch_wikisource_pages.py --volume <n> --start <page> --end <page> --outdir <dir>

- fetches Page:EB1911 - Volume XX.djvu/<page> from Wikisource
- stores raw wikitext + cleaned preview JSON per page
- strips most page-scaffolding/templates/tables/images
- preserves enough structure for downstream parsing

### 2. Import fetched pages into SourcePage
uv run python tools/fetch/import_wikisource_pages.py --indir <dir> --volume <n>

- imports cleaned Wikisource page text into `SourcePage.raw_text`
- leaves `cleaned_text` null for normal pipeline cleaning
- supports overwrite/re-import workflow

### 3. Clean
uv run britannica clean-pages <volume>

- header stripping
- unicode normalization
- whitespace normalization
- hyphenation repair

### 4. Boundary Detection
uv run britannica detect-boundaries <volume>

Currently supports:
- multiple articles per page
- multi-page articles
- continuation pages (no heading)
- prefix continuation before new heading on same page
- heading/body split when article opener and first sentence share one line

Current behavior on real Wikisource data:
- detects many real article starts successfully
- no longer requires headings to be isolated on their own line
- still over-captures some descriptive glosses into titles
- still admits some false-positive short/junk titles

### 5. Xref Extraction
uv run britannica extract-xrefs <volume>

Detects:
- `See X`
- `See also X`

---

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

## Testing

### Run all tests
uv run pytests

### Coverage

#### Unit tests
- unicode normalization
- whitespace cleanup
- header stripping
- hyphenation
- heading detection
- page parsing
- roman utility
- xref extraction
- xref resolution

#### Integration tests
- page cleanup pipeline
- boundary detection (multi-page + multi-article)
- prefix + heading edge case
- xref extraction + resolution
- unresolved xref reporting
- article export

All tests currently passing.

---

## Current Capabilities

✔ deterministic parsing  
✔ real-page ingestion from Wikisource transcriptions  
✔ multi-page article reconstruction  
✔ provenance tracking via segments  
✔ cross-reference extraction  
✔ exact-match resolution  
✔ unresolved reference reporting  
✔ backlinks (reverse graph)  
✔ JSON export for downstream use  
✔ minimal HTML viewer for inspecting exported articles  
✔ repeatable batch workflow for wipe → fetch → import → clean → detect → export

## Known Limitations

- xref resolution is exact-match only
- title extraction still over-captures descriptive glosses in some entries
- some false-positive headings still occur (e.g. initials / fragments / junk titles)
- hard-wrapped prose is not yet fully reflowed into readable paragraphs
- no alias/variant title handling yet
- no fuzzy matching
- Article.body is stored (not yet derived from segments)

## Next Steps (Planned)

### Short-term

1. Tighten title extraction
   - stop titles before descriptive glosses
   - improve handling of Britannica-style opening lines
   - reduce false positives like initials / fragments

2. Paragraph reflow
   - merge hard-wrapped prose lines into paragraphs
   - preserve true article boundaries while improving readability

3. Viewer refinement
   - add sample article index
   - improve navigation between exported articles
   - surface unresolved / suspicious boundaries clearly

4. Alias system
   - map variant names → canonical titles
   - improve xref resolution

### Medium-term

- fuzzy xref resolution
- editorial tooling (review issues)
- diffing pipeline outputs
- improved heading detection using neighboring-line context
- derive `Article.body` from `ArticleSegment`
- search index (Meilisearch / Typesense)

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

## Status

System is stable, test-covered, and now operating on real Wikisource page data.

Current state:
- end-to-end fetch → import → clean → detect → export workflow is working
- minimal viewer exists for inspecting exported article JSON
- boundary detection has improved substantially on real data
- the main open problem is now title extraction precision and remaining false-positive/false-negative heading cases

Immediate focus:

👉 tighten title extraction  
👉 improve paragraph reflow  
👉 continue validating real-page boundary detection with viewer-driven inspection



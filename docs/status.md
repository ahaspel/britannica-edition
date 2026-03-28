# Britannica Edition – Project Status

## Overview

This project ingests, cleans, structures, and links content from the 1911 Encyclopedia Britannica into a normalized, queryable format.

Current focus:
- deterministic parsing
- inspectable intermediate stages
- incremental enrichment (articles → segments → xrefs → graph)

---

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


---

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

### 1. Import
uv run britannica import-sample-pages ...


### 2. Clean
uv run britannica clean-pages <volume>

- header stripping
- unicode normalization
- whitespace normalization
- hyphenation repair

---

### 3. Boundary Detection
uv run britannica detect-boundaries <volume>

Supports:
- multiple articles per page
- multi-page articles
- continuation pages (no heading)
- prefix continuation before new heading on same page

---

### 4. Xref Extraction
uv run britannica extract-xrefs <volume>

Detects:
- `See X`
- `See also X`

---

### 5. Xref Resolution (v1)
uv run britannica resolve-xrefs <volume>

- exact match only (normalized title)
- sets `target_article_id`
- marks `resolved` / `unresolved`

---

### 6. Reporting

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

### 7. Export
uv run britannica export-articles <volume>

Outputs JSON per article:

- metadata
- segments
- xrefs
- resolution status

Output directory:
data/derived/articles/

---

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
✔ multi-page article reconstruction  
✔ provenance tracking via segments  
✔ cross-reference extraction  
✔ exact-match resolution  
✔ unresolved reference reporting  
✔ backlinks (reverse graph)  
✔ JSON export for downstream use  

---

## Known Limitations

- xref resolution is exact-match only
- no alias/variant title handling yet
- no fuzzy matching
- no UI yet
- Article.body is stored (not derived from segments yet)

---

## Next Steps (Planned)

### Short-term

1. Alias system
   - map variant names → canonical titles
   - improve xref resolution

2. Minimal HTML viewer
   - render articles from JSON
   - clickable cross-references

3. Search index
   - integrate Meilisearch / Typesense

---

### Medium-term

- fuzzy xref resolution
- editorial tooling (review issues)
- diffing pipeline outputs
- improved heading detection heuristics

---

## Development Notes

- Uses `src/` layout (important for imports)
- `.gitattributes` enforces LF line endings
- Docker required for local Postgres
- tests use SQLite for speed/isolation

---

## Status

System is stable, fully test-covered, and ready for:

👉 presentation layer (viewer)  
👉 or search integration  
👉 or smarter xref resolution  

---



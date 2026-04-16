# Pending fixes for next rebuild

## Source-code changes that need a pipeline rerun

### `detect_boundaries.py` — `{{nop}}` prefix blocking bold-heading check
- **Two-step fix** (the initial single-step version shipped in the 2026-04-15 rebuild but didn't work — the first-line pre-filter rejected `{{`-prefixed lines before the strip at `first_line_unwrapped` ever ran):
  1. Peel leading `{{nop}}` / `{{clear}}` / `{{-}}` templates off `stripped` *before* the first-line pre-filter.
  2. After peel, re-check the `{|` table-opener so `{{nop}}{|` doesn't bypass `_in_table` tracking (defensive — no such pattern found in corpus, but cheap to guard).
- **Why contributor linking needs this too:** John Morley is a contributor in vol 29's front matter. Phase 3b links contributor names to articles — if the MORLEY [of Blackburn] article doesn't exist in the DB, his contributor record has no article to attach to. The fix has to ride a **full** rebuild so Phase 2 → 3b → export all see the correct article boundary.
- **Example this fixes:** MORLEY [of Blackburn], JOHN MORLEY, Viscount (vol 18 p.840) — swallowed into MORLEY, HENRY. Source line:
  `{{nop}}[[Author:John Morley|'''MORLEY''' [{{sc|of Blackburn}}], '''JOHN MORLEY,''' {{sc|Viscount}}]]`
- **Corpus-wide scan:** 1 article matches the `{{nop}}[[Author|'''TITLE''']]` pattern (MORLEY). 18 other `{{nop}}`-prefixed lines are empty (`{{nop}}` alone) or decorative (`{{clear}}{{anchor|…}}`) — all continue to be skipped correctly by the post-peel filter.

## Full-text search overhaul (deploy-only)

Substantial UX rework of `index.html` full-text search:
- Per-article result card shows **every line containing the query** (paragraph-level snippets ±50 chars) with `<mark>`-highlighted matches. Mirrors viewer.html's in-article match list.
- **Exact substring only** — Meili fuzzy/prefix matches filtered out client-side (fixes `adamas` → `ADAMS` contamination).
- Title matching disabled in the UI — body text only.
- Results deduped by (title, volume, page) to collapse duplicate index entries.
- Sorted by **match count descending** (most-hit articles first); match count shown next to title.
- Each occurrence snippet is a link → `viewer.html?article=…&q=<term>&match=<N>`.

`viewer.html` consumes the new URL params: pre-populates the in-article search box, highlights all matches, scrolls to the Nth match. Preserves `q`/`match` across its URL rewrite (both local `?article=` and production `/article/{id}/{slug}`).

`search.html` is now a redirect shim to `index.html?q=…&mode=fulltext` (single source of truth for search).

### Indexer fixes (`index_search.py` + `index_search_ec2.py`)
- `body` added to `displayedAttributes` so the UI can retrieve match context. Without this, search.html cannot do client-side exact-match filtering.
- Batch size bumped 100 → 5000 so Meili ingests in far fewer tasks (local reindex was previously queuing ~370 sequential tasks).
- **EC2 note:** the updated `index_search_ec2.py` has been `scp`-pushed to the EC2 box directly; the next rebuild's `python3 ~/index_search_ec2.py` call will use it without any change to `rebuild_all.sh`.

## Topics / classified TOC (deploy-only, no rebuild needed)

Current state: category-bounded OCR + per-cat walker (see `project_vol29_parser.md`). 23,050 articles across 24 cats, 60 empty leaves. Further refinement is per-cat — edit individual `cat_ocr/<slug>.txt` or rerun `ocr_vol29_classified.py --only='Cat'`.

To deploy the current Topics state:
- `uv run python tools/parse_classified_toc.py` — regenerates `classified_toc.json` and per-cat files.
- Upload: `classified_toc.json`, `topics.html` to S3 + CloudFront invalidation.

## Pre-deploy checks (per `feedback_regression_scope.md`)

- Run `uv run python tools/quality_report.py` and compare its "Changes from Previous Build" section.
- 5×+ swings in `stray_wiki_italic`, `stray_braces`, `pipe_leak`, `html_tag` are likely regressions — investigate before deploy.
- Topics spot-check after deploy: Math (Pure/Applied/Biographies populated), Astronomy, Engineering, Law subs all have articles; verify the editors' introduction (collapsed) and source-scan link on `/topics.html`.

## Known issues (not rebuild-blocking)

- OCR quality is the ceiling for several flat cats' article recall. Math at 198/250, Astronomy 210, Physics 164. Further improvement requires multi-pass OCR (different upscales / engines) or manual correction. Per-cat iteration workflow in place (`tools/ocr_vol29_classified.py --only='X'`).
- Vol 20 trailing black pages — IA Bengal scan artifact, low priority.

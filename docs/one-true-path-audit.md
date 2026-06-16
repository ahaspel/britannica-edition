# The One True Path — Off-Path Survey & Wipe-List

**Date:** 2026-06-16  **Status:** enumeration complete; nothing deleted yet.

**Purpose.** Enumerate *everything* on the producer side that is not **on**, or **necessary to**, the single legitimate pipeline ("the One True Path"). Deletion follows this list — the order is fixed: *enumerate → wipe → only then rebuild.*

**Method.** Four parallel sweeps — (1) `elements/` producers, (2) the rest of `pipeline/`, (3) `src/britannica/` outside `pipeline/`, (4) `tools/` + rebuild reachability — each grepping the repo for live callers, then a Bash verification pass (0-byte census + dead-symbol reachability + double-walk/dup confirmation). `tools/_scratch/` (gitignored, ~830 untracked files) is excluded; it isn't tracked code.

---

## The One True Path (the keep-spine)

**Per volume:** 1) assemble leaves — **article/plate ONLY** — from SourcePage; 2) combine into one continuous stream (`make_stream`); 3) preprocess (corrections, quote-runs, entity-decode, page-seam heal); 4) walk & divide into articles (`super_walker` / `super_detect.detect_boundaries`).

**Per article:** 5a) preprocess (title, `«SEC»` anchors); 5b) walk/classify/produce `«…»` markers (`elements/`); 5c) reassemble; 5e) extract contributors **off the same 5b walk**.

**Corpus-wide** (after all articles walked): build the xref resolution index and assign xrefs — **one** pass.

**Then:** 6) write finished articles to disk as JSON (`export/`).

**Legitimately separate — necessary, NOT wiped:** the contributor-list build (vol-29 index + front-matter harvest); reader's-guide / ancillary / static site pages; the viewer; the standing QA/regression toolkit; manual asset-acquisition (fetch/import/download) and dev/deploy helpers.

**Disposition tags.** **PURE-DELETE** — nothing live depends on it. **SURGICAL** — module stays, a named dead def/import/constant inside it goes. **FIX-FIRST** — it runs today; its one legitimate function must move onto the spine first, *then* it goes. Only FIX-FIRST items carry risk; everything else is a free deletion.

---

## A. Phantom subsystems — empty 0-byte stub modules  · PURE-DELETE · high

Entire packages scaffolded and never built (verified: every file 0 bytes, no importer). **Delete the whole directory:**

- `src/britannica/ai/` — client, schemas, trace, __init__  (4)
- `src/britannica/domain/` — contracts, enums, ids, types, __init__  (5)
- `src/britannica/io/` — checksums, files, html, images, jsonl, __init__  (6)
- `src/britannica/sources/` — base, internet_archive, local_text, wikisource, __init__  (5)
- `src/britannica/review/` — heuristics, issue_builder, __init__  (3)
- `src/britannica/db/repositories/` — articles, pages, sources, __init__  (4) — the pipeline talks to the DB via `db.session` + models directly; there is no repository layer

**Scattered empty stubs** (delete the file; the package stays, it has live siblings):

- `src/britannica/logging.py`
- `src/britannica/pipeline/{orchestrator,provenance,results,state}.py`
- `src/britannica/util/{text,metrics,timing}.py`
- `src/britannica/cleaners/page_artifacts.py`
- `src/britannica/parsers/{page_parser,section_parser,title_parser}.py`  (keep `img_float.py` — live)
- `src/britannica/db/models/{review_issue,source,source_file}.py`  (not in models `__all__`)
- `src/britannica/export/{search_docs,static_site_payloads}.py`

≈ **44 files.**

## B. Dead modules — real code, no live caller  · PURE-DELETE

| File | What | Evidence | Conf |
|---|---|---|---|
| `pipeline/stages/elements/_figure.py` (466 ln) | the removed structural figure-span recognizer | refs: itself + the also-dead `tools/diagnostics/figure_span_audit.py`; walker docstrings say "the figure recognizer was removed" | high |
| `pipeline/stages/elements/_text.py` — `_strip_br` | `<br>`→space mauler | imported in `_tables.py`, never called; module dead | high |
| `pipeline/stages/fold_unfold.py` (263 ln) | unfold `<br>`-stacked rows | only a "now-retired" comment in `source_cleanup.py` + a test | high |
| `pipeline/stages/transform_articles/djvu_refs.py` | djvu page-ref rewrite | superseded; live djvu lives in `elements/`; the transform_articles import is a dead re-export | high |
| `cleaners/reflow.py` — `reflow_paragraphs` | marker-stream reflow sweep | no src caller; only a test | high |
| `cleaners/whitespace.py` — `normalize_whitespace` | whitespace collapse | no caller | high |
| `cleaners/headers_footers.py` — `strip_headers` | strip page-header line | no references at all | high |
| `util/roman.py` — `roman_to_int` | roman→int | no caller; pipeline roman lives in `_ordered_list.py` + `sections.py` | high |
| `xrefs/llm_excerpt.py` — `clean_excerpt` | LLM excerpt cleaner | no caller; sole importer of the dead `markers.IMG_RE` | high |
| `db/models/editorial_action.py` — `EditorialAction` | orphan table model | not in models `__all__`; never imported, table never created | high |

**10 files.**

## C. Dead code inside live modules  · SURGICAL

- `elements/_leaf.py` — `_format_structural_formula`, `_is_structural_formula` (+ their dead imports in `_tables.py` and `elements/__init__.py`).
- `elements/_section.py` — `section_name` (staged for an unlanded step; no caller; the two producers in the file are live).
- `elements/_image.py:12` + `elements/__init__.py:19` — dead `_img_float_parser` imports (the real parse re-imports locally).
- `elements/_outline.py` — the `require_emphasis=False` branch + param (its only caller, the deleted plate-outline detector, is gone).
- `markers.py` — the named delimiter constants (`IMG_OPEN/CLOSE`, `FN_*`, `TABLE_*`, `VERSE_*`, `LEGEND_*`, `LN_*`, `MATH_*`, `SEC_*`, `BOLD_*`, `ITALIC_*`, `SMALLCAPS_*`, `SHOULDER_*`), all `_INTERNAL_*`, `TABLE_CELL_RE`/`parse_table_cell`, and `IMG_RE` — all dead (the viewer holds its own JS copy of the cell grammar). **Keep** the live helpers (`markers_to_text`, `strip_*_markers`, `PAGE_MARKER_*`, `IMG_PARTS_RE`, `parse_img_meta`, …).
- `source_cleanup.py` — `strip_section_tags` (+ `_SECTION_TAG_RE`), `normalize_line_endings` (section-tag drop lives in `super_detect`/`super_walker`).
- `detect_boundaries.py:499-504` — the "Legacy per-page detect_boundaries" tombstone comment (function already gone).

## D. Duplicate spine-step implementations  · FIX-FIRST → collapse to one

1. **Step 1/2 runs 2–3× per volume.** `super_detect.detect_boundaries(volume)` triggers `_split_out_plates` at `super_detect.py:52`, again inside `volume_stream` (`super_walker.py:215`, called at `super_detect.py:59`), and again when `super_walk` re-calls `volume_stream` internally; `preprocess(make_stream(...))` runs twice. **Fix:** compute `volume_stream(volume)` once and thread the prebuilt stream + plate-free pages into `super_walk`; `_split_out_plates` runs once.
2. **Second article walk.** `extract_contributors.py:255` re-walks every article (`walk_article`) only to harvest sign-offs, duplicating the canonical walk at `assemble.py:36` — and in production both run (Phase 2 extract-contributors, then Phase 4 assemble). **Fix:** harvest contributors off the single assemble walk (5e on the 5b walk). *Caveat:* requires reordering — extract-contributors currently writes `ArticleContributor` rows in its own Phase-2 stage, before the corpus is assembled.
3. **`process_elements_tree` indirection.** Its only caller is `process_elements`, which discards the returned tree via `[0]`; the promised "export reads the tree" consumer never existed. **Fix:** fold the body into `process_elements`, drop the dead `tree` plumbing.

## E. Shadow / scaffolding passes  · FIX-FIRST → then delete

- **`_CHROME_EMPTY_NAMES` drop-list** (`_classifier.py`) — neutralizes mis-routed front-matter / vol-29 / printed-TOC / `hws` content to EMPTY. It exists *only* because front matter rides into the walk (the step-1 violation). **Dies once step 1 excludes front matter** (manifest note below). Its non-front-matter entries (maintenance templates: ambox/suspect/…) need a separate look.
- **`_HWS_STANDALONE` / `_HWE_STANDALONE` regex sweep** (`preprocess.py`) — the sole handler of `{{hws|frag|WORD}}`/`{{hwe}}`, reconstructing the split word by regex over the stream. Word reconstruction is a content decision → a producer's job (the classifier already reserves the `hws`/`hwe` labels). **Fix:** make it a producer; delete the sweep + the `_CHROME_EMPTY_NAMES` hws/hwe entries.
- **`_allow_figure` flag threading** — vestigial since the figure recognizer was removed; gates nothing that still exists, yet threaded through `_walker.py`, `_classifier.py`, `__init__.py`, and every producer's `process_elements(..., _allow_figure=False)` call. **Fix:** remove the dead flag everywhere.
- **Stale module docstrings** (not code, but they lie): `_classifier.py` "dormant until Phase C … legacy three-pass pipeline" (the classifier *is* the live spine); `markers.py` "the fetcher creates markers … converts at end of cleaning" (that fetcher/cleaner is deleted). Rewrite or delete.

## F. tools/ — orphaned & superseded scripts

Reachability ground-truth = `rebuild_all.sh`. The spine invokes only `britannica detect-boundaries`, `extract-contributors`, `corpus-export` (Phases 2 & 4); the rest of rebuild is the separate-necessary builders (contributor table, printed-pages, math width/annotate, vol29 TOC, site pages, readers-guide, quality report, deploy).

**Spine-duplicate / one-off drivers · PURE-DELETE**
`tools/pipeline/run_volume.sh` (duplicates Phase 2) · `tools/pipeline/fetch_all.sh` (old fetch wrapper) [med] · `tools/test_lighthouse_tables.py` (one-off mock builder)

**Broken diagnostics — import already-deleted symbols, cannot run · PURE-DELETE**
`tools/diagnostics/`: `check_routed_textloss.py`, `check_table_figure_textloss.py` (import `_process_html_table`) · `figure_span_audit.py` (imports `_figure`/`_IMAGE_FLOAT_RE`; pairs with `_figure.py`) · `compare_detect_boundaries.py` (imports moved `detect_boundaries`) · `measure_wrap_loss.py` (imports gone `article_json` helpers)

**Orphaned one-off investigation audits — no caller · PURE-DELETE · med**
`tools/diagnostics/`: `audit_brace2.py`, `categorize_lc_titles.py`, `convert_osmania_sample.py`, `extract_all_scans.py`, `count_html_tag_files.py`, `find_html_tag_leaks_by_type.py`, `figure_caption_audit.py`, `find_poem_ref_collision.py`, `find_swallowed_author_links.py`, `image_metadata_survey.py`, `toc_ambiguity.py`, `wikilink_slice.py`, `preview_html_table_routing.py`, `shadow_export.py`

**vol20 scan-migration scaffolding — already executed · PURE-DELETE**
`tools/pipeline/probe_vol20_fm.py`, `tools/pipeline/swap_vol20_scans.py`

**Orphaned CLI / viewer assets**
`src/britannica/cli/main.py` — the `extract-contributor-bios` command (not in rebuild; bios harvested elsewhere) [FIX-FIRST: verify, then drop] · `tools/viewer/scans_osmania.html`, `tools/viewer/vol20_browse.html` (dead pages, not deployed/linked) · `tools/viewer/title_page_9.jpg`, `title_page_ia.jpg` (orphaned alt assets; live one is `title_page.jpg`) · `src/britannica/export/article_json.py:476` (stale comment → deleted `verify_refactor.py`)

**vol-29 separate-concern dead scripts — your call**
`tools/vol29/`: `vision_ocr_vol29.py`, `vision_ocr_contributors.py`, `vision_ocr_ancillary.py`, `parse_abbreviations.py` — one-off OCR/parse producers whose JSON outputs are live-consumed but whose scripts never re-run. They're the only record of *how* the OCR was made — keep as provenance or kill as darlings. · `cleanup_toc.py`, `detect_toc_artifacts.py` — orphaned cleanup passes that mutate `classified_toc.json` in place and are **not** wired into rebuild (a fresh rebuild won't reproduce their effect — a latent bug in its own right) · PURE-DELETE the scripts, flag the un-reproduced cleanup.

## G. Tests that ride along

Dead §B modules are kept green only by their unit tests — delete together: `test_fold_unfold.py`, `test_reflow.py`, `test_whitespace.py`, `test_roman.py` (+ trim structural-formula / figure-span cases). `test_transform_v2.py` / `test_transform_v2_realdata.py` name deleted symbols *in docstrings only* — bodies call the live `process_elements`; just rename.

---

## KEEP — necessary-separate (explicitly NOT wiped)

- **Spine + separate builders in rebuild:** detect-boundaries, extract-contributors, corpus-export; contributor table / vol29 linkers; printed-pages; math width/annotate; vol29 TOC parse/disambiguate; site pages; readers-guide; quality report; dedup gate; deploy.
- **Standing QA / regression net (no caller but prized):** `quality_report.py`, `leak_audit.py`, `snapshot_corpus.py`, `walker_snapshot.py`, `check_table_path_purity.py`, `check_quality_gate.py`, `xref_coverage_audit.py`, `verify_known_articles.py`, the label-distribution/snapshot family, `tools/qa/*`, `tools/render_article.py`.
- **Manual asset / dev / deploy:** `fetch/`, `import_wikisource_pages.py`, `download_images.py`, `download_djvu_crops.py`, `fetch_ia_scans.sh`, `rebuild_volume.py`, db helper scripts.
- **The live src spine:** everything the sweeps marked ON-PATH (walker/classifier/producers; preprocess/quote_runs/corrections/unicode; transform_articles; assemble/resolve_xrefs; export/; xrefs/; contributors/; db live models; parsers/img_float; util/strings; markers live helpers).

## The step-1 front-matter fix (recorded once)

Front matter rides into the walk because step 1 splits out *plates* but not *front matter*, and the per-volume **article leaf-range is recorded nowhere** (`grep first_article/page_range/VOLUMES` → nothing). The fix is not a recognizer to chase — it's a **per-volume manifest**: record, once, the leaf each volume's articles start and end on. Front matter = leaves outside that range; the step-1 partition reads the manifest. Then §E's `_CHROME_EMPTY_NAMES` front-matter entries and the front-matter walk die at the root. (Saved to memory as `article-range-manifest`.)

---

## Tally

| Bucket | Count | Disposition |
|---|---|---|
| Empty stub modules (§A) | ≈ 44 files | pure-delete |
| Dead modules (§B) | 10 files | pure-delete |
| Surgical dead defs/constants (§C) | ≈ 24 sites | surgical |
| Orphaned/superseded tools (§F) | ≈ 30 files | pure-delete (2 judgment calls) |
| Ride-along tests (§G) | 4 files | delete with §B |
| **Fix-first architectural collapses (§D–E)** | **5** | front-matter manifest · step-1 dedup · contributor double-walk · hws producer · `_allow_figure`/`process_elements_tree` |

The first five buckets are free deletions — ~90 files and ~24 in-file edits that change no behavior. The five FIX-FIRST items are the actual engineering, and they're where the spine gets *truer*, not just lighter.

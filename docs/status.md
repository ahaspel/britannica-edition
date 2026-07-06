# Britannica Edition — Status

**Last updated:** 2026-07-06.  Single source of truth for project state.  Snapshot
audit reports live in `docs/reports/`; long-form per-topic notes live in the
agent's memory directory and are not duplicated here.

> **THE CAMPAIGN (2026-06-01):** the recursive architecture works; the bugs are
> old scaffolding still running beside it.  The good path is written down in
> **[`docs/canonical_path.md`](canonical_path.md)** — the few steps that build an
> article/plate properly.  Everything outside it has to go (catch-all
> `_strip_templates`, 16 fake-recursion regexes, the legacy `parsers/plate/`).
> Measure: `strip_scan.py` / `fake_recursion_audit.py` → 0, then delete.

> **THE THREE PRINCIPLES (2026-06-03, the user's governing philosophy)** — one
> end-to-end losslessness chain; old junk is whatever breaks it:
> 1. **Recurse to the end** — decompose every structure to its leaves; never
>    flatten/body-text what should recurse.  Scoreboard: `fake_recursion_audit`→0;
>    "does the cell run `process_elements`, not `text_transform`?" (open frontier).
> 2. **Carry everything in the source** — carry-by-default, never drop source
>    styling/content.  Scoreboard: `strip_scan`/`ts_audit`→0 for the *visible* leaks —
>    but **silent drops** (a discarded slot, e.g. row-attrs pre-row-carry) are
>    invisible to those, so auditing carry also means "what slots does a producer throw away?"
> 3. **Render what we carry** — the viewer renders mechanically every marker / carried
>    `style=`; carrying into a void (e.g. raw HTML on an `escapeHtml` path) is a bug.
>    VERIFY rendering before claiming a carry-win.
>
> **`_strip_templates` is the canonical DOUBLE violator (1 **and** 2):** it flattens
> (strips a template without descending into the shape it wraps) AND drops (the
> content is gone).  So every catch-all leak is a 1+2 violation, and draining a family
> is a two-for-one — the highest-leverage hunt.  Handled-but-drops (the `«CTR»`-only
> `<p>`/`<div>` handlers that lose font-size) violate 2 ONLY (the handler already
> recurses) — the carry cleanup tail.  See [[feedback_three_principles]].
>
> **DIAGNOSTIC (user): virtually every bug traces to a violation of one or more of
> these three.**  Debugging = name the principle the bug breaks, restore it.  Bug-
> classification, not philosophy.

---

> **History:** the completed-arc progress logs (2026-06-09 back to 2026-05-17), the
> old `NEXT ARCS`, the 2026-05-17 rebuild record, and the pre-campaign `Queued` /
> `Known issues` lists (which reference now-deleted labels — `LAYOUT_WRAPPER`,
> `CAPTIONED_FIGURE_INLINE`, `LEGENDED_FIGURE*`, the six table labels) have moved to
> [`docs/status_history.md`](status_history.md).  This file keeps only the current state
> and the durable reference.

---

## CURRENT STATE (2026-07-06)

The recursive architecture is in place corpus-wide; this session closed out the
remaining scaffolding (the catch-all preprocess stage, the title double-decider, the
viewer's layout-guessing) and drained several whole leak classes.  **Three principles**
above still govern; every change below is one of *recurse to the end* / *carry the
source* / *render what we carry*.

### Session 2026-07-06 — SHIPPED to production · distribution products live · contributors closed

**Full rebuild + deploy (66 min, exit 0) — first production deploy since 2026-05-17.**
One consistent `--skip-import` re-export ships the entire recursive-architecture campaign,
the LINK ARC, the banked MATH `display` / `«BR»` producer work, the vol-29 classified-TOC
rebuild, and this session's spacer / table-cell / shoulder-heading producers.  Phase 9
preflight clean (all hard refs reachable); search re-indexed across 37,226 articles.
**Rule banked ([[feedback_never_partial_rebuild]]):** never a partial rebuild/deploy — I
nearly pushed a viewer-only deploy against a stale corpus and the user stopped it; the
full rebuild also removes the "where did my change land?" tracking burden entirely.
Corollary banked ([[feedback_tune_dont_fork]]): a shared job = one owning function tuned
with a parameter, never two divergent copies.

**Distribution products (the HN asks: download · API · EPUB) — core audience = agent-feeders.**
Shipped the **free download**: `articles.jsonl` (Markdown records) + `xref_edges.jsonl` +
`topics.json` + `contributors.json`.  The three knowledge graphs are the moat —
reconstructed from the edition + vol-29 index, not extractable from Wikisource.  Live at
`s3://britannica11.org/download/eb1911-corpus.tar.gz` (self-describing: manifest +
checksums + schema + validation) **and on Hugging Face**
(huggingface.co/datasets/britannica11/eb1911, CC-BY-SA 4.0).  New: `body_to_markdown`
(`export/markdown.py`, marker→Markdown sibling of `markers_to_text`), `export/download.py`
(assembler), Phase 6h, `tools/publish_hf.py`.  Download page generated from
`docs/download.txt` → `build_download_page.py` (about.txt pattern).  Model: **free data,
paid EPUB + API** (both in preparation; commerce layer still to build).  See the
Distribution section below.

**Contributors closed — 41 → 0.**  The "41 authorless contributors" were index-attributable
all along: phase 3b2 (vol-29 article linker, which runs *after* the 3b front-matter
fallback) mops up exactly the residue.  Confirmed at the artifact level — both
`articles/contributors.json` and `download/contributors.json` carry all **1507**.  The
investigation surfaced the real residue: three initials-matchers doing one job with
divergent normalizers (`_normalize_initials` rich · `_ws_normalize_initials` whitespace-
only · raw `.strip()`); the roster is *stored* folded, so the weaker two can only miss.
Two stragglers left (`W. AY.` Wilfrid Airy, `T. G. BR.`).  Fix = collapse to the one
normalizer; queued with the div-gate batch (below).

### Session 2026-06-14 — figures render block · MATH display carry · dead-relic deletion

**Centred figures, not inline glyphs.**  `_styled_br_to_marker` rewrites a wrapper's
top-level `<br>`→`«BR»` *before* the inner walk, so `_is_inline_image_position` (which knew
only the literal `<br>` line-ender) read the `«BR»` as same-line prose and mis-stamped
centred figures `align=inline`.  The check now treats `«BR»` as a line break like
`\n`/`<br>`: **109 captioned figures across 40 articles flip inline→block** (HYDRAULICS
Figs 209/210, BOILER, BREAKWATER, CATACOMB, …).  Routing them to the block producer also
drops a redundant File `|alt` arg they kept as a caption ([[feedback_no_caption_concept]];
no content loss).  5 transform snapshots rebaselined.

**MATH carries `display`.**  `_process_math` reads block-vs-inline off the source
(`<math display="block">` or a `\begin{…}` environment) into `«MATH[display]:…»`, so the
viewer renders `displayMode` mechanically — exactly like an image's carried `align`.
Producer wired (`_leaf.py`/`__init__.py`/`annotate_math_markers.py`); viewer half (read the
token, drop `mathOnly`/`skipMath`) pending — needs a rebuild.

**Dead body-producer-unwrap relic deleted.**  `_wrap_body_runs` (+ `_find_atomic_wrapper_spans`,
`_LAYOUT_WRAPPER_NAMES`, `_HTML_WRAPPER_TAGS`, ~165 lines) is the corpse of the old design
where layout wrappers were kept atomic in body runs for the *body producer* to unwrap.
`walk()` now extracts `{{nowrap|…}}`/`{{center|…}}` as whole `DOUBLE_BRACE` elements routed
to the sole-owner style registry, so the chain had no caller; the body producer does ONLY
`\n\n`→«P», exactly as it must ([[feedback_producer_template]]).  Byte-identical (dead code).
The `\Big` math-typography leak was diagnosed a raw-source muff (3 fragments, HYDRAULICS —
`\sqrt` with a sizing delimiter as radicand; 280 corpus `\sqrt` uses, only these 3 break),
not a producer gap.  **Suite 378 green** throughout.

### Producer / preprocess / title / viewer sweep (2026-06-12 → 2026-06-13)

**Walker · elements · producers (recursive-architecture closeout).**
- **Walker/shape consolidation** — type-shapes collapsed into *structural* shapes; the
  classifier now routes purely by name (`_shapes.py`/`_walker.py`/`_classifier.py`).
- **Body text is a first-class element** — producers *consume-and-recurse* their own
  content through the one dispatch; the article body is no longer a special flat path.
- **False-leaf producers recurse** — the producers that still read their content flat
  now recurse to the ground; the speculative `dual-line` split was collapsed (it was
  specificity with no real occupants — [[feedback_leaks_are_core_recursion_bugs]]).

**Tables.**  Cut over to the recursive fold and **deleted the sub-classification slum**;
the table leaf now recurses to the ground and folds cell/row attrs *at the emit*
(`fold_cell_styles` absorbed the last three things `_cell_styles` knew; the tangle is
gone).  Borderless figures **un-mint** — a figure-table emits a class-less `<table>`,
not `class="figtable"` (20 transform snapshots rebaselined; trailing whitespace healed
before newlines).

**Plates.**  Detect on the walk's own heading recognizer; the **legacy per-page plate
parser is deleted** (one heading recognizer, validated against the prior splitter).

**Preprocess — the catch-all stage folded away.**  `prepare_wikitext` is **deleted**:
typo corrections + quote-run conversion folded into the source-clean; the **ref-follow
sweeper** and the nop / page-heading strips dropped; presentational HTML entities decoded
to their Unicode char in source-clean (`&nbsp;`/`&mdash;`/`&alpha;`…, no content
decision); `<ins>` proofreading insertions unwrapped (the `<del>` mirror); the malformed
`<noinclude">` opener tolerated; `<bdo>` direction + script-wrapper size params carried;
genealogy charts (`chart2`/`familytree`/`tree-chart`) recognized as an **image in the
walk**, not reshaped in preprocess.

**Title — one decider.**  `produce_title` is now the **sole** title authority: the joint
is stripped on the raw, the field decoded from the `«TITLE»` marker; `_is_title`
classifies caps-prose directly (`clean_title`/`normalize_title` retired); letter-article
drop-caps are carved into `«TITLE»` so every non-plate title is produced uniformly (all
26 letters × 8 markup forms verified).  The dead `title_display` / `title_raw` columns
and all their plumbing are deleted — the walked `«TITLE»` node is the single carrier.

**Hiero.**  All **298 leaked glyph blocks** now render.

**Viewer (stop reconstructing what the producer carries).**  Images render by their
**carried `align` / `width`**, not a block-layout guess — `{{IMG:…}}` is out of the
block-marker scan, so inline letterform glyphs stay in the prose flow (ALPHABET's
β/λ/σ); the `imgIsWide`/`.wide` heuristic is dropped (we carry `width=N`); a title's
footnote-ref scales to the heading font.

**Quality / tests.**  4 stale quality checkers fixed; unit tests no longer reference the
obsolete `figtable` class; **suite 378 green**.

**Rebuild tooling.**  `--skip-import` (the raw wikileaves never change → reuse the static
`source_pages`, ~30 min saved per rebuild; FK-safe truncate, boundaries+contributors
still re-derive) and Phase-4 progress ticks (corpus-export was a silent ~25-min hole).

### The LINK ARC (2026-06-09) — recap

Every raw link/ref surviving into output became a recognized element resolved to a
marker.  Generic `[[X]]` → `«LN»` via a 3-rung ladder (internal EB11 → WS-verified `«XL»`
→ strip); contributor / `{{section}}` / `#frag` / shortcut classes → 0.  **BROKEN leak
backlog 6,118 → 1,589** at 06-09; the 06-12/13 preprocess sweep (entities, `<ins>`/
`<del>`, genealogy, hiero, …) drove it the rest of the way down to **149** (re-audited
06-13 — see *Leak audit* below).  The xref panel = the article's *resolved internal*
links only.
New markers `«ANCHOR:slug»` and `«XL:url|display»` were added with **viewer decode
deferred to the render phase** — verify they're registered in `viewer.html` before the
next deploy.  Full notes in `status_history.md`.  [[project_wikilink_backlog]]
[[project_xref_panel]]

### Build & deploy state

- **Suite:** 378 green (last run 2026-06-13).
- **Last *deployed* rebuild: 2026-07-06** — full `--skip-import` rebuild + deploy, 66 min,
  exit 0, preflight clean.  **The campaign is now in production**, shipped as one consistent
  re-export: recursive architecture + LINK ARC + MATH/`«BR»` producer work + vol-29
  classified-TOC + the 2026-07-06 spacer/table-cell/shoulder-heading producers + the
  download bundle.  (Prior deployed rebuild: 2026-05-17.)
- **Working tree:** clean — all banked.  The 2026-06-14 producer work and the readers-guide
  regeneration that were "awaiting a rebuild to land" have landed.

### Leak audit (re-audited 2026-06-14, `tools/diagnostics/leak_audit.py`, full corpus)

**BROKEN: 149 in 48 articles (0% of corpus)** — down from 1,589 at 06-09; the old
per-class census is **superseded**.  Reading the actual output around each leak, the
producer is **essentially done** — the 149 decompose as:

- **~100 OCR / source junk** — `<word`/`<letter` scannos (Pliny inscription `<consul`,
  `<praetor`, `<secundus`), un-transcribed math `<`, mojibake.  Not pipeline bugs.
- **audit masking false-positives** — `htmltag:math` / `htmltag:poem` are *conjured by the
  audit's own* `_mask_final_form` fusing fragments across a masked marker; the real output
  is clean (verified: 0 `<math>`, 263 `«MATH»` in a flagged article).  The audit
  over-reports here — **hardening `_mask_*` is owed** so the "is the producer done?" check
  is trustworthy (a noisy audit corrupts the very check, [[feedback_kill_all_darlings]]).
- **recognized constructs failing on malformed source** — `{{nowrap}}` (79/84 in the worst
  article render fine; the leaks are unclosed `}}`), `{{fine block}}` (recognized in the
  style registry; nested-source), `<includeonly>` (recognized + unwrapped at
  `__init__.py:809`; the leak is an overlapping `{{fine print/s}}…/e}}` span straddling the
  tag).  OCR/transcription noise — **not producer gaps** (corrects the 06-13 list, which
  wrongly flagged these three for closing).

The **one genuine unrecognized construct is `<chem>`** (2 corpus-wide — e.g. art 5939264, a
well-formed `<chem>K4Fe(NC)6->…</chem>`): absent from `_OPAQUE_TAGS`/`_ELEMENT_TAGS`.  The
fix is **viewer-coupled** — route to `«MATH:\ce{…}»`, which renders only if KaTeX has the
mhchem extension — so it rides with the MATH viewer work, not the producer.  Everything
else is faithful rendering of broken source.  [[feedback_dont_flag_honesty]]
[[project_leak_audit_reframe]]

### Open frontier / next

**Active queue (2026-07-06), in order:**
- **nowrap/`{{left}}` + `html_tag` div gate** — contained producer/classifier recognition
  gap: `{{nowrap}}`/`{{left}}` cell templates and span/div `html_tag` leaks.  Fix the
  recognition gate upstream; changes export → rides a rebuild.  **Batch the contributor
  normalizer collapse into this** (one canonical `_normalize_initials`; delete
  `_ws_normalize_initials` + the raw-`.strip()` front-matter lookup; recovers the `W. AY.`/
  `T. G. BR.` stragglers — [[feedback_tune_dont_fork]]).
- **The `\n\n` viewer restructuring** — the invasive one (touches every article's render):
  the viewer splits body on `\n\n` then re-merges with two heuristics (continuation-merge at
  ~2958 = the viewer fixing an OCR *source error*, a flagged no-no; SH-absorb at ~2976).
  Root = producer paragraph-delimiting; the cure is producer-owned `«P»` boundaries + a
  mechanical viewer split, *deleting* the heuristics.  **Trace why the producer emits those
  `\n\n` seams before deleting anything**; treat with the snapshot/audit net (protect the
  ~36k working mass).  See [[feedback_viewer_mechanical]], [[feedback_viewer_not_source_errors]].

**Standing frontier (pre-2026-07-06 campaign):**
- **THE VIEWER campaign — make it mechanical; "get out of the way and let the markup
  do its job" (user).**  Plan: [`docs/plan_viewer_mechanical.md`](plan_viewer_mechanical.md).
  **WS1 (headings/sections/TOC) ✅ DONE 2026-06-14** — recognition moved to
  `preprocess_article`'s `stamp_sections` (`«SEC»` anchors riding the walk); the dual
  `SC_RE` slum deleted (viewer −8 KB); orphaned minor `{{section}}` anchors dropped;
  UNITED STATES TOC restored (verified).  **Remaining (viewer-side):** WS2 collapse the
  per-context decoders (`decodeInlineMarkers`/`formatCell`/`applySizeMarkers`/
  `renderTitleMarkers`) into one — the "renders here but not there" class; WS4 delete the
  dead `{{TABLE}}` decoder (`parseTableCell`/`tableCellHtml`/`scaleDisplayMath` — 0 in
  fresh output, ride the rebuild); WS3 block-marker re-split; WS5 CSS audit.
  See [[feedback_viewer_mechanical]], [[feedback_viewer_no_regex]].
- **MATH display half + `<chem>`** (rides the viewer campaign): render `displayMode` from the
  carried `«MATH[display]:…»` token and drop the `mathOnly`/`skipMath` guesses; recognize
  `<chem>` → `«MATH:\ce{…}»` once KaTeX has the mhchem extension (the one genuine producer
  gap, deferred here because it's viewer-coupled).  Both need a rebuild.
- **Harden `leak_audit._mask_final_form`** — it conjures `htmltag:math`/`htmltag:poem`
  phantoms by fusing fragments across masked markers; fix so the BROKEN headline is
  trustworthy (the audit is the "is the producer done?" instrument).
- **Re-triage the old "Known issues" list (now in `status_history.md`) — mostly stale,
  must be confirmed.**  It predates the recursive-architecture campaign and references
  now-deleted labels/producers (`LAYOUT_WRAPPER`, `CAPTIONED_FIGURE_INLINE`,
  `LEGENDED_FIGURE*`, the six table labels), so most entries are likely already fixed by
  the figure/table collapse.  **Treat none of it as live until re-confirmed** against the
  current build; keep only what still reproduces.
- **Viewer registration for `«XL»` / `«ANCHOR»`** (deferred from the LINK ARC) before any
  deploy.
- **Fresh full rebuild + deploy** — ✅ **DONE 2026-07-06** (see Session 2026-07-06 /
  Build & deploy state).
- **Resolve the readers-guide regeneration** — ✅ shipped in the 2026-07-06 rebuild.
- A few pre-campaign infra items still worth re-triage (now in `status_history.md`):
  viewer-deploy `aws s3 sync` instead of per-file enumeration, shared viewer page shell,
  genuinely-fast `rebuild_volume`.

---

## Overview

A scholarly digital edition of the 1911 *Encyclopædia Britannica* — the first
hyperlinked, searchable, fully annotated edition with proper rendering of Greek,
Hebrew, hieroglyphics, mathematical notation, chemical formulas, footnotes,
images, verse quotations, and contributor attribution.  Live at
**britannica11.org**.

---

## Architecture

### Boundary detection

Article boundaries are determined by `<section>` tags in the Wikisource
wikitext — not heuristic heading detection.  Plate pages are split off first
in a stateless PASS 1 (`_split_out_plates`), then the article state machine
runs over the plate-free pages in PASS 2.

### Element pipeline

Walk → classify → produce, recursively, per article (`pipeline/stages/elements/`,
entry `process_elements`).  The old `transform_articles/_transform_text_v2` shim and
the catch-all body-text passes (`_strip_templates`, strip-HTML) are **deleted**; source
cleanup (corrections + quote-runs + entity decode + `<ins>`/`<del>` unwrap, no content
decisions) lives in `source_cleanup.py`.

1. The **walker** bounds every bracket construct by one balanced rule on near-raw source
   (`{{}}`, `{|…|}`, `[[]]`, `<x>…</x>`) — it knows only bracket syntax, never "table"/
   "ref"/"figure".
2. The **classifier** assigns one structural label by name (TABLE, IMAGE/ICL, MATH, CHEM,
   POEM, TITLE, body text, …); body text is a first-class element.
3. Each label's **producer** transforms its own outer wrapper and *recurses* its inner
   content through the same dispatch — figures/tables/cells decompose to their leaves
   (the image leaf, the prose leaf); no producer reads its content flat.
4. Reassembly with `\x01PAGE:N\x01` markers; the viewer decodes markers mechanically.

### Marker formats (internal)

| Marker | Meaning |
|---|---|
| `«B» / «I» / «SC»` | Bold / italic / small caps |
| `«LN:filename\|target\|display«/LN»` | Resolved link |
| `«LN:target\|display«/LN»` | Unresolved link (falls back to search) |
| `«MATH:…«/MATH»` | LaTeX, plain |
| `«MATH[fs=N]:…«/MATH»` | LaTeX, render at N% font-size |
| `«MATH[display]:…«/MATH»` | LaTeX, block display mode (carried from source `<math display="block">` / `\begin{…}`) |
| `«MATH[popout]:…«/MATH»` | LaTeX, render click-to-pop-out link |
| `«FN:…«/FN»` | Footnote |
| `«HTMLTABLE:…«/HTMLTABLE»` | Complex table preserved as HTML |
| `«CHEM:…«/CHEM»` | Chemistry valence-bracket grid |
| `«PRE:…«/PRE»` | Preformatted block |
| `«SH»…«/SH»` | Shoulder heading |
| `{{TABLE:…}TABLE}` | Wiki-table block |
| `{{VERSE:…}VERSE}` | Verse block |
| `{{LEGEND:…}LEGEND}` | Figure-legend block |
| `{{IMG:filename\|caption}}` | Image with caption |

### Cross-reference resolution

Multi-strategy resolver: exact title, alias table, plural/singular, name
inversion, trailing article/period, qualified prefix.  Resolved targets are
rewritten as direct links at export time so the viewer routes to
`/article/{page}/{slug}` instead of search.

### Stack

Python 3.12, SQLAlchemy, Typer, Postgres, Meilisearch, KaTeX, Playwright (for
math measurement).  pytest (378 tests).

---

## Pipeline phases (`tools/rebuild_all.sh`)

1. Truncate DB, clear exports.
1b. Build contributor table.
1c. Apply vol 29 contributor linker.
2. Per-volume: import → clean → detect boundaries → transform → classify →
   extract xrefs → resolve xrefs (intra-vol) → extract images → extract
   contributors → export.
3a. Resolve xrefs across all volumes.
3b. Link contributors from front matter.
3b2. Link vol 29 article attributions.
3c. Rebuild printed-page mapping.
4. Re-export (with cross-vol xrefs resolved).
**4b. Measure math widths (refresh scale-hint cache).**
**4c. Annotate math markers from refreshed cache.**
5. Export front matter.
6b. Parse classified TOC; 6b2. apply cached disambiguations; 6c. detect fm
   first-content pages; 6d. rebuild generated site pages (incl. about/download
   from `docs/*.txt`); 6e. build Reader's Guide; 6h. build the download bundle
   (JSONL + 3 graphs).
7. Deploy (S3 sync articles + images + scans + JSON + viewer + download bundle;
   CloudFront invalidate; index search on EC2).
8. Quality report.
9. Deploy preflight (check_deploy_refs.py).

---

## Scripts

- `tools/rebuild_all.sh` — full corpus rebuild + deploy (`--no-deploy` for
  local-only).  ~2 hours.
- `tools/pipeline/rebuild_volume.py <vol> <TITLE>` — rebuild a volume
  targeted at one article.  Fast (in-process) by default; `--full`
  wipes source + re-imports + runs all stages; `--deploy` uploads
  the article JSON to S3.
- `tools/render_article.py <TITLE>` — re-render one article from existing DB
  state (~3 s).  Fastest iteration loop.
- `tools/diagnostics/quality_report.py` — body-wide metrics (run before every
  deploy).
- `tools/diagnostics/measure_math_widths.py` — refresh math-width cache.
- `tools/pipeline/annotate_math_markers.py` — re-annotate exported MATH
  markers from refreshed cache.
- `tools/deploy_html.sh` — upload viewer HTML + invalidate CloudFront.
- `tools/pipeline/start_services.sh` — start/stop local Postgres, Meilisearch,
  web server.

---

## Data model

`Article` (title, volume, page range, body, article_type, section_name) ·
`ArticleSegment` (text ↔ source page) · `CrossReference` · `ArticleImage` ·
`Contributor` · `ArticleContributor`.  Stable IDs: `{vol:02d}-{page:04d}-{slug}`.

---

## Viewer

- `home.html` — title-page landing.
- `index.html` — volume tabs, title / full-text / contributor search,
  alphabetic navigation.
- `viewer.html` — articles with volume:page citations, shoulder headings,
  images, footnotes, tables (inline + complex), TOC, in-article search,
  KaTeX math (with fs= scaling + popout modal for wide expressions),
  bold/italic/small-caps/hieroglyph rendering, direct cross-reference
  links.
- `search.html` — Meilisearch full-text, exact-substring filter, dedup,
  match-count sort, per-occurrence links to `viewer.html?…&match=N`.
- `contributors.html`, `preface.html`, `topics.html`, `ancillary*.html`,
  `readers-guide*.html`.

---

## Production

- **britannica11.org** — single S3 bucket + CloudFront (dist
  `E24BJKH0IB4I6`).  CloudFront function `article-rewrite` maps
  `/article/{page}/{slug}` → `viewer.html`; `strip-search-prefix` proxies
  `/search-api/*` to Meilisearch on EC2.
- **Meilisearch** — Docker on EC2 `t3.small`
  (`ec2-44-222-119-72.compute-1.amazonaws.com`), port 7700.
- **Raw wikitext** backed up to `s3://britannica11.org/raw/` (28 zips, 139 MB).
- **IA page scans** — 29 volumes (~30 GB), `data/raw/ia_scans/`.

---

## Distribution (download · API · EPUB)

Three deliverables from the HN launch; core audience = agent-feeders.  Model: **free data,
paid book + interface.**

- **Download (free, LIVE 2026-07-06).**  `s3://britannica11.org/download/eb1911-corpus.tar.gz`
  and **huggingface.co/datasets/britannica11/eb1911** (CC-BY-SA 4.0, matching Wikisource).
  Contents: `articles.jsonl` (one record/article — Markdown text + metadata + sections +
  denormalized categories/xrefs/contributors), `xref_edges.jsonl` (cross-reference graph),
  `topics.json` (vol-29 subject taxonomy), `contributors.json` (authorship roster), plus
  `manifest.json` (counts + SHA-256), `schema.json`, `LICENSE`, `README.md`.  **The three
  graphs are the moat** — reconstructed from the edition + printed vol-29 index + contributor
  tables, not extractable from Wikisource.  Images carried as *references* (`file`), not
  binaries, to stay light for text pipelines.  Built by `src/britannica/export/download.py`
  (+ `body_to_markdown` in `export/markdown.py`), rebuild **Phase 6h**, uploaded in Phase 7;
  published to HF by `tools/publish_hf.py`.  Page authored in `docs/download.txt` →
  `tools/viewer/build_download_page.py` → `download.html` (the `about.txt` pattern).
  Manifest counts (2026-07-06): 37,226 articles · 32,730 xref edges · 519 topic nodes ·
  1,507 contributors.
- **EPUB (paid, in prep).**  The whole encyclopedia as a single e-book; reuses the marker
  decoder against an HTML target, topic index as its TOC.  Pricing plan: ~$20 direct /
  ~$55 on Amazon (KDP 35% royalty tier above $9.99; Amazon = discovery channel, direct =
  margin channel).
- **API (paid, in prep).**  Full-text search + article retrieval + traversal of the three
  graphs.
- **Commerce layer** (checkout for the EPUB, API keys + metering + billing) — still to build.

---

## Topics page (Vol 29 classified TOC)

The "Classified List of Articles" (vol 29) as a browsable topic index --
`data/derived/classified_toc.json`, rendered by `topics.html`.  **The index needs both
ORDER and STRUCTURE, and no single read has both:** the whole-page OCR keeps the
full-width band banners and gutter-spanning notes whole but scrambles its columns; the
half-page OCR keeps the columns (so the buckets and links) in reading order but shears
the banners at the gutter.  Each is sourced from the read that holds it, and merged:

    read tree = whole bands + their notes  +  halves' ordered buckets + links + notes
    merge     = graft the read tree onto the printed index (parse_index), by name
    resolve   = resolve the links already on the tree, in place

**Four pieces, nothing else load-bearing:**

1. **Whole read** -- `band_structure` reads the 40 bands off the `spread` field (24
   majors + `GEO_BANDS` 11 + `HIST_BANDS` 5; only Geo/History carry sub-bands).
   `whole_tracks` reads `vol29_whole_{ws}.txt` for the header track that marks the
   halves, and returns the band-notes whole (the halves shear them at the gutter).
2. **Half read** -- `assemble_sequence` marks the bands onto each half (`_mark_bands`
   aligns every column to the whole read's header track; `band_check` = 0 violations)
   and reads the buckets in reading order; `build_sections` recognizes each bucket and
   its links + column notes.
3. **Merge** -- `complete_index.stitch` builds the read tree off the halves (bands
   carrying their band-notes; ordered buckets carrying links + column notes); `merge`
   grafts it onto the printed-index trunk by NAME -- a bucket that matches a trunk node
   seats on it, one the index omitted grafts under its band (bare leaves like Lakes
   under Physical features, kept on their parent by `grp_region`).  Every node is one
   shape `{name, notes, articles, children}` -- no filled/marking flags, no
   pointer/xref kinds.  A bare banner the index disambiguates by position is renamed
   (`_BAND_WALL`: the UK's bare `PHYSICAL FEATURES` -> `United Kingdom ...: Physical
   Features`); a read/index spelling gap goes in `_NAME_VARIANTS` (`...Syriac
   Literature` -> the index's `Hebrew, Armenian and Syriac`).
4. **Link resolution** -- `populate.build_resolver` + `resolve_tree` resolve each seated
   link to its article file (a coarse cascade, ~5% unresolved).  Cached ambiguity
   disambiguations applied at rebuild (pipeline 6b2, `disambiguate_toc.py`).

`populate.main` is the sole writer of `classified_toc.json`: load the completed index
tree (`complete_index.index_tree`), resolve its links in place, dedup per leaf, write.
**There is no pour** -- the read tree carries the links through the merge, so nothing is
seated positionally.

**State (2026-07-04): DONE.**  24 categories, **36,395 articles / 95% resolved**.  Built
from the two-read model above, replacing the old index-count + positional-pour scheme;
the pour, the filled/unfilled marking, and the `_whole_content` single-read chain were
deleted (net ~570 fewer lines).  Output reproducible (stable sort tiebreak).  Small
known residue, both parked: two band-level sibling-vs-child grafts (`Belgium` under
`Balkan Peninsula`, `Malay Peninsula` under `India`); link resolution is coarse.

---

## File / directory conventions

- `tools/_scratch/` — disposable.  Promote keepers to `tools/diagnostics/`
  with a real name and docstring.
- `data/corrections.json` — source-text typos by `vol:page`; never edit raw
  wikisource page JSONs directly.
- `docs/reports/` — dated snapshot audit reports.
- `docs/status.md` — this file.  Source of truth for current state.

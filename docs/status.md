# Britannica Edition — Status

**Last updated:** 2026-05-25.  Single source of truth for project state.  Snapshot
audit reports live in `docs/reports/`; long-form per-topic notes live in the
agent's memory directory and are not duplicated here.

---

## Current focus (2026-05-25) — Honesty campaign: super-walker WIRED + producers on RAW (Stages 1–2 landed; per-family producer queue open)

**Goal:** every transform from corrected-raw happens inside a producer.  The
walker walks raw and hands raw to the classifier; the classifier decides the
label (it may consult a transformed copy, but emits nothing); the producer
receives RAW and does all transformation.  Result: the transformation surface is
100% producer-owned, and every residual bug sorts into a clean, data-safe tier —
**producer** (wrong render of correct raw), **classifier** (wrong label, e.g.
LAYOUT_WRAPPER leaks), or **walker** (wrong boundary).  Raw always arrives intact,
so a bug can only mis-route, never destroy.  See [[transform-only-two-places]],
[[walker-on-raw-source]], [[turn-bugs-into-producer-bugs]],
[[layout-wrapper-definition]].

### Super-walker runs on RAW — pre-walker chew DELETED (this session)
`super_walker.volume_stream` no longer calls `_preprocess_wikitext`; it joins raw
pages.  Page chrome (`<noinclude>`, `<section …>`) is RECOGNIZED and skipped in
`_LEAD` (carry-raw), not stripped.  Of the 3 chew transforms: line-endings was a
no-op (**0 CR in 28,706 pages**), `<section end>` strip contributed **0
boundaries**, and noinclude (**+31 detections**) is fully replaced by the `_LEAD`
recognizer.  **raw == chewed: 36,689 = 36,689 boundaries, 0 volume diffs**; all 31
noinclude-adjacent articles recovered (incl. STRAFFORD, THOMAS WENTWORTH).

Two real boundary MISSES the raw walker exposed, both fixed (recognizer gaps):
- **STAWELL, SIR WILLIAM FOSTER** — `[[Author:…|` + newline before `«B»`; added
  `\s*` to `_HEADING` / `_BOLD` / the super_detect anchor pattern.
- **HOLLAND, JOSIAH GILBERT** — `{{sc}}` title-case headword rejected by the
  title-case guard; `clean_title` now uppercases `{{sc}}` content.

**rawvsview** (raw-fed vs view-fed classification) = **98.6% identical** corpus-
wide (4438/4500 on figure/table-heavy vols); the ~1.4% residual is entirely the
image/figure family (inline `[[File:|Npx]]`, the css_crop cluster, figure-vs-
image) — i.e. the predicates that must reach for a utility = the Stage-2 worklist.

### Stage 0 — baseline captured (the regression net)
`tools/diagnostics/label_distribution_snapshot.py before` →
`tools/_scratch/label_distribution.before.json` (**51,155 classified elements,
37,219 articles**).  Producer net pre-exists: per-seed snapshots +
`tests/regression/test_transform_snapshots.py`.

### Stage 1 — boundaries WIRED  ← THIS CHECKPOINT (NOT yet rebuilt/deployed)
`detect_boundaries` → `super_detect_boundaries` at `cli/main.py:114`.  Changes:
- NEW **`src/britannica/pipeline/stages/super_detect.py`** — clean
  `super_detect_boundaries(volume)`: boundaries from `super_walk`, RAW article
  slices, title via `produce_title`, per-page segments from `«PAGE»` markers.
- **`elements/_title.py`** — `produce_title` now returns `(title, body,
  title_raw)`; unwraps `[[Author:…|…]]`/`[[Portal:…|…]]` in the returned span so
  the downstream `title_display` transform keeps the bold run.
- **`cli/main.py:114`** — the one-line swap.

VALIDATED: boundaries conserved (36,689, +23 wins); the `title_raw`→`title_display`
contract holds across vols 1/13/15/25 — the *only* divergence is super_detect
**preserving** a formatted display detect_boundaries dropped (HOLLAND, a win).
Wired function runs (vol 1 → 1716 articles).  Gated on the next clean rebuild +
corpus quality gate (`cli.main` full-import can't run in-env: missing
`mwparserfromhell`, pre-existing).

### Stage 2 — honesty hand-off  ← LANDED (flip in; per-family producer queue open)
**Producers now receive the RAW corrected body, zero pre-pass.**  In
`_transform_text_v2`, `original_raw` is captured before any pass and fed to
`process_elements` (`process_elements(original_raw, …)`); the whole Layer A is
**bypassed** (and being deleted per-family as each lands).  `produce_tree`
already forwards `ce.raw`, so producers get raw by construction.

**INVARIANT (unbendable):** corrected-raw → nothing → producer.  corrections.json
is the only thing that touches source (already baked into `page.wikitext`).  No
pre-pass, no relocated pre-pass, no "pure-noise" pre-pass.  A failing producer is
NOT fixed by re-adding a pass — it's fixed by the producer *calling* the relevant
Layer-A method as a **utility** (Layer A is the shelf; producers reach for it).
The drift to watch (caught twice this session): rationalising a pre-pass back in
under a "noise"/"preserve old output" label.  Old output is NOT the oracle.

**Family 1 — layout-unwrap: DRAINED.**  `_unwrap_layout_templates` (inside the
text producer `_transform_body_text`) gained `block center / larger / smaller /
nowrap / Fine / sm`; the Layer-A `c_unwrap`/`balanced_unwrap`/`poem_unwrap`/
`csc_normalize`/`fine_print_se` passes are now duplicates of it (bypassed; delete
when convenient).  Verse/center/fine-block render from raw via the producer.

**Image family — DRAINED (figure-caption, inline, css_crop, raw-image), 2026-05-25.**
Every image row of the Stage-2 queue landed, and notably **none needed a pre-pass
re-added** — each was the OWNING layer (walker or classifier), carry-raw:
- **Figure caption-pairing** (ACCUMULATOR Fig 3) — NOT a producer-utility call, a
  walker mis-break.  `figure_tail_end`'s `_SEP` now treats pure spacer templates
  (`{{em|N}}`/`{{gap}}`/`{{dhr}}`) as separators, so a `{{em|3}}` between image and
  `{{Fs|…{{sc|Fig.}}…}}` caption no longer halts the run.  Byte-identical to
  snapshot; corpus orphan audit **0 real orphans / 1071 IMAGE**.  `_figure.py`.
- **Inline glyphs** (A, ALPHABET) — the "positional survivor", done with NO
  pre-pass and NO walker logic.  The walker already carries the surrounding markup
  in the placeholderized text; `classify_article` (`_mark_inline_images`) reads
  the IMAGE placeholder's trailing line-context and relabels prose-adjacent ones
  `INLINE_IMAGE`; the producer stamps `align=inline` (`force_align`).  Vols 1,20:
  93 INLINE_IMAGE, all genuine (letterforms, per-symbol, chem `Rangle`/`Langle`),
  0 block mis-fires.
- **css_crop** (218; SHIPBUILDING/OPIUM/SEWERAGE) — walker recognition only:
  `_DJVU_CROP_RE` + opener hint + `_derive_double_brace_label`→DJVU_CROP; producer
  `_process_djvu_crop` already existed.  Per-page crop index order-consistent. No leak.
- **raw-image** (34; PACIFIC OCEAN/SWITZERLAND maps, WEIR/WATER MOTORS figures) —
  `_RAW_IMAGE_RE`→RAW_IMAGE→new `_process_raw_image` (djvu page-ref →
  `djvu_volNN_pagePPPP.jpg`; plain filename keeps spaces; `{{c|cap}}` folded). No leak.

The recipe held every time: diagnose the mis-break → fix the layer the
architecture points to → verify (byte-diff + corpus count).  `{{raw image}}` is
"bare full-image, no inline caption" — full-page djvu (maps/plates) AND plain
figure files; the producer forks on the arg.

**Remaining image work:** only **table-figure legends** (BRACHIOPODA — legend in
an HTML `<table>`, the missing inter-cell space) — that's the table-path/ICL
mechanism, its own problem.

**Seed regression net (standalone runner `tools/_scratch/run_seed_snapshots.py`,
since the pytest conftest needs missing `mwparserfromhell`).  Initial flip: 8 pass
/ 12 fail; after the image family: 9 pass / 11 fail (A green; css_crop/raw-image
articles aren't seeds — verified directly on OPIUM/SEWERAGE/WEIR/PACIFIC OCEAN);
0 green→red.  Initial queue map below:**
The 8 green = layout/simple (validates Family 1).  The 12 red = the per-family
producer queue — each a producer that must CALL a Layer-A utility it lost:

| Seed(s) | Producer | utility to call |
|---|---|---|
| ACCUMULATOR, STEAM_ENGINE, BRACHIOPODA | CAPTIONED_FIGURE / IMAGE EXTCAP | caption-pairing (`center_file_split`/`bundle_raw_image`/GLUED_BR fold) |
| ABBEY, HYDROMEDUSAE | LEGENDED_FIGURE | `_transform_body_text` on legend cells |
| A, ALPHABET | IMAGE (inline) | `promote_inline_glyphs` — **positional** (the rare survivor; tag-not-transform is the honest target) |
| AFRICA | HTML_TABLE | table cell/quote normalization |
| ACCUMULATOR-chem | CHEMISTRY_LAYOUT | chem cell handling |
| ALDEHYDES (`＋`→`+`), MOLECULE (lead space), AGRICULTURE | text/chem/verse | `normalize_unicode`/`replace_print_artifacts`/whitespace — pure-noise; **re-baseline** (honest output is the non-meddling one) |

**Proof the flip lost nothing:** `raw_error=0` corpus-wide; the producer-output
diff (pure-noise filtered) was ~3% real divergence, all in these families.
Net: image/figure/table/chem are the work — the SAME producers the table-path
purity campaign (Prior focus) was sharpening, so it folds in here.

**NEXT:** per-family, wire each red producer to call its utility (image/figure
first), turning reds green; re-baseline the pure-noise seeds; delete each Layer-A
pass as its family lands.  Tests stay red-then-green per family by design — NOT
pushed to production (deliberately, to keep liberty to break).  Standing
classifier-tier work this lens still implies: drain LAYOUT_WRAPPER (~107
mislabels).

---

## Prior focus (2026-05-25) — Remove non-tables from the table path; **`<table>` FIGURE+MATH+CHEM+SINGLE-COLUMN+VERSE routed** (HTML_TABLE 49%→98% pure)

### Step-3 `<table>` flip LANDED — figures left the table path (2026-05-24)
`_classify_html_table` (`_classifier.py`) routes a `<table>` through
`_classify_table` but remaps genuine-table labels back to HTML_TABLE, so only the
figure family (`_HTML_TABLE_ROUTE_AWAY` = the 5 captioned/legended/unpaired
labels) leaves the path.  **Result (purity scoreboard):**

| Path | Before | After |
|---|---|---|
| HTML_TABLE | 4998, **49%** pure (2073 figures) | 2942, **84%** pure (**figures 2073→17**) |
| DATA_TABLE | 1272, 95% | 1272, 95% (unchanged) |
| COMPLEX_HTML | 1506, 96% | 1506, 96% (unchanged) |

The flip exposed latent FIGURE-PRODUCER bugs (the WIN — table-path entanglements
became LOCAL producer bugs, [[turn-bugs-into-producer-bugs]]); all fixed in the
producers, render-verified, **0 content loss, bounded to the figure bucket**
(`snapcheck.py`; all 9 changed snapshots are figure articles, rebaselined):
- **Metadata-carry** (`_image_ph_meta`) — figure producers now pass
  width/height/align to `_assemble_figure_parts` (dropped before, wiki AND table).
- **Poem-caption** (`_CAPTION_POEM_RE`) — a `<poem>` opening with Fig./Plate.
  folds as caption, not chopped by `_emit_legend_chunk`.  JOINTS Fig 1/2 fixed.
- **In-cell content** — `_process_simple_plate` reads each image's OWN cell, not
  just rows below.  JOINTS Fig 4/5 fixed → all 7 JOINTS figures render full.
- **Conservative caption / no fancy legend heuristics (option A)** —
  `_has_legend_material`: `{{Hi}}` is NO LONGER a legend signal (ambiguous: real
  legend in ARACHNIDA Fig 26 vs sub-figure list in BRACHIOPODA Fig 12-18, no
  clean discriminator → default to caption); prose-cell detection skips
  Fig./Plate.-opener AND `{{Hi}}` cells.  BRACHIOPODA now content-complete (minor
  parens on the sub-figure list); ARACHNIDA `{{Hi}}` legends fold to captions
  (approved, lossless); HYDROMEDUSAE's dedicated prose-cell legend still extracts.

**Cleanup follow-ups (small):** delete the now-dead `_extract_hi_legend` /
flowing-italic in `_process_legended_figure`; re-run `render_zero.py` on the
`<table>` population WITHOUT the metadata filter for a final end-to-end gate.

### MATH/CHEM buckets — LANDED 2026-05-24 (HTML_TABLE 84%→86%)
Cheapest because the CLASSIFIER already recognized them — only producer plumbing
needed (the wiki path stays byte-identical; a `<table>` branch is added):
- MATH: `_process_equation_layout` + `_process_math_layout_table` read cells via
  `_content_rows` (wiki=`parse_wiki_table`, `<table>`=`_html_table_grid`).
- CHEM: `_process_chemistry_layout` splits `<tr>` + `_split_html_chem_row` (the
  span-aware `<td>/<th>` analog of `_split_chem_row`); wiki path untouched.
- Added `MATH_LAYOUT_*` + `CHEMISTRY_LAYOUT` to `_HTML_TABLE_ROUTE_AWAY`.
Result: HTML_TABLE math 70→4, chem 6→0, figure-residue 17→12 (5 chem-bracket
"figures" recovered to CHEMISTRY_LAYOUT — confirming CHEM was bigger than the bare
6).  Content-safe (`check_mathchem_textloss.py`: only marker/template/placeholder
tokens consumed by producers, 0 formula/equation content lost).  362 tests green.

### SINGLE-COLUMN bucket — LANDED 2026-05-24 (HTML_TABLE 86%→92%)
`_is_single_column_table` (detector) + `_process_single_column_table` (producer)
made `<table>`-aware (detector uses `_table_grid` with the `|-` gate kept
wiki-only so wiki is unchanged; producer branches `_html_table_grid`).  Added
SINGLE_COLUMN_TABLE to `_HTML_TABLE_ROUTE_AWAY`.  HTML_TABLE single-col 210→4
(206 → `«PRE:`); content-safe (`check_mathchem_textloss.py`: only 2 `eb` ref-marker
tokens, 0 real content).  Unit test `test_html_table` updated (one-cell `<table>`
is now SINGLE_COLUMN_TABLE; added `test_html_table_single_column`).  363 green.

### VERSE bucket — LANDED 2026-05-25 (HTML_TABLE 92%→98%)
NOT the 2-col-quote `_is_verse_table` shape — the 167 are POEM-WRAPPERS: a table
that just centres `<poem>` child(ren) (BELL/BOAT — a quotation).  New
`_is_poem_wrapper_pred` (≥1 POEM child, no IMAGE, no data-header, AND no
substantive non-poem cell text) placed BEFORE `_is_layout_wrapper_pred`;
`_process_verse_table` gained a poem-child branch (emits each `<poem>` as
`{{VERSE:}`, like `_process_poem`); VERSE_TABLE added to route-away.  167→6
(the 6 are caption+poem figure-legend tables — BRACHIOPODA — correctly KEPT: the
substantive-content check excludes them so their caption isn't dropped).
Content-safe by construction (cell is only the poem) + 363 green.

### NEXT SESSION (2026-05-25+) — the HARD cases: ~100-200 classification errors
The easy wins are done — every bucket whose shape the classifier ALREADY
recognized has been routed (figures/math/chem/single-col/verse), HTML_TABLE
49%→98%.  What remains is ONE kind of work: **classification errors** — shapes
the classifier does NOT yet recognize, so they land in a catch-all / wrong label.
These need RECOGNITION (new/fixed predicates), not producer plumbing.  Inventory:
- **LAYOUT_WRAPPER (108)** — pure misclassification sump (its un-pairable-figure
  role is empty post-flip): 36 verse, 23 single-col, 22 nested-figure-group, 19
  data-tables (Governors lists / grammar / correlation tables — `«other»`), 8
  single-image.  Each belongs to an existing producer but isn't recognized as
  such.  Characterize with `tools/diagnostics/layout_wrapper_contents.py`.
- **HTML_TABLE residue (26)** — 12 figure (CATACOMB/CORNET miss the ICL gate),
  6 verse (caption+poem figure-legend tables), 4 single-col, 4 math.
- **COMPLEX_HTML residue (45)** — 36 math, 7 single-col, 5 verse, 4 figure
  (these are `{|`-with-spans / span-HTML; a different recognition surface).
- **DATA_TABLE residue (54 single-col)** — wiki one-col tables to re-check (the
  2 "math" are the legit INFINITESIMAL CALCULUS reference grids — leave).
Approach: same as this session but the hard half — recognize each shape
structurally, route to its producer, verify render-zero + content-safe + purity.
Verification net (all in `tools/diagnostics/`): `check_table_path_purity.py`
(scoreboard), `render_zero.py` (producer render-diff), `check_mathchem_textloss.py`
(content-preservation per routed label), `layout_wrapper_contents.py`.

### Step-4 cleanup (deferred) — drain `_process_html_table`, delete dead code
Now that figures/math/chem/single-col/verse leave the `<table>` path,
`_process_html_table`'s buried `_unwrap_html_illustration` branch is superseded
(delete it); and `_extract_hi_legend` / flowing-italic in `_process_legended_figure`
are dead (the conservative-caption fix dropped `{{Hi}}`/flowing-italic legends).
`_row_is_legend` (`_layout.py`) is also dead.



**THE GOAL (reframed this session):** not decomposing the table producers — it's
**removing everything that isn't truly a table from the table path**.  Producer
leanness is a *consequence*, not the goal.  Non-tables in the table path is the
ROOT of almost every bug this campaign found (#8/#10/#12-empties/#13/#6) — the
table producer's job is to grid-and-flatten, so handing it a non-table corrupts
it.  Metric = **table-path purity**.  See `[[remove-nontables-from-table-path]]`.

**"When is a table not a table?"** — when its grid is *incidental* (a positioning
crutch), not load-bearing for meaning.  Test: strip the grid, reflow the cells —
if meaning survives, it was never a table.  Non-tables wearing table syntax + the
content signal that unmasks each: figure (IMAGE child) · verse (POEM child) · chem
(element-formula + reaction operator) · math (math content, not a value grid) ·
preformatted (single content column) · plate (`article_type=='plate'`, a separate
pipeline).  Genuine tables (stay): DATA_TABLE (the grid IS the data) · HTMLTABLE
(needs cell spans); a reference grid of equations (function/derivative) IS a table.

**Governing invariant:** every producer is shape-in → shape-out; NEVER self-
classifies.  Transform only in minimal preprocessing or producers (classification
is structure-alone; content-recognition justified only for CHEM/MATH/VERSE).
Corpus static → corpus-verified claims durable.  See `[[table-producer-invariant]]`,
`[[transform-only-two-places]]`, `[[layout-wrapper-definition]]`,
`[[plate-component-model]]`, `[[source-is-static]]`.

### TABLE-PATH PURITY scoreboard (`tools/_scratch/check_table_path_purity.py`)
| Path | total | genuine grid | pure | remaining non-tables |
|---|---:|---:|---:|---|
| DATA_TABLE (wiki `{`-pipe) | 1272 | 1216 | ~99.8%\* | 54 single-col, 2 math\* |
| COMPLEX_HTML | 1506 | 1454 | 96% | 36 math, 7 single-col, 5 verse, 4 figure |
| HTML_TABLE (`<table>`) | 4998 | 2472 | **49%** | **2073 figure**, 210 single-col, 167 verse, 70 math, 6 chem |

\* the 2 DATA_TABLE "math" are the INFINITESIMAL CALCULUS derivative/integral
reference grids — genuine tables (scan false-positive).  The **wiki path is
essentially DONE** (the carves worked).  **ALL remaining impurity is the `<table>`
path** — HTML_TABLE is 49% pure (half non-tables, dominated by 2073 figures).
Phase 2 routes `<table>` through the shape classifiers → ~pure.

**Done this session (committed unless noted; NOT yet rebuilt/deployed):**
- **#8 CHEM** — element-aware reaction recognizer (`_has_chem_reaction_content`:
  periodic-table + formula grammar, operator-connected formulae in a cell;
  wrapper-agnostic core `_chem_row_is_reaction`) wired as 3rd OR-arm of
  `_is_chemistry_layout_pred`.  16 reactions routed → CHEMISTRY_LAYOUT (7
  DATA_TABLE, 5 COMPLEX_HTML, 3 SINGLE_COLUMN, 1 MATH), 0 collateral.  PURIN's
  reaction diagrams now uniform.  MATH-gap probe found NO gap (the 2 INFIN.
  CALCULUS math grids are legit DATA_TABLE).
- **#10 `{{sub}}`/`{{sup}}`** — text_transform STRIPPED these → ~7000 sub/super
  lost across 195 articles (apocaffeine C₇H₇N₃O₅ + hypocaffeine C₆H₇N₃O₃ both
  rendered "CHNO").  Fixed at top of `_convert_sub_sup` (body_text.py).
  Scoping-verified: single central call site (the shared text_transform);
  sibling `_convert_inline_sub_sup` is `<sub>`-only and feeds text_transform.
- **#12 figure-removal milestone** — SIMPLE_PLATE + CAPTIONED_FIGURE_GRID
  classifiers REMOVED, collapsed into one clear label **UNPAIRED_FIGURE_GROUP**
  (un-pairable multi-image; producer = `_process_simple_plate`, proven TOTAL:
  ≥passthrough bundles in every case, **+11 bundling fixes** incl 4 grids).  381
  multi-image figures, **0 table-path leaks by construction**, 0 regressions; all
  381 audited OK (every IMAGE child bundled, 0 lost —
  `check_unpaired_figure_output.py`).  Dead code removed (`_is_image_grid`, dead
  labels/dispatch).  B-lite primitive **`_table_grid`** (rows×cells, both syntaxes,
  robust to unclosed `<td>`/`<tr>`) added; ICL helpers `_image_alone_in_row` +
  `_has_inline_caption_signal` + the 3 `_is_icl_family` anti-signals made
  syntax-agnostic (the gate is now `<table>`-ready).

Every carve verified by the corpus-wide label-distribution diff (intended
transitions only, zero collateral) + snapshots 20/20.  Verification net:
`tools/_scratch/table_label_dist.py` (now **skips `article_type=='plate'`** to
mirror production — production routes plates to `parse_plate`, not the element
pipeline) + `diff_tld.py`; baselines `tld.np0..np5.jsonl`.  **Promoted** to
`tools/diagnostics/` (2026-05-24): `table_label_dist.py`, `diff_tld.py`,
`check_table_path_purity.py` (their `tld.*.jsonl` baselines stay in `_scratch`).

### Phase 2: route `<table>` figures out of the table path (the 2073) — steps 1-2 DONE
Same playbook as the wiki carves, applied to `<table>`.  Steps (task #12):
1. **Legend + chem helpers agnostic — DONE 2026-05-24, wiki-zero verified.**
   `_row_has_legend_multicol_cells` now takes a **cell-list** (was a wiki row-
   string); `_has_legend_material` + `_has_chem_reaction_content` feed it via
   `_table_grid`, so both fire on `{|` AND `<table>`.  Two `_layout.py` callers
   (`_row_is_legend`, the multicol producer) updated to pass `split_wiki_row`
   cells.  Wiki-zero: `tld.s1pre→s1post2` = **0 transitions, 0 elements changed**.
   (`_has_beside_legend_signal` left wiki-only — the preview shows NO `<table>`
   figure routes to BESIDE, so it degrades gracefully to LEGENDED/CAPTIONED.)
   (`_row_is_legend` is dead code — only its own def; clean up later.)
2. **Figure producers read `<table>` cells — DONE 2026-05-24, wiki render-zero
   verified.**  Converted the 5 producers reachable by `<table>` figures —
   `_process_captioned_figure` (1693), `_process_captioned_figure_inline`,
   `_process_legended_figure_child` (46), `_process_legended_figure` Phase 2,
   `_process_simple_plate` (242) — to build cells via `_table_grid` instead of
   `re.split(|-)`+`split_wiki_row`.  **Wiki render-zero: 1224/1226 byte-identical**
   (`render_zero.py` full-corpus before/after); the 2 diffs are an INCIDENTAL FIX —
   `_table_grid` drops a dangling `|-` separator that the old `_process_simple_plate`
   run-collapsing split mis-captured as a `-` cell → spurious `(-.)` attribution
   (BEARINGS Fig 6, BELLOWS Fig 8).  And **`<table>` figures render content-
   preserved**: `check_table_figure_producer.py` → 2059 figs with NEW≥OLD images
   (vs the buried `_unwrap_html_illustration`), **0 image drops, 0 producer errors**;
   14 route to non-ICL producers (LAYOUT_WRAPPER/CHEM residue, step-2 follow-up).
   Residual producers NOT yet `<table>`-aware: `_unwrap_layout_table` (uses
   sep/attr; 10 figs), chem-figure (5), beside (wiki-only).  362 tests pass.
3. **Flip routing — NEXT (the invasive step; pause-point agreed with user).**
   Route `<table>` through the shape classifiers instead of flat
   `_derive_html_tag_label` (`tag=="table"→HTML_TABLE`).  **Safest design (refined
   from the preview):** a `_classify_html_table` adapter that calls `_classify_table`
   but **remaps any genuine-table label (DATA_TABLE/COMPLEX_HTML/…) back to
   HTML_TABLE** — because `DATA_TABLE`'s producer `_process_table` is wiki-only and
   would break the 789 no-span `<table>` grids that fall to the catch-all.  This
   ISOLATES the change to non-tables: the 2472 genuine grids stay byte-identical
   (still `_process_html_table`); only the 2071 figures + 66 math + 164 verse + 6
   chem newly route to proper producers.  Preview (`preview_html_table_routing.py`):
   figures 2071/2073 leave, chem 6/6, math 66/70, verse 164/167.  Verify render
   equal-or-better vs the buried branch (which has gaps: MAGNETISM empty,
   BRAIN/CARPET leak); extend `render_zero.py` to the `<table>` population.
4. **Drain `_process_html_table`** to the genuine span-HTMLTABLE residue; DELETE
   `_unwrap_html_illustration` (pure duplicate of the shared figure pipeline).

New diagnostics this session — promoted to `tools/diagnostics/`:
`preview_html_table_routing.py` (the flip dry-run / oracle×flip-label crosstab),
`render_zero.py` (full-corpus before/after producer render-diff via
`_shadow_transform`; `capture <tag>` / `diff <a> <b>`), `check_table_figure_producer.py`
(NEW-vs-buried image preservation on `<table>` figures).  Their per-run artifacts
(`rz.*.json`, `tld.*.jsonl`) stay disposable in `tools/_scratch/`.

Then drain COMPLEX_HTML's 45 non-tables + LAYOUT_WRAPPER's ~107 residue (verse→
VERSE, single-fig→CAPTIONED_FIGURE, data-shells→table homes).  NOTE: the `<table>`
figures CURRENTLY render as `{{IMG:}}` via the buried `_unwrap_html_illustration`
branch — so this is mostly relocating *recognition* (out of the table path, onto
the shared pipeline, closing the duplicate's gaps), not first-time rendering.

**Filed (separate tracks):**
- **#13** `{{dual line|A|B}}` stripped by text_transform → 625 two-line formulas
  lost across 66 articles (#10-sibling; surfaced by the #12 HYDRAULICS empty;
  quick fix mirroring #10).
- **#11** delete `_convert_inline_sub_sup` (de-dup — text_transform now owns
  sub/sup + tag-strip; gated on a render check of the COMPLEX_HTML articles).
- **#6** spurious `⟦r⟧`/`⟦c⟧` colspan — several instances fixed incidentally by #8.
- **#3** wiki no-pipe "inline-text" drawer — largely subsumed; the wiki path is
  ~99.8% pure, so the residue is small (54 DATA_TABLE single-col to re-check +
  a few prose).

**Earlier in this campaign (committed):** SINGLE_COLUMN_TABLE carve (→`«PRE:`),
VERSE_TABLE carve (2-col + single-cell quote verse → `{{VERSE:}`), math
spacer-heavy over-claim fix (`_INLINE_MATH_SIGNAL` gate); #4 image-frame VERIFIED
NON-BUG (all plate articles); #24 prose-figure producer; #25/#28/#30
table-metadata + sub-header fixes.  #29 HTMLTABLE de-HTML (AFRICA `<ref>`-in-`<td>`
leak) still queued — naturally folds into Phase 2.

---

## Prior focus (2026-05-23) — Structural figure break: `_process_figures` DELETED

Goal achieved: the walker/classifier/producer now PRODUCES the final figure;
nothing runs after it.  The `_process_figures` post-pass (a prose heuristic) is
**deleted**.  Captions/legends in EB1911 source are always *structurally*
delimited (templates/tables), never bare prose — so recognition is structural.

**The structural figure break** (`elements/_figure.py`):
- `figure_wrapper_end` (`{{center|…image…}}` wrapper IS the figure) +
  `figure_tail_end` (bare image + its caption/legend run).  Pure structural
  gates, **NO length heuristics**: caption templates require an `{{sc|Fig}}`/
  `(From` signal inside; bare `Fig. N.—…` requires the em-dash immediately after
  the number (so body "Fig. 6. The simplest…" is NOT a caption); italic-label
  legends are `«I»short«/I», text` (comma, not period — `«I»d«/I». …` is a body
  item); verse legends are `<poem>`; attribution is parenthesized `(From`/
  `(After`; attribution-only tails (no caption) are left alone.
- `SHAPE_FIGURE` in the walker (leaf); `_produce_figure` re-processes the span
  with `_allow_figure=False` then runs `_assemble_figures` (the assembly utility,
  now a producer helper — TEMPORARY; a fully structural producer is the next step).
- The old prose-based `LOOSE_FIGURE` detour was ripped out first (it used the
  POST-production classifier pre-production; structural recognition replaced it).

**Verification (the discipline that mattered)** — render-level, not length:
- Body-preservation: **0 render diffs / 1499** with the break vs baseline.
- Deletion is data-safe: **0 content loss** (word-multiset check — only 3
  cosmetic hyphen/space joins at figure boundaries, all letters preserved).
- Deleting `_process_figures` is a NET WIN: ~73 body paragraphs the post-pass had
  wrongly captured (numbered sections "21. Method…", taxonomy, author citations,
  article openers) return to body.
- Snapshots **rebaselined** (`tools/diagnostics/capture_transform_snapshots.py`);
  full suite green (359).

**FILED BACKLOG** — two content-preserving format forms the structural producer
must still own (see tasks): (1) **attribution-fold** — `(From X.)` after a figure
lands as a stray body line instead of folding into the caption (~51); (2) **loose
table-legend** — a `{|`/`<table>` legend after an image renders as `{{TABLE}}`
not `{{LEGEND}}` (~37); plus the 3 cosmetic hyphen-joins.  These are *wrong*
(our problem in the new architecture), not regressions vs the deleted band-aid.

Kept tool: `tools/diagnostics/figure_span_audit.py` (over-absorption audit).

---

## Prior focus (2026-05-19) — Figure-shape redistribution + contributor signal

**Figure pipeline rewritten as focused producers**.  The 1700-line
`_unwrap_layout_table` catch-all has been dissolved into 6 focused
producers, each owning one structural shape and dispatching to a
shared assembler.  The architectural principle: classification is
the work — once the right shape gets the right label, producer
bodies become ~50 lines of orchestration over shared helpers.

**Labels added this session** (`pipeline/stages/elements/`):
- `CAPTIONED_FIGURE` — single image + caption (component-finder body,
  no fall-back).  ~52% of figure-shape wikitables.
- `CAPTIONED_FIGURE_INLINE` — image + caption share one cell
  (`<br>`-separated; ORDNANCE Fig 54-style).  ~3%.
- `LEGENDED_FIGURE` — cells-based legend (multicol-alternating,
  multicol-full-entry-with-continuation, prose-cell single).
  Unified through `_chop_legend_entries(text, delimiter, …)` —
  one helper, multiple sub-shapes.  ~12%.
- `LEGENDED_FIGURE_CHILD` — legend lives in a POEM placeholder or
  nested wikitable child.  ~4%.
- `SIMPLE_PLATE` — multi-image arrangements that don't fit the
  simple parallel-row grid (vertical-stack OR multi-row column-
  slice).  Real population is the multi-image figure WIKITABLES
  embedded in regular articles; standalone plate ARTICLES still
  go through `parsers/plate/` (separate pipeline by design).

**Shared figure pipeline** (`elements/_layout.py`):
- `_extract_figure_components(cells, registry, tt, skip_ph)` —
  partitions cell text into (caption, attribution, legend) via a
  Fig./Plate. marker split.  Handles POEM placeholders embedded
  in cells, image-cell-with-text shape via `skip_ph`.
- `_assemble_figure_parts(filename, cap, attr, legend)` — canonical
  `{{IMG:fn|caption (attribution)}}` + optional `{{LEGEND:…}LEGEND}`.
  Source-shape variations collapse to the same output here.
- `_unwrap_cell_wrappers` — strips `{{center|…}}`, `<span>…</span>`,
  `{{Fs|N%|…}}` via balanced-brace matching.
- `_chop_legend_entries(text, delimiter, tt)` — one helper for
  multicol-alternating, multicol-full-entry, prose-cell entries;
  auto-detects label-only vs full-entry shape from first chunk.

**LAYOUT_WRAPPER residual**: 3374 → 444 figure-shape hits.  Most of
the 444 are now genuine non-figure layouts (plate articles routed
elsewhere, verse-only wrappers, table-only wrappers) rather than
figure shapes the architecture can't handle.  Catch-all is doing
its job again.

**Snapshot suite** (`tests/regression/test_transform_snapshots.py`):
11/18 → 15/18 passing.  The 3 remaining failures are precise
regression signals for tracked future work, not noise (see
"Queued").

**New tool**: `tools/diagnostics/snapshot_diff_patch.py` — surgical
hunk-level snapshot updater.  Computes the line-level diff against
a snapshot, exposes each non-equal opcode as a numbered hunk, and
applies specific hunks back via splice while leaving every other
line byte-identical.  Lets us accept intentional output changes
(IMG/LEGEND standardization) while keeping the snapshot useful as
a regression-detection contract on unrelated lines.

**Contributor extractor: wikilink shape landed**
(`extract_contributors.py`).  ~152 articles credit their authors
as `{{right|([[Author:Full Name|Initials]]; …)}}` instead of the
canonical `{{EB1911 footer initials|…}}` template — THUCYDIDES is
the canonical case.  New `_RIGHT_AUTHOR_PATTERN` +
`_parse_right_author_contributors` extract `(name, initials)` from
each `[[Author:…|…]]` wiki-link, unwrap `{{small-caps|…}}`
wrappers, and feed the same downstream attribution path.  ~152
articles will pick up contributors on the next pipeline run.
Long-tail (~28 articles, mostly bare `:([[Author:…]])` and
parenthesized-initials shapes) tracked separately.

**Audit tools written**:
- `tools/_scratch/audit_figure_layouts.py` — per-bucket
  classification health check.
- `tools/_scratch/audit_signature_shapes.py` — end-of-article
  signature/contributor shape inventory.
- `tools/_scratch/audit_layout_wrapper_figures.py` — figure-
  shape-only LAYOUT_WRAPPER residual audit.
- `tools/diagnostics/label_distribution_snapshot.py` +
  `label_distribution_diff.py` — capture per-element label
  assignments across the corpus and compute directional
  transition counts.  The regression-surface check for any
  predicate change.  See
  `[[feedback_classification_is_regression_surface]]`.

**Failed loosening — diagnostic value**.  Attempted to relax
`_is_captioned_figure_pred`'s "image in row 0" / "no `||` in row 0"
gates to recover the 62-hit LAYOUT_WRAPPER figure-shape residual.
Reverted after the directional-diff revealed 4 real data-table
regressions (COMPLEX_HTML/DATA_TABLE → CAPTIONED_FIGURE) plus
figure-family regressions (ABBEY Fig 1's `|ELEM||legend` shape
was being handled correctly by LAYOUT_WRAPPER's
`_try_image_layout_subclass`).  Lesson: those gates were doing
structural-shape discrimination, not redundant data-table
protection; the LAYOUT_WRAPPER catch-all also does meaningful
internal work via its subclass mechanism.  Led to the ICL-family
gate / family-collapse architecture (`[[feedback_family_sub_pipelines]]`,
`[[project_icl_family]]`).

**Tests**: 286 unit/integration passing (same 8 pre-existing reds —
legend-extraction sub-patterns + chemistry-layout 2-D table); 15/18
snapshot regression tests passing.

---

## Previous focus (2026-05-17) — Phase A recovery shipped

The 2026-05-16 V2 deploy shipped marker-contaminated titles (`«B»X«/B»` in
the `title` field) plus a separately-broken xref resolver and contributor
linker — both downstream consequences of the same root cause.  Today's
Phase A recovery reverts the title contract and ships clean.

**Root cause:** an in-session edit to `_clean_extracted_title` kept the
`«B»/«I»/«SC»` formatting markers in the returned title so the viewer's
H1 could render typography.  Eight surfaces read `title` as plain text
(volume index, search, xref resolver, contributor linker, Meilisearch,
Reader's Guide, topics page, URL-slug builder); only the H1 was patched.
Every other surface either rendered raw `«B»` characters or failed
string-equality matching.  Net result: ~98% of titles displayed garbage
in the volume index, ~89% of cross-references unresolved (28,613 lost),
~70 contributors orphaned.

**Phase A fixes shipped today:**
- `detect_boundaries.py::_clean_extracted_title` — strips `«B»/«I»/«SC»`
  markers, returns plain title.  Single chokepoint.
- `detect_boundaries.py` multi-line bold extension — when first content
  line ends with `«/B»` and the next starts with `«B»`, the extractor
  joins them.  Fixes ROBESPIERRE, MAXIMILIEN FRANÇOIS MARIE ISIDORE DE
  (title's bold span spans two physical lines in source).
- `clean_pages.py::_convert_quote_runs` — applies quote-run conversion
  inside `<ref>...</ref>` blocks before masking, so italics in citations
  (`''Ency. Bib.''`) get marked correctly.  `stray_wiki_italic` 2,159 → 15.
- `tools/rebuild_all.sh` — quality report moved to Phase 6f (pre-deploy)
  for visibility.  Gate-style blocking deferred to a follow-up.
- 6 corrupted quality-report baselines deleted from
  `data/derived/quality_reports/` (post-stacked-DB-rebuild artifacts).
- `data/contributor_aliases.json` — three pairs added so `_clean_name`
  collapses them on next rebuild: Lawrence F. Abbott / Laurence Abbott
  (the one visible-on-page dup), H. Hamilton Fyfe / Hamilton Fyfe,
  Ralph Stockman Tarr / Ralph Stockman.  Only Abbott is currently
  visible (the others have one empty side).

**Tests recovered:** the 2026-05-16 boundary rewrite broke 24 unit tests
(fixtures fed raw `'''X'''` to `detect_boundaries`, which now consumes
cleaned `«B»X«/B»`).  Plus 9 regression/integration tests in the same
fixture-shape family.  All 33 updated to call the real
`_convert_quote_runs` before passing to the boundary parser.  Test
suite is back to being a real signal: 286 passing, 8 remaining red —
each one a documented production bug (image-legend extraction +
chemistry layout), not a stale fixture.

---

## Last full rebuild

**2026-05-17 — Phase A recovery deployed to britannica11.org.**
- 36,671 articles (+8 vs 2026-05-14 baseline)
- 31,815 xrefs resolved (vs 31,954 baseline — close to parity)
- 5,219 xrefs unresolved (vs 5,131 baseline)
- 0 titles contain `«B»/«I»/«SC»` in the JSON `title` field
- stray_wiki_italic: 15 (was 2,159 yesterday, 2 on 2026-05-14)
- stray_close_braces: 9 (unchanged from baseline)
- 1,501 contributors created, ~48 unlinked after Phase 3b → ~7 after Phase 3b2

---

## Queued (next session)

**Figure-shape redistribution follow-on** (each item is a tracked
failing snapshot in `tests/regression/test_transform_snapshots.py`
or a known LAYOUT_WRAPPER residual):

- **STEAM_ENGINE Fig 10 — preprocessing-to-producer migration.**
  `transform_articles/__init__.py` lines ~470-479 unwrap
  `{{center|[[File:…]]<br>caption}}` to `[[File:…]]\ncaption`
  BEFORE classification.  The unwrap was scaffolding from the
  catch-all era; with `CAPTIONED_FIGURE_INLINE` in place the
  preprocessing is producer logic in disguise — and it's the reason
  Fig 10's caption is lost in the current pipeline (the preprocessing
  strips the wrapper inside wikitables, leaving the producer with
  a degenerate shape).  Two paths: (a) tighten
  `CAPTIONED_FIGURE_INLINE` to handle the post-preprocessing shape,
  or (b) move the unwrap into the producer + add a sister extractor
  for the bare-`{{center|…}}` (non-wikitable) case.  (b) is more
  architecturally correct.  See
  `[[feedback_preprocessing_is_producer_work]]`.

- **ARACHNIDA Fig 3 — `{{hi|…}}`-separated same-line legend.**
  11+ legend entries packed into one cell, each wrapped in
  `{{hi|…}}` or separated by `<br>`, all on a single line.
  Neither multicol-row nor prose-cell-by-newline detection catches
  it.  May warrant a new label `LEGENDED_FIGURE_INLINE` (legend
  material packed into one cell).  Likely shared shape with
  ARACHNIDA Figs 26, 73, 78.

- **HYDROMEDUSAE Statocyst-series legend ordering.**  60 hunks,
  many showing legend entries in different order than snapshot.
  Statocyst figures (30-44) share legend structure across multiple
  images.  Need to inspect a representative figure visually before
  deciding whether new ordering is correct (column-major reading)
  or a regression.

- **ORDNANCE Fig 86-7 — positional sub-labels shape.**  Image
  contains two diagrams (Fig 86 + Fig 87) with positional labels
  meant to sit UNDER each in the rendered image.  Source has a
  row of `<span>` labels + a colspan caption row.  Currently
  baselined as "wrong but no worse than production" — when the
  positional-sub-labels shape gets its own producer (drop the
  labels in text rendering, keep the caption), snapshot will
  diverge and we re-evaluate.

- **Contributor extractor long-tail (~28 articles).**  After the
  `{{right|[[Author:…]]}}` pattern lands, residual signature shapes
  per `tools/_scratch/signature_shapes_audit.md`: 7 bare-`(X. Y.)`,
  7 `{{right|(X. Y.)}}` no-Author-link, 2 right-template-other,
  ~12 bare `:([[Author:…]])` (need discriminator vs in-prose Author
  refs).  Note: actual user-visible miss after the wikilink fix is
  smaller because volume author lists and vol 29 contributor list
  (the other two signals) cover some of these.

- **Refactor `parse_plate.py` to classify-then-produce architecture.**
  Plate articles stay in their own pipeline (different beast from
  regular articles — different inputs, different output
  expectations).  But the parse_plate.py implementation should use
  the same architectural principles as elements: walker identifies
  shape boundaries, classifier assigns labels (SIMPLE_PLATE,
  GROUPED_PLATE for GEM-style aggregated captions, etc.),
  producers are small focused handlers per label, shared assembler
  for canonical output.  Two pipelines stay separate but analogous;
  they share producers, utilities, predicates, labels — just
  organized as separate passes.  See
  `[[feedback_pipelines_share_producers]]`.

**Medium-term roadmap — redistribution by shape family, then collapse.**
The figure-shape work this session is the first of three analogous
redistribution campaigns; once each family's sub-shapes stabilize, a
final collapse encapsulates the family behind a single outer label.

1. **Figure-shape (ICL) redistribution** (this session — mostly done):
   IMG/caption/legend producers carved from LAYOUT_WRAPPER.  62
   figure-shape edge cases remain in LAYOUT_WRAPPER per
   `tools/_scratch/layout_wrapper_figures_audit.md`; predicate
   tightening attempted (`#24`) revealed real regression risk
   (4 data-table over-claims + figure-family transitions) — see
   `[[feedback_classification_is_regression_surface]]`.  Tracked
   as `#24`.
2. **Table-shape redistribution** (next campaign): the remaining
   non-figure LAYOUT_WRAPPER contents are TABLE_WRAPPER (~100,
   typographic outer wrappers around nested wikitables) and
   VERSE_WRAPPER (~37, wikitables wrapping a `<poem>` for
   positioning).  Plus possibly carving more-specific shapes out
   of today's DATA_TABLE / COMPLEX_HTML labels.  Same architectural
   principles.
3. **Plate redistribution** (separate but analogous pipeline):
   `parse_plate.py` → walker/classifier/producer for plate-article
   structural variants.  Shares producers/utilities with elements
   where shapes overlap.  See `[[feedback_pipelines_share_producers]]`.
4. **Family collapse — endgame** (after each family stabilizes):
   collapse the sub-labels of each family behind a single outer
   label (`ICL`, `TABLE`, etc.) with a private sub-pipeline.  The
   outer dispatch and article-level consumer see ~6-7 element
   kinds; sub-shape selection stays internal to each family.
   Tracked as `#25` (ICL collapse) and `#26` (TABLE collapse).
   See `[[feedback_family_sub_pipelines]]` and
   `[[project_icl_family]]`.

**Other open work** (carryover from prior session):

- **Phase B**: restore H1 typography via a `title_html` field rendered at
  export time in Python, emitted alongside plain `title` in the article
  JSON.  Single chokepoint (Python), every JS surface drops `title_html`
  into innerHTML.  No marker contamination, no per-surface helpers.
- **Captioned-figure producer bug — Phase 1** — defer until after the
  next clean rebuild.  Producer-bug pool = STRANDED + BLOCK_LAYOUT +
  float-wrapped refs = **2,226 corpus-wide**.  Adjacency audit
  (`tools/_scratch/audit_caption_patterns.py`) classified the pool by
  position of the nearest caption-shape text (`Fig./Plate/{{sc|Fig}}`):

  | Bucket | Refs | % | Notes |
  |---|---:|---:|---|
  | **GLUED_BR**    | 580 | 26% | `<br>`-glued caption directly after the ref |
  | **PARA_AFTER**  | 158 |  7% | Caption in next paragraph (existing EXTCAP path broken on template-wrapper closers) |
  | **PARA_BEFORE** | 160 |  7% | Caption on line(s) BEFORE the file ref |
  | ELSEWHERE       | 605 | 27% | Caption within 400 chars but not adjacent — mostly figure + wikitable-with-caption-header-row pattern |
  | NONE            | 723 | 33% | No caption-shape detected — mostly maps, chem-formula-as-content, article-start figures |

  **Phase 1 scope:** the first three buckets, 898 refs (40% of pool).
  Extend the IMAGE element's EXTCAP intake to:
    1. Accept `<br>`-glued captions directly after the file ref
       (GLUED_BR).
    2. Fix the existing PARA_AFTER intake so a caption wrapped in a
       template with trailing `}}` (outer-wrapper closer) doesn't
       trip the match regex.
    3. Accept captions on the line(s) immediately before the file ref
       (PARA_BEFORE — new direction).
  Wrapper templates to consume (small fixed set): `{{sc|Fig.}}`,
  `{{Fs|…|…}}`, `{{Fine block|…}}`, `{{EB1911 Fine Print|…}}`,
  `{{center|…}}` / `{{c|…}}`, bare prose `Fig. N.—…`.

  **Phase 2 (separate work):** ELSEWHERE bucket = 605 refs of
  figure-then-wikitable-caption-row patterns.  Either teach the
  wikitable extractor to bind its `|+` row as caption for an adjacent
  preceding figure, or teach IMAGE to look ahead into the next
  wikitable.  Own audit first.

  **Phase 3 (defer indefinitely):** NONE residual = 723 refs.  Mostly
  legitimately captionless.  Article-title-as-caption for maps is a
  separate design question, not a producer fix.

  Per `[[feedback_diagnostic_first_recipe]]`: pre-fix HTML snapshot
  of ~50 known-captioned-figure articles (ACCUMULATOR, BREWING,
  ORDNANCE, STEAM ENGINE, FLUTE, OBOE, CATACOMB, BRACHIOPODA, BOOK
  BINDING, …) BEFORE any code change.  Post-fix diff should show
  changes only on refs the audit classified into one of the three
  Phase 1 buckets; anything else changing is a regression.
- **Fast-mode rebuild_volume actually fast** — defer until after the
  next clean rebuild.  Current "fast" mode (vol 1) takes 174s vs
  production full mode at 180-240s — savings is only ~30s, so fast
  mode doesn't deserve its name.  Two structural fixes land it in a
  meaningfully different speed class:
  1. **UPDATE articles in-place** instead of DELETE+INSERT.  Same
     article rows, new body field.  Saves ~26s of DB wipe overhead.
     Cleanest match for the fast-mode use case (iterating on
     transform/export code without disturbing detected articles).
  2. **Parallelize transform_articles and export_articles_to_json**
     across CPU cores.  Both are per-article-independent.  Saves
     ~80-100s combined (transform 75s → ~10s, export 52s → ~6s on 8
     cores).  Same parallelization helps full mode (classify, xref,
     image, contributor stages all per-article-independent too).
  Combined effect: fast mode ~30-40s, full mode ~60-90s.  The
  "30-90s per volume" claim in `rebuild_volume.py`'s docstring then
  becomes honest.  (Skipping boundary detection on a heuristic was
  considered and rejected — too magical.)
- **rebuild_all.sh viewer-deploy enumeration** — defer.  The deploy
  phase has ~25 individual `aws s3 cp tools/viewer/FOO.html s3://…/FOO.html`
  lines; each new viewer file requires editing the list, and the list
  will silently drift from the actual `tools/viewer/` directory.
  Already caused a near-miss this session — `typeahead.js` would have
  404'd in prod if I hadn't noticed before the deploy phase ran.  Same
  catch-all-by-enumeration anti-pattern; structural fix is a single
  `aws s3 sync tools/viewer/ s3://britannica11.org/` with appropriate
  `--exclude` patterns (mirrors the `data/articles` sync a few lines
  above).  Per `[[feedback_dont_grow_catchalls]]`.
- **Shared viewer page shell** — defer.  Every viewer HTML page
  (`home.html`, `index.html`, `viewer.html`, `contributors.html`,
  `topics.html`, `ancillary.html`, and friends) duplicates its
  `<head>`, the `:root` CSS variable palette, the nav bar, and the
  script-loader IIFE that pulls in `article-urls.js` /
  `search-api.js` / `typeahead.js`.  Every color tweak or nav link
  addition touches N files; drift surfaces as inconsistent styling
  and the kind of "this works on index but not home" bugs the
  typeahead extraction surfaced.  Structural fix: a shared shell —
  either a tiny build-time partial included by every viewer page,
  or a runtime `viewer-shell.js` that injects `<head>` content +
  nav + script tags at load time.  Same anti-pattern as the
  typeahead duplication we just collapsed; same recipe applies.
  Per `[[feedback_dont_grow_catchalls]]`, treat each "add this
  small thing to all N files" diff as a smell.
- **`_transform_text_v2` decomposition** — defer until after the next
  clean rebuild.  Same catch-all anti-pattern as the old `clean_body` /
  `clean_pages`, just at a lower level: ~430 lines of template-name-
  specific preprocessing piled before `process_elements`, plus the
  `_strip_templates` allowlist regex (`IMG:|IMG-INLINE:|TABLE|VERSE:`)
  that grows every time we add a marker.  Recipe: name each pre-pass
  for the structural thing it does (`promote_inline_glyphs` is the
  shape), push template-specific knowledge into the element that owns
  it, drive `_strip_templates`'s catch-all to zero.  See
  `[[feedback_no_catchall_cleanup]]` and
  `[[feedback_dont_grow_catchalls]]`.
- **Contributor-dedup gate — LANDED 2026-05-17.** Shipped as a gate, not
  a fixer (per `[[feedback_db_writes_evaporate]]`).  `dedup_contributors.py`
  gains a `--report` mode (threshold default 0.85, JSON output);
  `aliases.json` gains a `distinct` list for acknowledged-different
  people; `tools/diagnostics/check_dedup_candidates.py` is a new
  pre-deploy gate that filters the report against `aliases` + `distinct`
  and exits 1 on any unreviewed candidate.  Wired as Phase 6g in
  `rebuild_all.sh`.  Current state: 11 raw candidates → 3 covered by
  aliases (collapse on next rebuild) + 8 in distinct → 0 unreviewed.
- **Pre-deploy quality gate** with hard thresholds + a title-shape check
  (`«` in any title → abort) + a (vol, page)-level pair diff against
  baseline.  Currently the quality report runs pre-deploy but doesn't
  block; harden it into a gate.
- **Architectural cleanup**:
  - **Inline-image rendering — LANDED 2026-05-17.**  Source convention
    `[[File:X|14px]]` mid-prose was rendering as a 600px-cap block
    figure, breaking ~337 corpus refs (Hebrew/Phoenician alphabet
    glyphs in vol 1 p774, the article on the letter A's 5 ornamental
    initials, similar inline glyphs scattered across letter articles
    and tag/ornament references).  New
    `elements/_inline_glyphs.py::promote_inline_glyphs` runs as a
    pre-pass to element extraction in `_transform_text_v2` and rewrites
    only the INLINE_GLYPH bucket — refs with no caption, no layout
    keyword, outside any wikitable, and in prose-line context — to a
    new `{{IMG-INLINE:filename|size}}` marker.  The other ~10,000 file
    refs (CAPTIONED 569, BLOCK_LAYOUT 2,631, TABLE_FIGURE 5,431,
    STRANDED 1,128, CHEM_BRACKET 210) continue through their existing
    paths unchanged.  Viewer renders the new marker as a true inline
    `<img>` with `vertical-align:middle` and the source-specified size
    (`Npx`, `xHpx`, `WxHpx`, or 1.2em default).  Routing buckets were
    established by exhaustive corpus audit in
    `tools/_scratch/audit_image_routing.py`.  Catch-all template
    stripper in `body_text.py::_strip_templates` allowlist updated to
    pass `IMG-INLINE:` alongside the existing `IMG:`, `TABLE`,
    `VERSE:`.
  - **8 pre-existing test failures resolved — LANDED 2026-05-17.**  All
    were test-harness bugs, not production bugs.  7 of 8
    (`test_image_layout_unwrap.py::test_*`) called `_transform_text_v2`
    directly on raw wikitext, but production runs `_convert_quote_runs`
    upstream in `prepare_wikitext` first.  Without that pre-pass,
    `'''italic'''` markers stay raw and the legend extractor's
    `_MULTICOL_FULL_ENTRY_ITALIC_RE` regex (which keys on `«I»…«/I»`)
    silently fails — producing the wrong test fixture output even
    though the underlying production articles
    (SPONGES/HYDROMEDUSAE/Abbey) render correctly.  Fix: 12-line
    wrapper in the test file that mirrors the production call shape
    (`_convert_quote_runs` → `_transform_text_v2`).  Zero production
    code changes.  The 8th (`test_fulminic_acid_competing_formulae`)
    was a stale assertion: the test expected `"Langle"` filename
    string preserved, but the chemistry processor has been correctly
    rendering it as the `❮` Unicode glyph for some time — assertion
    updated to match.  Tests: 294 passing, **0 red**.  Diagnosis
    process followed `[[feedback_verify_the_counter]]`: an earlier
    "fix" that mutated `_clean_legend_text` to strip `''` and HTML
    `<i>` tags appeared to fix 6 tests, but verification against
    production showed the affected articles already rendered
    correctly — the change was a test-side mirage with regression
    risk to the working mass.  Reverted, then dug deeper to find the
    real cause (the test harness, not production).
  - **`clean_pages` → `prepare_wikitext` rename — LANDED 2026-05-17.**
    The module/function name `clean_pages` was a holdover from when
    the stage did 13 different cleanup ops; after today's tightening
    it does exactly two things — `apply_corrections` + quote-run
    conversion — and "cleans" nothing in any general sense.  Renamed
    file `src/britannica/pipeline/stages/clean_pages.py` →
    `prepare_wikitext.py`, function `clean_pages(volume)` →
    `prepare_wikitext(volume)`, CLI command `britannica clean-pages`
    → `britannica prepare-wikitext`.  Updated all imports (CLI,
    transform_articles comments, body_text comments, corrections
    module docstring, img_float docstring, reprocess_article), all
    11 test files that imported `_convert_quote_runs`, renamed
    integration-test file `test_page_cleanup_pipeline.py` →
    `test_prepare_wikitext.py`, and updated the two active shell
    scripts (`tools/rebuild_all.sh`, `tools/db/rebuild_volume.sh`).
    Tests: 286 passing, same 8 pre-existing reds.  Disposable
    `tools/_scratch/*.sh` left untouched.  Earlier LANDED entries
    in this file still reference `clean_pages` to describe the
    pre-rename state accurately.
  - **SCORE → content-addressable element — LANDED 2026-05-17.**
    `<score>` handling lived as a pre-extraction pass in
    `clean_pages.py` (then briefly in `elements/_score.py`) because
    `SCORE_IMAGES` was keyed by `(volume, page, occurrence_index)` —
    treating SCORE as a positional element.  But the upstream Commons
    URL is a content-hash of the LilyPond source, not position-based;
    the keying was an implementation choice, not an architectural
    necessity.  Rekeyed all 11 entries by whitespace-normalized
    LilyPond content; `_leaf._process_score` now does a single dict
    lookup like `_process_math` and is reached as a normal post-extract
    element handler.  Deleted: `elements/_score.py`,
    `_replace_score_tags` entirely (it was the pre-extraction pass),
    `SCORE_TAG` regex from `image_assets.py`, the pre-extract
    registration in `_ELEMENT_HANDLERS`, the call site in
    `transform_articles/__init__.py:497`.  Smoke-tested: all 8 score
    tags across vol 3 p221 + vol 6 p416 resolve to their original
    URLs.  Tests: 286 passing, same 8 pre-existing reds.
  - **Editorial Preface → source-regenerated static HTML, full
    ancillary decoupling — LANDED 2026-05-17.**  New build script
    `tools/viewer/build_preface.py` reads vol 1 ws pages 10-23
    `raw_text` (not `cleaned_preview` — see below), applies
    `corrections.json`, converts wikitext to static HTML, writes
    `tools/viewer/preface.html`.  Joins all four ancillary builders
    in Phase 6d of `rebuild_all.sh` (`build_about_page.py`,
    `build_ancillary_pages.py`, `build_preface.py`).  Mirrors the
    article pipeline's marker semantics so output matches what the
    JS renderer would have produced if its input were correct.

    **Bugs fixed vs the old `export_front_matter.py` → JS path:**
    * **Wrong content range.**  The old export read pp.6-23 corpus-
      wide and glued the Prefatory Note (pp.6-9) onto the Editorial
      Introduction (pp.10-23).  Production has been showing both
      stuck together for the entire site's history.  New build reads
      pp.10-23 only; Prefatory Note stays in
      `ancillary-prefatory-note.html`.
    * **Missing opening sentence.**  The print's first paragraph
      begins "In the Prefatory Note the history of the production
      of the successive editions of the Encyclopædia Britannica has
      been briefly told; and elsewhere in these volumes…" but the
      Wikisource transcription drops this clause and starts at
      "Elsewhere…".  Confirmed against live Wikisource — same gap
      there.  Patched via `corrections.json` `"1:10"` (adds the
      missing clause, rebases the drop-cap from "E" to "I").
    * **Lost footnotes.**  The old path read `cleaned_preview`
      which captured only some `<ref>…</ref>` tags.  Building from
      `raw_text` keeps both footnotes intact.  Wired the same
      `id="fnref-N"` / `scrollIntoView` back-navigation the article
      viewer uses so footnote-list clicks return to the in-body
      anchor.
    * **Bold-italic shoulders.**  The old `cleaned_preview` stripped
      `'''` bold markers from SH content (italic-only via CSS); the
      raw-text build was emitting `<b>` inside `<span class=
      "shoulder-heading">`.  Now strips B markers to match.
    * **Lost spaces, mid-word soft hyphens, em-space entities,
      double periods, SH-broken paragraph flow** — each fixed; mirror
      the JS / fetch-pipeline transformations precisely (HTML space
      entities → space; `<br>` → space; `- ` removal joins
      soft-hyphenated words; SH content in margin via paragraph-
      merge so prose flows continuously around it).
    * **Wikilinks rendered.**  `[[w:X|Y]]` → Wikipedia anchor,
      `[[Author:X|Y]]` → `/contributors.html?q=Y`.  Production's
      `cleaned_preview` stripped these to plain text; restored as
      proper clickable links.

    **Decoupling work:**
    Deleted `tools/pipeline/export_front_matter.py`,
    `clean_for_front_matter`, the `clean_pages` compatibility
    orchestrator, the `cleaned_text` column from `SourcePage`, the
    Phase 5 export step from `rebuild_all.sh`, the dead
    `dedication.body` export, `cleaned_text=None` initialisers in
    the CLI / importer / test conftest, and the obsolete
    `test_page_cleanup_pipeline` assertions (replaced with a
    quote-run-conversion check on `wikitext`).  `clean_pages.py` is
    now ~180 lines doing one job: typo corrections + quote-run
    conversion on `page.wikitext`.  Tests: 286 passing, same 8
    pre-existing reds.  Production stays broken until the new
    `preface.html` is uploaded on the next deploy.  Follow-up: drop
    orphan `cleaned_text` column from local DB with
    `ALTER TABLE source_pages DROP COLUMN cleaned_text;` when
    convenient.
  - **`clean_pages` split — LANDED 2026-05-17.**  Replaced the 539-line
    catch-all with two narrow public entries.  `clean_for_articles`
    (~10 lines) does only typo corrections + quote-run conversion on
    `page.wikitext`.  `clean_for_front_matter` (~14 lines) does the
    six prose-cleanup ops (unicode, print artifacts, headers,
    hyphenation, reflow, whitespace) on `page.cleaned_text` consumed
    by `export_front_matter.py`.  `clean_pages` is now a compatibility
    orchestrator calling both.  Deleted ~280 lines of article-shaped
    catch-alls from the front-matter path (`_clean_plate_layout`,
    `_convert_img_float`, `_clean_leaked_table_markup`,
    `_fix_unclosed_footnotes`, `_fix_unclosed_tables`, plus
    stray-control-char / residual-`''` substitutions).  Audit verified
    these produced IDENTICAL output on the 19 pages
    `export_front_matter.py` actually consumes (Vol 1 pp.5-23 —
    dedication + editorial preface) — they were dead weight running
    against article-pipeline data the front-matter export never reads.
    Tests: 286 passing (same 8 pre-existing reds).  Idempotency check
    on Vol 1: 1028/1029 pages byte-identical when rerun (the 1 diff
    is a pre-existing quirk in `_convert_quote_runs`).
  - Decompose `detect_boundaries.py` (~900 lines): letter-article handler,
    bold extractor, glue check, fallback path → each its own module
    with focused tests.
- **Inline images rendered as block** — corpus-wide bug.  Source has
  `[[File:foo.svg|14px]]` mid-prose (letter articles use these for
  variant glyphs of A/B/C in Phoenician, Greek, Latin scripts; ARENIG
  GROUP and similar use them for taxonomic ornament).  Pipeline strips
  the size hint (`_image.py:34` skips `\d+px` parts) and wraps the
  resulting `{{IMG:fn}}` with `\n\n`, turning inline images into
  standalone block-level images at default size.  Fix is multi-file:
  preserve size in `_process_image` (and the ~10 other IMG-emit sites
  in `_layout.py`/`_tables.py`/etc.); extend marker schema to
  `{{IMG[size=14px]:fn|caption}}` mirroring `«MATH[fs=N]:`; stop the
  `\n\n` framing for inline images; teach the viewer to render the
  size-hinted form inline.

- **Letter-article simplification — LANDED 2026-05-17**.  Replaced
  ~70 lines of brace-walker + body-keyword check with ~25 lines of
  regex + brace-aware helper.  Validated 26/26 on corpus (one per
  letter A–Z), zero false positives.  See
  `tools/_scratch/verify_letter_articles_simplified.py`.

- **Missing-image audit honest + djvu refs normalized — LANDED 2026-05-17**.
  `find_missing_images.py` reported 14 misses but 10 were `EB1911 -
  Volume N.djvu/NNN` page-leaf refs whose canonical local form
  (`djvu_volNN_pagePPPP.jpg`) was already on disk — the audit just
  didn't apply the djvu normalization that `transform_articles` does
  to article bodies.  Two fixes: audit imports `_normalize_djvu_page_refs`
  before checking on-disk (14 → 4); `extract_images.py::_parse_image_ref`
  and `_parse_img_float` normalize before storing so `images[*].filename`
  matches what's on disk and what body markers already say.  Remaining
  4 were genuine Commons files never fetched on the last
  `download_images.py` run; all 4 downloaded locally (will reach S3 on
  next deploy).  Audit now reports 0.

---

## Known issues (open)

- **Bare-label legend bundling** — SPINAL CORD (vol 25 Fig 3) / MALLOW (vol 17
  5-part botanical legend).  Single-bare-label paragraphs render as body prose;
  needs a figure-pass that collects consecutive single-entry paragraphs.
  Styling, not content loss.
- **Legend extraction sub-patterns — refactored 2026-05-19 under
  LEGENDED_FIGURE / LEGENDED_FIGURE_CHILD.**  The figure-shape
  redistribution moved multicol + prose-cell legend extraction into
  focused producers using a shared `_chop_legend_entries(text,
  delimiter, …)` helper and column-major continuation via
  `_parse_multicol_legend_rows_column_major`.  Canonical cases
  (ARACHNIDA Figs 7, 12, 14, 47, 54, 65; ABBEY Fig 5) clean.
  Remaining sub-patterns:
    * **`rowspan=N` continuation cells** (ARACHNIDA Fig 31) — col-1
      cell spans 2 rows of col-0; rowspan row has only one source
      cell so legend parsing terminates early.  Need rowspan-aware
      row expansion before column-major build.
    * **Prime-marked labels** (`7′`, `I′ to V′` — ARACHNIDA Fig 47)
      — `_MULTICOL_FULL_ENTRY_RE` doesn't accept prime characters
      in the label, so labelled-with-prime cells get folded into
      the prior entry.  Extend label regex to include `′″‴` etc.
    * **`{{hi|…}}`-wrapped same-line legend** (ARACHNIDA Fig 3, 26,
      73, 78) — legend packed into one cell as a sequence of
      `{{hi|1em|…}}` templates separated by `<br>`, all on one
      line.  Tracked as queued task — may warrant a new
      `LEGENDED_FIGURE_INLINE` label.
    * **Side-by-side image cells losing caption + legend** (ARACHNIDA
      Figs 57–58, BAG-PIPE vol 3 p221) — two figures in a 2-column
      wikitable, each cell containing `[[File:…]]` (or `<score>`) +
      caption + `<br>`-stacked legend; pipeline lifts the IMG markers
      but drops the cell text and leaks the TABLE marker.  Distinct
      extraction-time issue (likely a CAPTIONED_FIGURE_GRID gap
      since it has the right shape but cell-content extraction
      doesn't see captions properly).
- **Fig 7 editorial note in trailing PRE** — a wikitable that follows the
  figure containing an editorial annotation `[According to the system…]`
  classifies as PRE; the figure walker doesn't recurse into PRE for an
  enclosed credit line.  Both an extraction-time classification miss
  (the trailing wikitable's actual structure is annotation + credit)
  and a walker miss.
- **BRITISH EMPIRE India-acquisitions table** — multi-line cell continuation
  + `|+` caption attribute leak; separate single-article residual.
- **`{{c|…}}` Roman-numeral subsections** (24 articles) — flatten to inline
  prose; no clean single-block distinguisher, only Roman-numeral progression
  across blocks.
- **Tall-brace taxonomic grouping** — print-typographic device using a tall
  `\left\{ \begin{matrix} \\ \end{matrix} \right .` (no math content, pure
  ornament) to group preceding-or-following items as members of a single
  category.  Two encodings in source:
    * **Brace inline in prose** (ARACHNIDA Eurypteromorpha sub-orders;
      scorpion families with Carboniferous bracket; ATMOSPHERIC ELECTRICITY)
      — renders as a stray vertical brace splitting the surrounding prose.
    * **Wikitable with rowspan + brace cells** (ARENIG GROUP — geological
      taxonomy of Ordovician sub-divisions) — multi-row wikitable using
      `rowspan="N"` to group items, brace-`<math>` cells as visual
      depth indicator.  Routes today to `COMPLEX_HTML` (correctly — it's
      not a figure) but renders as a verbatim HTML table, losing the
      hierarchy.

  ~8 instances corpus-wide between both encodings.  Real fix under the
  new walker/classifier/producer architecture: add a `TAXONOMY` (or
  `OUTLINE_FROM_TABLE`) classifier predicate that recognises the brace-
  decoration pattern + rowspan grouping, plus a focused producer that
  emits an `«OUTLINE:…«/OUTLINE»` marker.  The outline renderer is
  general-purpose and we underexploit it; this is one of several
  patterns that ought to route there.  Figure-shape redistribution
  has now landed (2026-05-19) — TAXONOMY is the next non-figure carve
  campaign queued for the architecture.
- **IMG-caption credit-glue missing space** — when a figure's descriptive
  caption and its `(From …)` credit live in the same source cell separated
  only by structural markup that gets stripped (`{{center|{{Fs|N%|…}}}}`,
  `<br>`, etc.), the IMG caption emerges with `).(From X)` — no space at
  the join.  Sample: ARACHNIDA Figs 13, 63, 74.  Narrow extraction-time
  fix: normalise `.(` → `. (` when assembling the caption (in
  `clean_caption` or the caption-build path of the layout subclasses).
- **Single-image-figure edge cases (~50)** — LAYOUT_WRAPPER residual
  with `images=1` after the 2026-05-19 figure-shape redistribution.
  Each is a figure that should have matched
  `CAPTIONED_FIGURE` / `CAPTIONED_FIGURE_INLINE` / `LEGENDED_FIGURE` /
  `LEGENDED_FIGURE_CHILD` but didn't — likely predicate gaps rather
  than missing labels.  Investigate by sampling per-bucket in
  `tools/_scratch/figure_layouts_audit.md`; fixes here improve the
  existing focused producers (especially the 51%-dominant
  CAPTIONED_FIGURE) rather than adding new ones.
- **Italic-marker inversion (residual)** — pre-existing class.  Post-Phase-A
  `stray_wiki_italic` counter is at 15 (vs baseline 2 on 2026-05-14, and a
  catastrophic 2,159 on the broken 2026-05-16 V2 deploy).  Ref-internal
  italics fixed today; the remaining 15 are the unfixed pre-existing edge
  cases in the 5-quote bold-italic handler.
- **8 unit-test failures** = 8 documented production bugs:
  - 7× `test_image_layout_unwrap.py` — the legend-extraction sub-patterns
    listed above (rowspan, prime marks, hanging-indent `{{Hi}}`,
    side-by-side image cells, sponges/hydromedusae figures).
  - 1× `test_elements.py::test_fulminic_acid_competing_formulae` —
    chemistry-layout doesn't emit `«CHEM:` marker for the
    competing-formulae 2-D table shape.
- **Contributor duplicates (1 visible, 2 invisible)** — Abbott pair
  visible on contributors page; Fyfe + Stockman pairs have one orphan side
  filtered out of the contributors page.  All three queued for merge via
  `data/contributor_aliases.json` on next rebuild.
- **Lower priority:** ~7 unlinked contributors after Phase 3b2 (down from
  ~88 in yesterday's broken deploy); ~3,633 unproofread Wikisource pages;
  Meilisearch port 7700 open to all (should be CloudFront-only).

See `docs/reports/` for historical audit snapshots.

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

Extract-process-reassemble per segment (`pipeline/stages/elements/` +
`transform_articles/_transform_text_v2`):

1. Wiki tables (balanced matching) → HTML elements (ref, html_table, poem,
   math, score) → wiki markup (image_float, image).
2. Each element processed recursively.
3. Body text transforms (~11 explicit functions: hieroglyphs, links, content
   templates, small caps, shoulder headings, layout templates, sub/sup,
   bold/italic, strip templates, strip HTML, decode entities).
4. Reassembly with `\x01PAGE:N\x01` markers.

### Marker formats (internal)

| Marker | Meaning |
|---|---|
| `«B» / «I» / «SC»` | Bold / italic / small caps |
| `«LN:filename\|target\|display«/LN»` | Resolved link |
| `«LN:target\|display«/LN»` | Unresolved link (falls back to search) |
| `«MATH:…«/MATH»` | LaTeX, plain |
| `«MATH[fs=N]:…«/MATH»` | LaTeX, render at N% font-size |
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
math measurement).  pytest (265 tests).

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
   first-content pages; 6d. rebuild generated site pages; 6e. build Reader's
   Guide.
7. Deploy (S3 sync articles + images + scans + JSON + viewer; CloudFront
   invalidate; index search on EC2).
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

## Topics page (Vol 29 classified TOC)

Category-bounded OCR (`tools/ocr_vol29_classified.py`) +  two-phase walker
(`tools/parse_classified_toc.py`).  23,050 articles across 24 categories.
Per-cat refinement: edit `data/derived/cat_ocr/<slug>.txt` or rerun
`ocr_vol29_classified.py --only='<Cat>'`.  Ambiguity disambiguation via
Haiku batch (`tools/vol29/disambiguate_toc.py`), cached.

---

## File / directory conventions

- `tools/_scratch/` — disposable.  Promote keepers to `tools/diagnostics/`
  with a real name and docstring.
- `data/corrections.json` — source-text typos by `vol:page`; never edit raw
  wikisource page JSONs directly.
- `docs/reports/` — dated snapshot audit reports.
- `docs/status.md` — this file.  Source of truth for current state.

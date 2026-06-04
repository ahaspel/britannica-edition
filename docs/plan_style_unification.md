# Plan: Unify style handling — one place, style-blind decomposers

**Goal (owner):** "Unify style handling — ONE place, across the board — and eliminate
everything else that attempts to deal with it." And: "decompose_figure and
decompose_table shouldn't even KNOW from styles."

**Principle:** style is orthogonal to structure. A styled wrapper carries its
style as a marker and recurses its *content* through the ONE classifier/producer
dispatch — regardless of what it encloses (table / MATH / CHEM / figure / prose /
nested wrapper). Structure decomposers are style-blind.

**Motivating bug:** `render_markers('<p {{Ts|ac}}><math>x^2+1</math></p>')` →
`«CTR»<math>…</math>«/CTR»` — the `<math>` leaks raw because `decompose`
(`_figure_faithful.py`) is a SECOND, PARTIAL classifier knowing ~6 shapes. The
main dispatch knows everything.

## Key enabling fact
The shared recursive dispatch ALREADY exists: `process_elements(inner, tt, ctx,
_allow_figure=False)` — the main `walk`→`classify`→`produce_tree` path, already
called recursively (`_ref.py:122`), already recognizes MATH/CHEM/TABLE/figure/
POEM/nested-STYLED at every depth, already assembles by placeholder substitution.
So `decompose` COLLAPSES INTO `process_elements`; no new mechanism.

## Sites to ELIMINATE / fold (confirmed)
- `_figure_faithful.py`: `_STYLE_WRAPPERS`, `_STYLE_OPENER_RE`, `_style_marker`,
  `_style_tmpl_marker`, `_div_block_marker`(+`_DIV_OPEN_RE`), `decompose`/
  `render_markers`, `_wiki_table_marker`/`_html_table_marker`/`_figtable_table_style`/
  `_html_figtable_style`/`_cell_marker`/`_rows_to_htmltable`/`_mask_nested`/`_match*`.
- `body_text.py` (`_apply_markup`/`_unwrap_content_templates`): `_ts_block`,
  `_p_ts` (DROPS images — defect), `_div_ts`, `_span_ts`, `_carry_style_spans`,
  `_handle_title_spans` (keep transliteration semantic), `csc` branch +
  `_CENTER_INLINE_TEMPLATES`.
- `_walker.py`: `_STYLED_DIV_RE` + styled-`<div>`→SHAPE_FIGURE gate. (Keep
  `_BALANCED_TAGS` `div`; extend to `p`/`span` if wrappers.)
- `_shapes.py`: MIRROR_GLYPH outer-`<span style>` strip (161) → derive via style layer.
- `_table_decompose.py`: `extract_wiki_rows`/`produce_cell` already carry RAW `attr`
  (opaque) — keep; make `_cell_styles` the SOLE `attr`→CSS caller.

## The ONE place to KEEP (the style core)
`_tables.py`: `_parse_ts_codes`, `_table_opener_styles`, `_cell_styles`,
`styled_marker(tag,css,body)`, `emit_html_cell`. Viewer decoders (`«DIV[style]»`,
`«SPAN[style]»`, `«SPAN[title]»`, `«CTR»`, `«SC»`, `«MIRROR»`) are pure — no change.

## Design
- **SHAPE_STYLED** (new): one recognizer for template-form (`{{center}}`/`{{csc}}`/
  `{{c}}`/`{{Ts}}`) AND HTML-form (`<div>`/`<p>`/`<span>` carrying `{{Ts}}`/`style=`/
  `align=`) wrappers. Structure-only recognition (presence of a style attr); raw
  bytes pass through. SHAPE_CENTER/MIRROR_GLYPH stay distinct shapes, same label+producer.
- **`_process_styled`** (one producer): peel wrapper → CSS via existing
  `_cell_styles`/`_table_opener_styles`/`_parse_ts_codes` → recurse inner via
  `process_elements(..., _allow_figure=False)` → wrap via `styled_marker` (`«DIV»`/
  `«SPAN»`), or `«CTR»` (pure center, byte-identical special case) / `«SC»` (csc).
- **Per-cell styles:** decomposer carries opaque raw `attr` (already true);
  `_cell_styles` is the single translator on the producer side. "decompose_table
  doesn't KNOW from styles" satisfied.

## Sequencing (suite green between steps)
0. Baselines: label-distribution `before`, `ts_audit scan` (35 leaks/14 arts), full suite green.
1. Add `_process_styled` consolidating `_ts_block`+`styled_marker`+`_div_block_marker`+
   `_style_marker`; NOT wired. Byte-identity unit test vs today's outputs.
2. Wire SHAPE_STYLED for HTML wrappers (`<div>`/`<p>`/`<span>`); delete `_p_ts`/
   `_div_ts`/`_span_ts`/`_carry_style_spans` SAME commit. (Fixes `_p_ts` image drop.)
   Label diff: only BODY/FIGURE→STYLED. `ts_audit`: `<p>`/`<div>`/`<span>` rows → 0.
3. Route template wrappers (`{{center}}`/`{{csc}}`/`{{c}}`) + SHAPE_CENTER/MIRROR to
   `_process_styled`; delete `_STYLE_WRAPPERS`/`_style_tmpl_marker`/`_style_marker`/csc branch.
4. + 5. Make decomposers style-blind AND collapse `decompose`→`process_elements`
   (together — Step 4 removes faithful's own table branch). `produce_faithful_figure`
   becomes `process_elements(raw, tt, ctx, _allow_figure=False)`; register image leaves
   in `_PRODUCER_DISPATCH`. **Gate hardest here.**
6. Clean full rebuild = static checkpoint; confirm no raw `<math>`/`{{Ts}}`/`<p>`/`<div>`.

## Regression net (every step)
Snapshot suite (21 seeds) · realdata unit tests + test_abbey/blank_verse/alloys ·
label-distribution diff (transitions only as expected; never MATH→BODY) ·
content-loss-vs-source · `ts_audit` delta (styled classes → 0) · full `pytest tests/`.

## Top risks (ranked)
1. **Figure-internal table styling** — faithful `_figtable_table_style` (align=right→float,
   bare width) vs `_process_table_unified`. Step 5 may shift figure-table render; keep a
   thin figtable-style shim if the diff regresses.
2. **`\n\n` block-spacing** — `decompose` joins blocks with `\n\n`; `process_elements`
   substitutes placeholders. Caption-after-image margins may change; measure via snapshots.
3. **`csc`/`«CTR»` byte-identity** — reproduce `_ts_block`'s pure-center→`«CTR»`, csc→
   `«CTR»«SC»` ladder exactly (Step-1 byte-identity test).
4. **MIRROR_GLYPH** — keep mirror its own marker; don't carry `{{mirrorH}}` as real CSS.

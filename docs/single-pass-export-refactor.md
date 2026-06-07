# Single-pass export: drop `transform_articles`, the export owns the walk

## One line
Collapse the article pipeline from a chain that flattens the tree to a string
and then repeatedly reparses it, into **two stages**: *detect* (corpus metadata)
and *assemble* (one walk that resolves, assembles, and writes). `transform_articles`,
`extract_xrefs`, `resolve_xrefs`, and the export's reparse all disappear;
`Article.body` stops being materialized.

## Why
`transform_articles` is `process_elements` + a DB write — it materializes the
*flattened* tree as `Article.body`, and that flattening is the sole reason every
downstream stage reparses. The xref pass is the keystone: it is *why* the body is
stored (so a later, inter-volume resolve can re-read it), why resolution is split
intra/inter, why the export rebuilds `link_targets`. Remove the stored body and
resolve in one pass, and the rest doesn't get fixed — it loses its reason to exist.

Reads are cheap and idempotent; what's expensive is materializing/mutating to
*avoid* a re-read, because that's what couples the stages. This refactor deletes
the read-once-and-mutate, and pays cheap re-reads for full decoupling.

## End-state architecture

### Stage 1 — detect (corpus metadata)
`detect_boundaries` (the honest `super_walker`) runs over every volume — it already
does. It carves articles and, in passing, records each `Article.title` + span. From
those titles, build the corpus-wide **title→filename index**. This is a light
boundary scan, **not** a `process_elements` walk, built from rows that already
exist — no body is touched. Pre-render disambiguation openings for the small set of
**colliding** titles only (a tiny walk of just those articles).

- **Change from today:** `detect_boundaries` records the plain title but **stops
  yanking it** — the title stays in the article span so Stage 2 can recognize it as
  an element. (The plain title is the *partition* read for identity; the marked-up
  title is the *produce* read in Stage 2. Same heading, twice, cheaply — the price
  of the title being an element instead of a yanked field.)

### Stage 2 — assemble (one walk)
Per article: `process_elements(raw)` → tree (held only for this article's turn,
then dropped) → read off the tree and assemble:
- resolve each `«LN»` on the fly against the title index (unambiguous straight off
  it; colliders against the pre-rendered openings); record the edge as the
  CrossReference byproduct;
- the **TITLE element** → `title_display` (marked-up);
- body, sections, page numbers, word count; byline + images + plates from the
  metadata tables;
- write the JSON record.

Backlinks (referenced-by) are a cheap aggregation of the recorded forward-edges,
applied after the pass.

**Held state:** title index + collider openings — tens of MB, metadata-scale.
**Never** the trees: one tree resident at a time.

**No `Article.body`.** The shipped artifact is the JSON `"body"`. Nothing outside
the pipeline reads `Article.body` except ~5 diagnostic tools (no Meilisearch-from-DB,
no viewer backend — confirmed), which reroute to shadow-compute or read the JSON.

## What disappears
- `transform_articles` → folded into the Stage-2 walk.
- `extract_xrefs` + `resolve_xrefs` + the intra/inter split → on-the-fly resolution
  during assembly.
- `classify_articles` → a tree check (empty? plate?) during assembly.
- the export's `«LN»` / `\x01PAGE` reparse → reads off the tree.
- the title yank + the separate `title_display` walk → the TITLE element in the tree.
- `Article.body` the field.

## The title-fold (in this plan)
Pieces already exist — `super_walker.py` (honest boundary, 0 misses) and
`elements/_title.py` (the TITLE producer). This is **wiring**, not building:
- `detect_boundaries` → `super_walker`: set the boundary, record the plain title,
  leave the title in the span;
- the walk recognizes the TITLE element (first element of the article);
- the export reads it → `title_display`.

## Contributors — deferred (the deliberate follow-on)
Not in this plan, for a real reason: the byline is assembled from the contributor
*tables*, not from walking the body, so deferring it forces no second walk — only
`strip_attributions` stays, as a strip. And contributors feed more than the byline
(the contributors page, the bios), so they are their own arc.

## Staged, verifiable rollout
The shipped artifact is the JSON; **every stage is proven by comparing the JSON
corpus before/after.** (Extend `verify_refactor.py`'s shadow-body comparison to
whole-JSON.)

- **A — Expose the tree.** `process_elements` returns the tree alongside the body
  string. Purely additive; body unchanged → `walker_snapshot` 0/36,691, the same net
  as the page fold.
- **B — Shadow the single-pass export.** Build the walk-once export beside the live
  pipeline: index from metadata, on-the-fly resolve, assemble JSON. Diff its JSON
  field-by-field against the current export's until identical. This is where
  transform/extract/resolve/classify become tree-reads, checked against ground truth
  at every step.
- **C — Title-fold.** Switch detection to `super_walker` (no yank); recognize the
  TITLE element; export reads it. Prove `body` (title still out of the prose) and
  `title_display` in the JSON are unchanged.
- **D — Cut over.** The single-pass export replaces the four stages; drop
  `Article.body`; reroute the ~5 tools; fix `cli/main`'s order. Final proof: JSON
  corpus identical to pre-refactor, modulo intended diffs.

## Things to prove (not assume)
- On-the-fly resolution == the current CrossReference-based resolution (JSON
  link-wrapping identical).
- Collider disambiguation == `resolve_xrefs` (same target picked).
- Backlink aggregation == the current CrossReference graph.
- Held state stays metadata-scale (no accidental tree-holding); one tree resident.
- The ~5 tools rerouted off `Article.body` (verify_refactor, disambiguate_xrefs,
  resolve_unresolved, link_vol29_articles, xref_coverage_audit).

## Settled decisions
Drop `Article.body`. Trees transient (no hold). Corpus single-pass (not per-volume).
Title demoted to an element (this plan). Contributors deferred. Verification moves
to the JSON output.

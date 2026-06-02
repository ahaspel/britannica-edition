# Britannica Edition — Status

**Last updated:** 2026-06-01.  Single source of truth for project state.  Snapshot
audit reports live in `docs/reports/`; long-form per-topic notes live in the
agent's memory directory and are not duplicated here.

> **THE CAMPAIGN (2026-06-01):** the recursive architecture works; the bugs are
> old scaffolding still running beside it.  The good path is written down in
> **[`docs/canonical_path.md`](canonical_path.md)** — the few steps that build an
> article/plate properly.  Everything outside it has to go (catch-all
> `_strip_templates`, 16 fake-recursion regexes, the legacy `parsers/plate/`).
> Measure: `strip_scan.py` / `fake_recursion_audit.py` → 0, then delete.

---

## PROGRESS (2026-06-02) — catch-all content-loss drain: prioritize HARM over count; MAP figures recovered

Full-corpus `strip_scan` worklist (553 deletions / 87 families) reframed by **harm,
not count**.  Key finding: most families are NOT content-loss classes — they have a
working handler and the catch-all only sees a tiny **leak-tail** (`{{eb1911 article
link}}` 9942 handled → 10 leak; `{{11link}}` 476 → 6; `{{dual line}}` 113 → 5).  Those
are queue-the-tail per [[feedback_structure_before_tail]].  The genuine **no-handler
content loss is tiny and localized**:

- **`{{Plain image with caption}}` — MAP (vol 17), ~16 figures — DONE 2026-06-02.**
  Standard Wikisource named-param figure macro the walker didn't recognize → MAP's
  cartography plates fell to body-text's catch-all and vanished.  Added to the image-
  template family beside `{{img float}}`/`{{raw image}}`: walker `_PLAIN_IMAGE_RE`
  recognizer (DOUBLE_BRACE), classifier `PLAIN_IMAGE` label, `_process_plain_image`
  producer (parses `image=`/`align=`/`width=`/`caption=` → `{{IMG:…}}`).  **CRITICAL:
  a recognizer is INERT unless its template name is also in the walker's
  `_OPENER_HINT_RE`** (the gate deciding which positions the scan examines).  The first
  commit omitted that line, so the fix did nothing — caught only because the verify was
  non-discriminating (see [[feedback_verify_the_counter]]).  Now genuinely verified:
  `Map Fig 1.png` + `Peutinger` caption present, IMG 46→62.  Guardrail added
  (`test_double_brace_template_is_recognized`) so an opener-hint omission fails CI.
- **`{{ppoem}}` — 7/8 articles, verse recovered as VERSE — DONE 2026-06-02.**
  Preformatted-poem template, verse analog of `<poem>`; the catch-all was deleting the
  whole `{{ppoem|…}}` (verse lost).  Walker `_PPOEM_RE` (DOUBLE_BRACE) + `PPOEM` label +
  `_process_ppoem` (strips `start=`/`end=` control params, takes the verse, routes
  through the same `{{VERSE:…}VERSE}` producer as `<poem>`).  Verified discriminatingly
  (verse text present AND inside a VERSE block), keyed on the ppoem-bearing article_id.
  **QUEUED: HOOD (vol 13)** — its ` {fine}` stray single-brace (OCR for `{{fine}}`?)
  breaks the bounded-nesting regex; verse survives as text but not as VERSE.  Fix later
  via corrections.json or a balanced-brace scanner recognizer.
- **2 genealogical trees — QUEUED (asset-blocked).** `{{familytree}}` COWPER, WILLIAM
  (vol 7 p369); `{{tree chart}}` SOLOMON, PSALMS OF (vol 25 p382).  Chart2's exact
  siblings → chart2 playbook (manual crop → `CHART2_IMAGES`-style substitution).  Needs
  the user to crop 2 scans before the substitution can be wired.
- **2 margin notes — TODO.** `{{EB9 Margin Note|…}}` VARIATIONS / VARIATIONS, CALCULUS OF
  (vol 27 p941).  Small; needs a render decision (aside vs inline).
- **~8 poems (`{{ppoem}}`), 3-4 format wrappers (`{{font-variant normal}}`, `{{nobold}}`)
  — TODO**, small.
- **`{{Ts}}` (287) — LAST.** Biggest by count but STYLE, and the table/layout producers
  already discard it; the 287 are leftovers their own strips miss.  No content loss →
  lowest harm.  Drain belongs to the table-family work ([[project_table_family_status]]).

### Test-suite green-up + snapshot rebaseline (2026-06-02)

Full suite went 41-fail → 0-fail.  ALL 41 were stale TEST scaffolding lagging the
committed FLIP (preprocess + super_detect + reflow-deletion), NOT production bugs:

- **18 abbey/alloys/blank_verse (KeyError):** regression conftest patched
  `SessionLocal` on 3 modules but not `super_walker` — post-FLIP `detect_boundaries`
  delegates the stream/heading walk there, so the walk read the wrong DB.  Fixed:
  patch `super_walker.SessionLocal` too.
- **9 integration (AttributeError):** `detect_boundaries(volume)` moved to
  `super_detect`; tests still called it on the old module.  Fixed: new
  `tests/integration/conftest.py` autouse fixture patches super_detect+super_walker
  session; call sites → `super_detect.detect_boundaries`.
- **1 realdata (`<noinclude>` survives):** the `_transform` test helper didn't run
  `preprocess` (which now strips noinclude upstream).  Fixed: helper mirrors prod
  (`preprocess(_convert_quote_runs(raw))`).
- **2 unit (`test_shapes` count 12→13, `test_producer_boundaries`):** SHAPES grew by
  `SHAPE_CENTER`; `_figure_decompose` is a genuine producer module (cleans the figure
  caption/legend content it extracts) → registered in PRODUCER_MODULES.
- **20 transform snapshots:** the committed reflow/seam-deletion footprint.  Verified
  render-neutral BEFORE rebaselining (per [[feedback_no_wholesale_rebaseline]]): a
  faithful viewer-model triage classified every paragraph-structure change as
  TERMINATOR (genuine boundary the deleted reflow had wrongly MERGED → improvement)
  or BLOCK (display-block separation the viewer normalizes anyway) — **0 mid-sentence
  page-seam splits, 0 regressions**.  Then synced the stale capture tool
  (`capture_transform_snapshots.py`): faithful `"".join` re-join (was `"\n".join`) +
  stable_id lookup (was the reassigned PK), and re-captured all 20.

Triage tooling: `tools/_scratch/triage_snapshots.py` (render-neutral classifier),
`classify_breaks.py` (per-junction TERMINATOR/BLOCK/MID-SENT).

## PROGRESS (2026-05-31, latest) — THE FLIP, started: net up, fraction step landed; runway corrected

The flip is underway, and grounding in the live code corrected the plan materially.

**ARCHITECTURE CORRECTION (supersedes the 2026-05-30 step-3 framing below).** The recursive
`walker → classify_article → produce_tree → substitute_top_level_markers` spine is **already live
and is the ONLY architecture** — the legacy three-pass (`_walk_recursive`/`_classify_recursive`/
`_produce_recursive`) is gone (a stale docstring sentence in `_classifier.py` is its only trace).
`produce_tree` **IS** `render()` — a recursive bottom-up pass. So the flip is NOT "build render(),
wire it in, delete the classifier / `ClassifiedElement` / SHAPE layer" — `ClassifiedElement` and the
recursive classify ARE the live spine, not the thing being deleted. The flip reduces to folding the
last LAYERED constructs into the spine that's already running:
  1. **Kill the fake recursion** — the two `for _ in range(8)` loops in `body_text.py` (fraction
     family; the general inline-template unwrap). [STEP 1a DONE — fractions.]
  2. **`/s`-`/e` overlap** → recognize the delimiter in the walker so the span is a node.
  3. **`ts` carry** → render's table path carries `{{Ts}}` style at level (the carry-half).
  4. **Drop the legacy bridge** — `produce_tree` invokes producers via `_to_legacy_registry` /
     `ElementRegistry`; handlers can take `ClassifiedElement` children directly. Pure refactor, last.

**STEP 0 — regression net: DONE, and it earned its keep immediately.** `tools/diagnostics/
snapshot_corpus.py` — corpus-wide `_transform_text_v2` snapshot+diff net (per-article body + sha
manifest under `data/derived/_flip_snap/<tag>/`; `capture` / `diff` / `show`). Every flip step is a
TAGGED DIFF vs the prior accepted tag, never a wholesale rebaseline. **On its first run it caught a
93-article LATENT CRASH** — `_process_single_column_table` (`_tables.py`) and `_content_rows`
(`_math_layout.py`) passed `_html_table_grid`'s `(sep, attr, content)` triples whole to
`text_transform` → `re.sub` TypeError. Latent since the `<table>`→non-table routing landed (post-
dates last build, so deployed bodies intact); a flip rebuild would have triggered it. FIXED (take
the content slot) + committed. Baseline `base` = post-bugfix / pre-flip, 36,691 articles, 0 errors.

**STEP 1a — recursive fraction expander: DONE + committed.** Replaced the (doubly) fake-recursion
fraction loop with module-level `_expand_fractions` (balanced parse → recurse inner → render).
Verified vs `base` (tag `s1a`): **14 articles changed, 0 added/removed, 0 transform-errors corpus-
wide; all 14 leak-resolved** (previously-DELETED equations now render — RADIOACTIVITY a/b/c coeffs,
PROBABILITY, INTERFERENCE, POWER TRANSMISSION, YACHTING…). Fraction tokens reaching the catch-all
`_strip_templates`: **94 → 6** (the 6 = ALGEBRAIC FORMS OCR-garbage source + a MOLECULE fraction
bisected by a table-cell boundary — both pre-existing, out of scope). The fraction loop's
pathological ordering comment deleted itself.

**ACCEPTANCE TEST for the flip (user, 2026-05-31): separate PATHOLOGICAL from LEGITIMATE ordering.**
"X must run after Y" comments are mostly fake-recursion scaffolding (flat `[^{}]` can't span nested
braces, so passes are hand-ordered to fake inner-out). Real recursion makes children-resolved-first
structural → those comments delete themselves. A residue is genuine precedence (classification
disambiguation, input canonicalization, longest-match lexing) and survives. Per-step signal: count
surviving ordering comments; pathological → 0.

**FINDINGS LOGGED (pre-existing, NOT flip-caused):**
- **7 articles leak a raw `ELEM:` placeholder** into output (e.g. HYDRAULICS, `…ELEM:N}VERSE}`) — a
  placeholder-substitution leak, likely VERSE-related, with an order-dependent element id. Revisit
  during the walker / substitution steps. (NB: the order-dependent id means cross-tool diffs must
  share processing order — `snapshot_corpus` always captures in volume/page order.)
- 1a EXPOSED (did not cause) two downstream rendering artifacts now that the content survives:
  overline applied over `«I»` marker chars (CLOCK), an unrendered sup (POWER TRANSMISSION). For the
  overline / sup handlers' own attention.
- **Curated 20-seed snapshot suite (`test_transform_snapshots.py`) is STALE** — not re-captured since
  the leak-tail drain; 15/20 fail for reasons predating 1a (1a changed 0 seeds). Re-sync with a
  TAGGED per-seed diff (not a blind rebaseline) so it resumes guarding during 1b.

**STEP 1b — general recursive inline-template expander: IN PROGRESS.** `_expand_inline_templates`
(module-level, registry-driven balanced-brace recursion — the general form of `_expand_fractions`)
added to `body_text.py`, run first in the unwrap loop. Registry batch 1: greek/polytonic/hebrew/
lang/uc/nowrap/right/left → content; sc/asc/smallcaps/small-caps → «SC»; Fs → «FS[size]» (value-
bearing). Verified vs `base`/`s1a`: 17 articles changed, 0 regressions — leak-resolutions
(empty `«I»«/I»` / `«CTR»«/CTR»` → full content) + marker RE-NESTING corrections (overlapping
`«FS»«SC»…«/FS»…«/SC»` → properly nested `«FS»«SC»…«/SC»…«/FS»` — EGYPT, SILK; the recursion paying
off). NEXT: step B (delete the now-redundant flat regexes the engine supersedes — byte-identical) +
migrate remaining nestable families (sub/sup translate-family, etc.).

**THE NESTING-REGEX SCOREBOARD (user principle, 2026-05-31): any regex that gestures at nesting is a
latent bug.** Regexes provably can't match balanced structure, so a negated class / non-greedy used
to fake "stop at the nesting boundary" (`[^{}]*`, `[^}]*`, `[^<]*`, `.*?` butting a `{{`/`<`/`[[`) is
correct only on non-nesting inputs; where they nest it silently deletes / mis-matches / drops a
marker — usually LATENT. Corpus-of-code count: ~256 candidate sites (233 brace, 14 tag, 9 non-
greedy). NOT 256 fixes — they PARTITION into a few structural cures, each dissolving a category:
body_text inline (~92) → the engine + step B; `_walker` (~13) → recursive recognition (the flip
proper — a correctly-recursive walker needs no regex to approximate nestable extent);
figure/table/math producers (~50) → route captions/cells through the recursive transform;
detect_boundaries / title / extract_* (~50) → separate subsystems, triage (some are honest flat-
token matchers, not nesting). The count is a second flip scoreboard alongside strip_scan; it falls in
STEPS (one per cure) to a floor of genuine leaf matches. Per-site test: does the construct actually
nest in the corpus? ([[verify-corpus-claims]]).

**FINDING — multi-line caption truncation (pre-existing, logged):** the IMAGE producer's external-
caption capture is LINE-BASED; a caption spanning two source lines (TRANSFORMERS Fig. 4:
`{{center|{{Fs|92%|{{sc|Fig}}. 4.—…⏎Closed Circuit Transformer.}}}}`) is captured only to line 1,
cutting `{{center|{{Fs|` before its closers → unbalanced braces → mangled caption (`92%` debris).
Broken in BOTH pre- and post-1b (s1a's caption is also truncated, missing line 2) — step 1b only
changed the cosmetic debris, NOT a regression. Fix = brace-aware multi-line caption capture; belongs
to the figure/caption worklist.

**REMAINING RUNWAY:** 1b (general inline-template expander — same recipe, the `_unwrap_content_
templates` / `_strip_templates` surface) → 2 (`/s`-`/e`) → 3 (`ts` carry) → 4 (bridge drop) →
vol-1 rebuild. Plus the curated-seed re-sync.

---

## PROGRESS (2026-05-30) — plate-probe session: render() bet CONFIRMED on real plates; THREE steps to the finish

Ran the recursive-render bet on real plates (AEGEAN PLATE I–IV) via `render_proto.render_markers`
(new producer-contract variant: emits the MARKER contract, not HTML) + viewer CSS. **Result: the
grid-preserving `render()` beats production with ZERO plate-specific producer logic.** Everything
the plate needed was *generic, corpus-wide* work. The plate doubled as a **probe** that flushed out
the real remaining issues.

**The runway (corrected):**

1. **Viewer consolidation — DONE.** One `decodeInlineMarkers`; all six render contexts wired;
   plate renders clean.  Adding a marker is now one line.
2. **Leak tail — IN PROGRESS (1378 → ~1015, acceptance test PROVEN).** Drain what `_strip_templates`
   silently deletes, then delete it.  KEY REFRAME: the raw "1378 deletions / ~135 keys" overstates the
   WORK.  Families split into (a) genuinely-unhandled — small new handler; (b) bulk-handled, EDGE-TAIL
   only — a targeted patch.  **Drained so far (each verified: strip_scan count → 0):**
   `float` ✓ (143, «FR»/«FL»), `coordinates` ✓ (100, formatted in place), `underline`/`double
   underline`/`u` ✓ («U»), `strikethrough` ✓ («STK»), size-extras ✓ (`fs70/85/90`, `font-size`,
   `font size`, `xxx(x)-larger` → reuse «FS[n%]»).  Re-run #1 confirmed float+coordinates dropped
   to 0 (1378→1130); cheapies are ~115 more.  Also drained: `lkpl` (71, via a post-loop second pass)
   and the small-print paired wrappers (consolidated at body_text:838; center paired already at 820-828).
   **THE ENDGAME — three moves and the tail is done:**
   - **layout scatter** (`brace`/`brace2`/`fsp`/`center block`/`lsp`/`letter-spacing`/`font-stretch`/
     `pad thin`/`multicol*`/`parabr`/`clear`/`nopt`) — flat, non-nesting: unwrap-to-content / space /
     strip-contentless. Genuinely cheap. IN PROGRESS.
   - **`ts`** (247) — table-style extraction; entangled with table handling (wants render's table path).
   - **KILL THE FAKE RECURSION** — the BIG move.  `sfrac`/`sub`/`sup`/`greek`/`sc` (+ nested `lkpl`) are
     NOT edge-forms to patch: they're NESTING bugs ([[context-leaks-are-nesting-bugs]], 3rd instance).
     `TT`'s template unwrap uses flat `[^{}|]` arg-slots + an **8-pass iterative loop that fakes
     recursion** (inner-out); residual leaks are where the fake breaks — a resolved nested marker with a
     PIPE (`«LN:a|b»`, `{{sub}}`'s pipe) the slot can't span, or nesting >8.  CURE = real recursion
     (balanced parse, split on TOP-LEVEL pipes, recurse into each arg, then apply) — NOT a flat
     "pipe-aware parser" patch.  This dissolves the whole class at once AND **is the recursive
     inline-template handling `render()` needs** — so the leak-tail's last move is the flip's
     foundation.  (`lkpl`'s post-loop patch is itself flat-paradigm; the recursion subsumes it.)
   Acceptance test: strip_scan records zero → delete `_strip_templates`.  Measure with **strip_scan**
   (real pipeline), NOT leak_scan (its render_proto engine over-reports page-furniture consumed upstream).
3. **Flip the walker — render() takes over AS the classifier comes OUT.**  This is mostly a
   DELETION, not feature-building.  In the recursive model there is no labeling step, so wiring
   `render()` makes the entire classify-then-produce edifice dead: the 5-tier dispatch,
   `ClassifiedElement` + labels, ICL-pairability, DATA_TABLE-vs-figure, the CHEM/figure-family
   taxonomy, the per-family producers, the SHAPE layer.  **Migrates (survives, simplified):** the
   structural *recognition* — which source token = which block — i.e. `decompose`, already present
   at every depth, minus the labels.  **render() genuinely still needs:** the real terminals
   (math/hiero/score) + a few structural dispatches (footnotes, sections, titles, figure↔legend
   assembly).  Most "element types" (ICL/chem/figure families) DON'T need new handlers — they
   dissolve (recurse the table/figure structurally; the plate proved render() preserves structure
   instead of classifying).  Then: wire it in (promote `render_markers` from `tools/diagnostics`),
   **regression-snapshot** vol-1/working-mass before vs after (the safety the whole approach rests
   on), flip, rebuild vol 1.

Non-blocking tidy: 2-3 redundant viewer no-op handlers (body hieroglyph/LN, footnote LN); the
queued bare-initial contributor pickup.

### DISSOLVE-CHECKLIST vs SURVIVORS — verify against the post-flip vol-1 rebuild

The flip CLAIMS to dissolve every classifier-rooted bug. The rebuild must PROVE it: re-test each
DISSOLVE item against the rebuilt output — if one survives, the refactor missed it (a real finding,
not an assumption).  The SURVIVORS are NOT expected to dissolve; keep tracking them separately.
Rule: a bug dies iff its root is in the deleted layer (per-family producers / classification labels
/ `ELEM:` placeholder indirection / imposed table-figure-legend-chem taxonomy); it survives iff
rooted in a layer that persists.

**DISSOLVE — re-test each post-rebuild (should be GONE):**
- [ ] `ELEM:NNNN` placeholder leaks inside `«HTMLTABLE»` cells (VIRGINIA governors, WEST INDIES
  population) — render recurses cells in place, no placeholder substitution step.
- [ ] Chemistry rendering edge-cases — CHEM dissolves (recurse the table).  *Caveat: current CHEM
  path stays until render's rowspan-aware bracket layout matches it — verify parity, not just presence.*
- [ ] Bare-label legend bundling — SPINAL CORD, MALLOW.
- [ ] Two-column-legend sub-patterns — ARACHNIDA Figs: rowspan continuation (31), prime labels (47),
  hanging-indent (26), side-by-side image cells (57-58), credit-glue missing space (13/63/74),
  trailing-PRE annotation (7).  ARACHNIDA is the canonical "all at once" target — if it's clean, this class is dead.
- [ ] BRITISH EMPIRE India-acquisitions table (multi-line cell + `|+` caption leak).
- [ ] (general) any remaining per-family-producer / classification-leak bug.

**SURVIVE — keep tracking (the flip does NOT touch these):**
- **Walker/boundary** (feeds render(), not deleted): title parenthetical-bundling (NITRIC ACID,
  BELLARMINE); `{{c|…}}` Roman-numeral heading-shaped blocks (24); section-recognition.
- **Terminals**: wide-math scaling (KaTeX/CSS dead-end); tall-brace→OUTLINE grouping reconstruction (~8).
- **Upstream text-conversion** (`prepare_wikitext`/`_convert_quote_runs`, below render): italic-inversion
  cascade (`stray_wiki_italic`).
- **Source/data/infra** — ⚠ STALE-SUSPECT, sourced from a weeks-old known-issues memory; **re-verify
  against current state before treating any as open** (the faithful renderer SURFACES source errors
  but never fixes them — `corrections.json`/ops domain).  CONFIRMED STALE/RESOLVED: vol-6 page-map
  off-by-2 (map is sequential 790-794, no gap; scans look right), Meilisearch port exposure (user
  confirms fixed).  UNVERIFIED (could not quick-check; assume nothing): unproofed-OCR count, 13
  missing image files, page-level image mis-ownership, ~93 linkless contributors.
- **Diagnostics/calibration**: `pipe_leak` false-positives on centered math; `stray_braces` math/typo collisions.
- **Content-inspection** (no structural signal): bare-initial contributors (queued, [[hard-means-unencoded-knowledge]]).

**Landed this session (all corpus-wide, not plate hacks):**
- **Size family — DONE, regression-clean.** The font-size scale now carries SYMMETRICALLY: was
  half-handled (up only — `x-larger`/`xx-larger`→`«XL»`/`«XXL»`), the *entire smaller half* +
  `larger` + `fs` were flattening (size dropped on ~12k corpus instances). Now `larger`→`«LG»`,
  `smaller`/`sm`→`«SM»`, `x-smaller`→`«XS»`, `xx-smaller`→`«XXS»`, `{{fs|N%}}`→`«FS[N%]»`
  (value-bearing). Viewer renders the scale (`.size-lg/sm/xs/xxs`, `«FS[v]»`, `«LH[v]»`). Git-isolated
  before/after: **zero content change** (purely additive markers).
- **`{{lh}}` (line-height) — DONE.** Was a SILENT content-loss bug: `_strip_templates` ate
  `{{lh|N%|content}}` whole (Figs 3-6 captions vanished) — invisible to leak_scan (it catches
  over-retention, not deletion). Now carries `«LH[N]»` (content + line-height). 19 articles.
- **`colspan`/`rowspan` — DONE.** `_normalize_attrs` lifted CSS only; now lifts the HTML span attrs.
- **Figure-grid rendering — DONE (viewer).** Figure-tables emit `«HTMLTABLE»` w/ `class=figtable`;
  full-size cell images (`formatCell` was 60px-capping), `display:block` images, `body.plate-page`
  breaks the 960px reading column. Wide-table Expand confirmed intact (HTMLTABLE path, ≥10 cols).

**Step 1 — Viewer consolidation — IN PROGRESS. "Main source of remaining bugs" (user).**
Seven near-duplicate marker renderers, each covering a different SUBSET → **context-leaks**: a
marker renders in the body but not in cells/footnotes/verse/title (the `«CTR»`/`«LH»`-in-cells bug).
This is the viewer-side form of a producer NESTING bug — see memory [[context-leaks-are-nesting-bugs]].
Built ONE shared `decodeInlineMarkers` (the position-invariant markers; frame ones — FN/IMG/MATH/SH/
page/DHR-block-vs-inline — stay per-context). **Headless-tested** (`tools/_scratch/test_decoder.js`,
node: 0 diffs vs body, 0 leaks). **Body wired.** Remaining FIVE: `formatCell`, `formatFootnoteText`,
`renderTitleMarkers` (+ title-display), verse `applyMarkers`, inline-`«HTMLTABLE»`. Acceptance test:
adding a marker becomes a ONE-LINE change. (Two harmless dead no-op handlers — hieroglyph/LN —
linger in the body to tidy; the `«`-vs-`«` escaping mix made the exact-match fragile.)

**Step 2 — `_strip_templates` is a disguised sweeper — CAMPAIGN (drain → delete).** It's the catch-all
tail of `_apply_markup`: deletes ANY unhandled `{{template}}` (content + all) + orphan-brace cleanup,
silently — INVISIBLE to leak_scan. `tools/diagnostics/strip_scan.py` = the MIRROR of leak_scan;
corpus-wide ≈ **1378 deletions / ~135 keys** (distinct count likely inflated by `/s`+`/e` paired-form
splits, size-variant spread, and a count-1 sentinel-artifact tail — verify). Drain to zero, then
delete. Orphan markup should be source-errors-ONLY by construction (every structural token is consumed
by its owning producer); residual → `corrections.json`, surfaced not swept (the totality invariant —
a faithful renderer SHOWS source errors instead of hiding them; the AEGEAN plate's 1-2-vs-3-6 spacing
inconsistency is exactly such a transcription error, faithfully reproduced).

**New diagnostic tools:** `strip_scan.py`, `viewer_loop.py`, `plate_render_diff.py`, and
`render_proto.render_markers` (producer-contract render).

**QUEUED — bare-initial contributor signatures.** `extract_contributors` only knows the
structured shapes (`{{EB1911 footer initials}}`, `{{right|[[Author:…]]}}`); it misses bare
`(A. P. C.)`-style sigs (`{{float right|(A. P. C.)}}` / `{{right|(…)}}` / bare text). These have
NO structural signal — recognition is content-inspection, but *principled*: a sig iff the initials
are MEMBERS of the EB1911 contributor-initials roster (the [[hard-means-unencoded-knowledge]]
move — set-membership in the frozen key, not a parens-and-caps heuristic which false-positives on
asides). They also appear at SECTION ends, not just article ends, so the scan is "find every
`(INITIALS)`, test against the roster, attribute to the enclosing section" — position is a
secondary confidence signal, not the anchor.  ~5-8 named instances in float/right form (`A. P. C.`,
`S. K. M.`, `E. S. M. B.`) + unknown bare-text count; `(X.)` is the ANONYMOUS marker (correctly
excluded).  The float-drain now DISPLAYS them (`«FR»`, no longer deleted); the remaining piece is
ATTRIBUTION — needs the initials key (we have it via `vol29_index`/`vol29_linker`; the current
`ContributorResolver` is full-name-based, not initials-keyed).  Small, self-contained, not a
content-loss bug now.

**Lesson (recurring this session):** several audit-counter failures (wrong-file title-globs,
full-pipeline-vs-standalone drift, byte-vs-content metric, nested-marker word-strip) each manufactured
phantom diffs. When a strong structural prior says "this can't happen" and the audit disagrees,
**suspect the audit first.** See memory [[verify-the-counter]].

---

## VALIDATED (2026-05-30, later) — one recursive `render()` spans figures AND tables; the taxonomy was negative-value

**Extends the pivot below to its endpoint.** There is no ICL producer and no table
producer — there is **one recursive `render()`**: at each node, `leaf` vs `nested`
→ *process directly* vs *recurse*. Nested (block structure: `{|` table,
`{{center}}`, `<poem>`) → preserve it, pass the node's own style through *at level*,
recurse into children. Leaf → dispatch by what the leaf IS: prose → carry its style,
`[[File:]]` → image, `<math>` → KaTeX.

**REFINED (2026-05-30, later) — there is NO element-level terminal *classification*.**
The leaf-dispatch is by what the leaf literally is, not a label on the container:
- **OUTLINE dissolved** — indentation (`:` / `{{em|N}}`) is a STYLE you carry, not a
  transform; its semantic nested-`<ul>` is *optional presentation* (for overflow).
- **CHEM dissolved** — a `CHEMISTRY_LAYOUT` is a borderless TABLE of
  `<sub>`/`<big>`/`«I»` fragments that *leans on* the `<math>` leaf for its `\Big[`
  delimiters. Recurse the table; the math parts become math; nothing chem-specific.
  **CONFIRMED by a full ALDEHYDES chem render via `render()` (`tools/_scratch/
  ald_render.py`):** reaction formulas render with their `[[File:Langle.svg|12px]]`
  bond-bracket glyphs (sized image-leaves), sub/sups, and `→` arrows; the aldehydes
  data table recurses to clean aligned columns; the structural-formula diagram is a
  plain centered `IMAGE`. **CHEM dissolves as a TAXONOMY** (no compile-terminal, no
  label). BUT naive recurse renders the bond-brackets BADLY — it drops `rowspan` and
  pins the bracket at inline 12px, so it can't span its 2-line group; the hand-tuned
  CHEM path is FAR better on bracket layout. Matching it needs rowspan-aware cells +
  the bracket sized to its spanning cell — real work; **current CHEM path stays until
  then. Dissolves-as-category ≠ renders-as-well.** Key insight: the source already
  records the *transcriber's renderability decision as the form* — markup for what he
  could mark up (reaction formulas), an `[[File:]]` IMAGE for what he couldn't (the
  ring diagram). Recursion honors both (recurse markup / carry image); the
  genuinely-hard chem is pre-resolved as scans, so the bracket-layout work is bounded
  to the cases he judged markup-able.
- The genuine *compile-terminals* are the notations that are PROGRAMS, not pictures:
  **`<math>`** (LaTeX→KaTeX), **`<hiero>`** (WikiHiero — Gardiner codes + layout
  operators `-` join / `:` stack / `\` mirror → a 2-D quadrat; 17 in corpus, currently
  PUNTED to a `[hieroglyph: …]` placeholder), and **`<score>`** (LilyPond
  `\new Staff \relative <<{…}>>` → engraving via the Score extension; 5 in corpus —
  BAG-PIPE, BINIOU — CONFIRMED 2026-05-30). They fire as leaves wherever they sit. **MIRROR_GLYPH is NOT
  one** — `<span style="{{mirrorH}}">char</span>` is text + a CSS mirror = style;
  dissolves. **HARD-AND-FAST RULE for a terminal node: anything the VIEWER has to
  COMPILE** (run a notation-engine on — KaTeX / WikiHiero / LilyPond). The producer
  carries every leaf verbatim (math/hiero/score source rides through like style or an
  image — no special-casing); the viewer then either LAYS OUT (structure + style →
  HTML/CSS) or COMPILES (the notation-leaves → an engine). So "terminal" is a
  viewer-side fact, not a producer classification — it is exactly the set of engines
  the viewer embeds. Bounded, stable (grows only with a new notation-engine, never by
  special-casing), and it retroactively explains every dissolution (lay-out) and every
  terminal (compile).

Everything else — figure / legend / data-table / caption / attribution / chem /
outline — collapses to recurse + pass-attributes; structure & style read from the
**source's own attributes**, not a label. `leaf()` = "no block children" (inline
markup stays inside the prose leaf). Termination bottoms out at prose.

**TOTALITY INVARIANT / acceptance gate — NO LEAKED MARKUP, EVER, except transcription
errors.** If every construct is recurse / carry / compile, no WELL-FORMED source can
survive to output. So once the recursion is total, any residual `{|` / `<table>` /
`{{…}}` / `«…»` / `[[…]]` / literal `<hiero>` ⟺ a **transcription error** (malformed
source), located to the element — fixed at the TOP (`corrections.json`) or reported
upstream, **never swept** (the positive form of no-sweepers: handled, or a flagged
source defect — no third bucket). The leak-scan thus flips from a dev gap-finder (now:
HTML-table branch, template renderers, hiero punt) to a **corpus proofreading tool**
when total; leak-count → "only malformed source" *is* the totality signal. Distinct
from render *quality* (chem-bracket layout, hiero placeholder = handled-but-incomplete,
NOT leaks). Two gates: no-leaked-markup (totality) and renders-well (quality).
**Leak verdict, fully stated:** a **transcription error** (fix at TOP / `corrections.json`)
— OR, *only after proving we use EVERYTHING the source gives and there is no transcriber
image-fallback*, **genuine source inadequacy** (well-formed but can't convey the
original; an accepted limit, RARE by construction — the transcriber already absorbs
most inadequacy into `[[File:]]` fallbacks). **Leash:** "source inadequate" is the LAST
verdict, never the first reach — this session repeatedly found apparent-inadequacy was
our own *underuse* (figure / chem / brace / csc all "had it" once we used it all). The
exception is not an escape hatch.

**Prototype + render proof — `tools/_scratch/faithful_html.py` (~40-line `render()`,
no figure/table/ICL anywhere in it) → screenshot, against viewer's real CSS:**
- **OGAM** centred italic caption over image; **CHESS/Sarratt** title+image | solution
  side-by-side (the source's two-cell `{|` table); **ABBEY Fig.3** image + centred
  caption + two-column legend, each item its own line, centred small-caps heads.
- **DATA TABLES through the *same* `render()`**: **ABBREVIATION** (173-row two-column
  list → clean aligned columns + centred small-caps section head), **ABERRATION**
  (numeric columns), **ABRACADABRA** (display). All borderless/aligned — and *more
  faithful than production*, because EB1911 "tables" are aligned columns, not ruled
  grids: the source carries **no border attr**; production's `DATA_TABLE`→`.data-table`
  gridlines were our imposition. Border-vs-borderless comes from the source attr
  (a `GRID` check on the `{|` line), not a label.

**csc fix landed + corpus-audited.** `{{csc}}` = "Center Small Caps" (= `{{center}}`
+ `{{small-caps block}}`); the pipeline flattened `csc → «SC»`, dropping the
centring. Fixed in `body_text.py` (`csc → «CTR»«SC»…«/SC»«/CTR»`). Corpus audit
(`tools/_scratch/audit_csc.py` + `diff_csc.py`): **732 segments / 943 occurrences,
100% pure centring-wrap, zero content change, zero errors.** The "centred-vs-left"
fork was never a source-vs-print judgment — it was us tossing an attribute the
source named in the template. See [[forks-are-dropped-attributes]],
[[imposed-taxonomy-is-negative-value]].

**Capstone:** the figure/table/ICL taxonomy was an imposed, **negative-value**
re-encode — a lossy re-encode of an already-clean signal that could only lose
fidelity AND add work (the classifier, the gate, `LAYOUT_WRAPPER`, the sweepers,
the forks). The tell: it made us work *harder*, not easier.

**Open (NOT done — report is, not ought):**
1. **Corpus-wide validation** — proven on ~6 representative cases, not the corpus.
2. **Ruled-table inverse — RESOLVED (AUSTRIA, 2026-05-30).** AUSTRIA-HUNGARY has both
   kinds and the source distinguishes every one: borderless → no border signal;
   ruled → explicit (`border="1"`, `class="wikitable"`, a `{{Ts|bt}}` row border-top,
   per-cell `border:none` overrides). Sharper: **border is per-element style (table /
   row / cell), NOT a table-level binary** — #4's rule is `{{Ts|bt}}` on a *single
   row* (a header separator), which "gridded vs borderless" cannot even express. So
   the prototype's `GRID` flag (data-table-class vs figtable) was itself a small
   RELAPSE into the dismantled taxonomy; the fix is to DROP it and carry border as
   per-element style like width/align/valign. No recognition residue — border is
   attribute-passing, same as everything else; terminals stay the only real classify.
3. **Wiring** — all of the above is a prototype `render()`, NOT in the pipeline. The
   terminals exist, but csc proved a terminal can silently flatten (BODY_TEXT dropped
   centring), so they need a faithfulness AUDIT, not the assumption that they're
   correct. Work: the structural walk that dispatches to them + the viewer subtraction
   (drop figure-box / legend-aside / imposed data-table gridlines + the `GRID` flag;
   recognise `{{ts}}`/border at level instead of spreading/bucketing).
4. **csc snapshot re-baseline** — `body_text.py` change is live; affected snapshot
   baselines need re-baselining on sign-off (the audit is the tagged diff).

### Falsification test — PRE-REGISTERED (2026-05-30), verdict fixed before running

Guards both biases at once: the wish (toward the elegant single-`render()`) and the
over-correction (manufacturing theory-kills to perform rigour). Run the HOSTILE set,
count breaks, do NOT relabel a break as "engineering" afterward.

**A break = a real theory residue** iff a source shape:
- (a) renders correctly ONLY with a *label*, not from per-element attributes; or
- (b) needs a *source-MEANING* decision absent from the source (NOT presentation —
  see below); or
- (c) loses content; or
- (d) forces the "mechanical" viewer to decide a source-question (caption? ruled?).

**Explicitly NOT breaks:** (1) viewport/presentation fitting — wide content
overflowing a column (wide math, wide image, wide table) is a display strategy
orthogonal to source meaning; (2) the article→element PARTITION — section /
boundary / plate-DETECTION is an upstream layer, never claimed to be `render()`'s
job. A "decision absent from the source" counts under (b) only if it's about what the
source MEANS, not how to fit a faithful render into a viewport.

**Hostile set:** AFRICA (brutal), a wide-math article, an HTML-`<table>` article, a
float/`{{clear}}` layout (the standalone CHESS solutions), a plate, an OCR-garbage
math page — chosen *because* they are likely to break it.

**Standing bets (2026-05-30):** wide math → presentation, not a break; **plates →
`render()` covers rendering in full** (a plate is a figure-of-figures; detection is
the partition). The test exists to *earn* these, not assume them.

**RAN (2026-05-30) — NO BREAK.** Prototype `render()` + an HTML-`<table>` branch
(reusing `_html_table_grid`, balanced nested-table masking) over `tools/_scratch/
hostile.py`:
- **Plate** (AEGEAN PLATE II) → rendered as images + centred `Fig.` captions. Bet won.
- **AFRICA** (187 elems, the corpus's worst): **0 exceptions; structural recursion
  100% clean** — the 16 residual leaks are ALL `{{tmpl}}` (two unhandled body-text
  templates: `{{EB1911 Shoulder Heading}}`×16, `{{Fine block}}`×4); **zero** raw
  `<table>` / `{|` / `<poem>` / `[[File]]` leaks. The HTML-`<table>` branch took
  structural leaks 57→16 on AFRICA and 45→1 on INTERPOLATION.
- **Residue, fully enumerated, all engineering (no label, no source-meaning call):**
  (1) a finite set of missing body-text template renderers — `{{EB1911 Shoulder
  Heading}}`, `{{Fine block}}`, `{{ne}}`, `{{Polytonic}}`, `{{EB1911 tfrac}}`, and
  `{{brace}}` (the last a real row-spanning brace-group LAYOUT renderer, not a
  one-liner); (2) dropped table captions (`|+`/`<caption>`); (3) the
  CONTRIBUTOR_FOOTER terminal (names drop) — footer renderer or partition-layer.
- **Verdict:** earned, not asserted — the structural core + HTML branch hold on the
  worst article with criteria fixed beforehand. **Bounds:** proves structure, not
  that every missing renderer is trivial (`{{brace}}` isn't); still AFRICA +
  INTERPOLATION, not the broad corpus. Detector caveat: content-loss counts are
  inflated by a word-counter that strips `«LN»` link text from output-but-not-raw.

---

## WORK PLAN (2026-05-30) — remaining work is PURE ENGINEERING, ordered

Recognition / architecture is settled (sections above). This supersedes the looser
open-items list. Two instruments gate and drive everything — build them first.

**Phase 0 — instruments.**
- **leak-scan** = totality gate + worklist. De-noised (do NOT flag `render()`'s own
  `<table class=…>`; measure real content-word loss with a template-name stopset). Run
  on `render()` output corpus-wide; each leak names the next construct to handle.
- **render-diff vs the current pipeline** = regression + quality net. Two-way; tag
  every diff improvement / regression / neutral.

**Phase 1+2 — producer ⇄ viewer, ONE per-attribute lockstep loop** (broad-strokes
steps 1+2). Built as a PARALLEL path on raw elements — the live pipeline is untouched,
so the whole phase is low-risk and validated offline. It is the metadata-carrying
pattern (proven on img align/width) repeated attribute by attribute: translate one
attribute in the producer → handle it in the viewer → verify → commit → next. The
system is consistent at every attribute boundary (never a half-built contract), so you
can stop / commit / ship between any two.
- **Totality attributes (leak-scan-driven):** transcribe every source attribute — full
  `{{Ts}}` vocab, `{{em}}`, font-size / line-height, image width / align,
  rowspan / colspan — plus the few template renderers (`{{Fine block}}`, `{{ne}}`, …).
  Viewer SUBTRACTS opinions (600px figure-box, legend-aside, data-table stripes, the
  `GRID` flag) and gains the borderless layout-table lane + `{{Ts}}` recognition. Done
  when leak-scan → only-transcription-errors corpus-wide (TOTALITY FLOOR). Lousy
  renders allowed here.
- **Quality attributes (render-diff-driven):** the ones that don't leak but render
  badly (chem bracket → rowspan-aware sizing). Same lockstep, graded by the visual
  diff. **Keep the current CHEM path live until its bracket quality is matched** —
  total never ships worse.

**Phase 3 — cutover (broad-strokes step 3 + classifier + SHAPE), LAST, incremental,
netted.** The front end collapses to **one recursive `decompose` + outer boundaries**:
the walker = `decompose` at the top level + the genuinely-outer boundaries it keeps
(`«PAGE»`/segment, section, article); `render()` = the same `decompose` recursing.
- Cut over **one outer-element-type at a time** through `render()`; render-diff each
  against the working mass; sign-off before any rebaseline. NOT big-bang.
- When all types route with clean diffs, DELETE the dead code (delete-dead-code: after
  call-sites are gone, not before) — the tier-dispatch **classifier** (~35 labels), the
  **SHAPE** layer (`_shapes.py` + SHAPE_* + shape-dispatch; its regexes were the
  construct-inventory `decompose` had to absorb), and the **per-label producers**.
- Re-run leak-scan corpus-wide post-cutover — totality must still hold.

**Invariants throughout:** (1) totality = no leaked markup except transcription errors
(leashed inadequacy exception); (2) total never ships worse than the current render
(chem quality preserved across the move); (3) the two gates stay independent —
no-leaked-markup (totality) and renders-well (quality).

**Shape:** instruments → parallel low-risk per-attribute build (totality-floor, then
quality) → incremental netted cutover that collapses walker + classifier + SHAPE into
`decompose` and deletes the taxonomy + per-label producers.

---

## ARCHITECTURAL PIVOT (2026-05-30, late) — the ICL taxonomy is a needless two-ended imposition

**The conclusion that supersedes the figure-extractor section below.** Reached by
stepping back and asking what caption / legend / attribution REALLY are: they are
**our invented categories**, not properties of the source. The source already
carries everything renderable — **structure** (what each element is), **order**
(arrangement: the thing above the image renders above the image), and
**attributes** (per-element style: italic, centred, cell widths, image size).
Classification reads that information, buckets it into our categories, then maps
the buckets *back* to styled output — a **roundtrip that begins and ends at the
same information.** The label "caption" is attached and never consulted; the
output is produced from text+style+order regardless.

**It's a TWO-ENDED imposition, one taxonomy:**
- **Producer end** — the classifier sorting content into caption/legend/attribution
  (and everything serving it: legend parser, multicol logic, `{{LEGEND}}` block,
  attribution-relocation, the move-list mis-fire).
- **Viewer end** — `viewer.html`'s opinionated renderers: the 600px IMG figure-box,
  the `figure-legend` aside, caption-bundled-in-IMG, `data-table` gridlines. The
  **viewer has too many OPINIONS** — it decides how a figure/legend/table looks
  instead of rendering the author's markup ([[feedback_shape_vs_rendering]]:
  viewer deciding a source-question = bug).

**The clean model — both ends SUBTRACT:**
- **Producer**: preserve source structure + style + order; emit the one genuinely
  structural marker (`[[File:]]`→IMG, because an image must render as an image);
  carry everything else's markup (`«I»`, `{{center}}`, cell attrs) through. No
  classify, no relocate, no assemble. The walk/bag/attributes/order work already
  done is exactly what this consumes — it is NOT wasted; only the classification
  *layer on top* dissolves.
- **Viewer**: render that markup MECHANICALLY, holding no opinions — italic→italic,
  centred→centred, table→table-with-its-own-attrs. Delete the figure-box, the
  legend-aside, the caption-bundling, the data-table styling.

**Validated (producer side) by a faithful-render prototype (`tools/_scratch/
faithful_prototype.py`):**
- **OGAM** (`{{center|«I»caption«/I»<br>[[File:…]]}}`) — production *breaks* it
  (renders the image as the literal filename text); faithful = `[italic caption,
  IMG width=700]` in order → caption above image. **Production bug fixed for free.**
- **CHESS** — every "problem" DISSOLVES with no classification: the move-list
  "White wins… 1.… 2.…" renders as the prose it is (production bundled it as the
  IMG caption); "Diagram 1.—…" renders as small-caps text (never needed to be a
  `Fig`); position titles render italic. CHESS was never broken — *we* invented
  its problems by imposing a taxonomy it didn't fit.

**Remaining work = subtraction + one preservation gap (sized on real cases, not
hand-waved):** (1) walk loose `{{center|…}}` figures, not just tables; (2) STOP
stripping wrapper-style — `_walk_cell`'s `_unwrap_cell_wrappers` discards
`{{center}}`/`{{Fs}}`, so the ogam caption loses its centring; carry it as an
attribute; (3) `<br>`→line break; (4) viewer: remove the opinionated renderers,
render carried markup faithfully.

**DISCIPLINE — do NOT rip out until rendered output is looked at.** Producer side
proven by prototype; **viewer side pending**: render source markup with the
viewer's opinions removed and confirm figures come out correct. Look, then delete.

---

## Current focus (2026-05-30) — Figure extractor rebuild + corpus loss-sieve

**Context:** `_figure_decompose.extract_figure_components(raw, tt)` is the raw,
recursive figure-component extractor (the ICL analog of `_table_decompose`) —
a clean PARTITION of a figure into images / caption / attribution / legend /
footnotes via consume-as-extract.  Built + validated, still **additive/inert**
(not wired into any producer or the gate).

**Governing principle this session (memory: `feedback_current_output_not_oracle`):**
production is a **floor, not a target** — byte-identical is a chimera; the only
failure mode that matters is being **worse** (content lost/corrupted), not
**different**.  Validation flipped from "IDENTICAL vs DIVERGE" to a
one-directional **loss** check.  Corollary: when reusing production's
battle-tested leaf parsers, **delegate a parser WHOLE or reimplement it whole —
never splice** (a cherry-picked multicol fragment + my own sort made us *worse*
than production: scrambled order + truncated continuations).

**Landed this session (all in `_figure_decompose.py`, inert):**
- **Loose-`<poem>` legends** → `_emit_legend_chunk` (poem masked through the
  cell splitter so its entry-per-line structure survives — the nested-table
  masking analog).  Fixed a real data-loss (dropped `A.`/`B.` labels).
- **Multicol legends** → production's COMPLETE logic (rowspan / column-major-
  with-continuation / alternating-pair, column-major reading order, conditional
  sort).  Replaced a partial fragment that truncated + reordered.
- **HTML `<table>` figures** → flavor dispatch in `_gather`: `<table>` peels to
  `_html_table_grid` (robust to EB1911's unclosed `</td>`/`</tr>`, preserves
  newlines), `{|` to the wiki path; everything downstream shared.  "One
  recursion, two row-extractors."

**Corpus loss-sieve (`tools/_scratch/sieve_legend_loss.py`) — the standing
acceptance gate.**  For every article-page figure: does any content word
production put in a `{{LEGEND:}}` appear *anywhere* in the new extractor's
output (reorder/markup/arrangement-tolerant)?  Loss = real drop.  Run over all
36,691 article pages.
- Before HTML fix: **3526 missing content-words / 35 articles**, ~all one root
  (extractor was wiki-only → HTML figures produced empty).  *This is the blind
  spot reasoning can't see: a whole input flavor never entered the recursion —*
  *the no-loss theorem only covers bytes that get in the door.*
- After HTML fix: **~40 words.**  Residual = (a) production markup-leak
  (`td/tr/style` — we're strictly better, 0 content), (b) **the prose-legend
  case** — `<br/>`/newline/italic-label/`{{em}}` entries `_gather_cell`
  flattens (`<br/>`→space as *noise*) and the prose parser partially DROPS
  (CHAERONEIA: `commissure`/`ventral` genuinely lost), (c) PALAEOGRAPHY (13
  Latin words, manuscript facsimile, outside any figure element) + OCR noise.

**Next — step 2: recurse the prose legend to the ground.**  `<br/>`, newline,
`<poem>` line, and `;` are all entry-boundaries; the ground-up recursion treats
them UNIFORMLY → each entry a labelled leaf in reading order → retires the
masks, `_parse_prose_legend_rows`/`_emit_legend_chunk` delegates, and the
`<br/>`-as-noise drop together.  Sieve must go to zero on the prose residual.
Then wire the extractor (gate recognizes image-anywhere-in-raw; producers read
`extract_figure_components`; corpus inertness; figure cohort → ICL).

---

## Current focus (2026-05-29) — Recursive table decomposition + classifier tier model + LAYOUT_WRAPPER audit

**Goal:** finish draining `_strip_templates` of nameable templates, then move
the drain *upstream* to the classifier where its analog (`LAYOUT_WRAPPER` and
`DATA_TABLE` catch-alls) hides recognition gaps.  Architectural pivot mid-
session: each remaining `ts` leak got mapped to a specific producer bug, so
`ts` is no longer a strip-templates problem but a localized table-producer
problem.  That insight cascaded into a target-architecture recording for the
whole classifier dispatch.

### Catch-all drain
- 2,292 → ~1,646 phase-1 deletions (−28% this session); explicit named
  owners for: cheap-win inline typography (smallcaps / small caps / bold /
  bl / smb / nw / di / x-smaller / word-spacing / rule, hyphenation
  joiners, char escapes), bare `{{0}}` (padding), bare `{{lb-}}` (unit),
  Dotted TOC line / Dotted TOC page listing (council and country tables).
- `<div {{Ts|…}}>…</div>` body-text handler (167) + extended to tolerate
  `<div align=center {{Ts|…}}>` (~108).
- Walker `html_ts_figure_end` recognizer for `<div {{Ts|ac|…}}>…[[File:…]]…
  </div>` figure-wrapper variant (6), sibling of `html_float_figure_end`.
- **`ts` 391 → localized to producer bugs:** the remaining `ts` strips
  break down to specific producer-side leaks now queued as tasks (#24 HTML
  table attr-slot peel, #25 `_process_prose_figure` absorbed caption-table
  opener, #26 wikitable special-shape producers bypassing
  `_extract_table_cells`).  `_strip_templates` no longer hides them.

### Architectural principles clarified (memory)
- **`feedback_total_functions_not_cleanup_passes`** updated with the user's
  canonical vocabulary: "total" = every producer is total over its byte
  string.  Use the term.
- **`feedback_table_decomposes_recursively`** (new) — table → row → cell →
  body-text; each layer peels only its own structural wrapper, cell content
  reaches body-text in prose-uniform context.  One body-text handler set
  covers cell content AND article content AND ref content.  No "in a table"
  mode.  The architectural fix for ALL context-specific leaks (e.g. `Ts` on
  attribute slots, `sc`/`sup` inside cells) in one stroke: every wrapper
  producer total → inner template handlers' totality is sufficient.
- **`project_classifier_tier_architecture`** (new) — five-tier dispatch
  PRE-ICL → ICL → PRE-TABLE → TABLE → body-text; each tier total over its
  accepted domain or rejects (falls through); NO CATCH-ALLS at any tier.
  ICL and TABLE tiers have symmetric shapes (gate → atomic decomposition →
  assembly).  Wiki vs HTML at the table tier is one producer with two row
  extractors.
- **`feedback_sweepers_hide_bugs`** extended: the producer-side invariant
  applies identically at the classifier layer.  `LAYOUT_WRAPPER` and
  `DATA_TABLE` (as catch-alls) are classifier-side sweepers; every occupant
  is a known classifier recognition gap.

### Table-decomposition refactor (Step 2 done)
- **Step 1:** new `_table_decompose.py` (200 lines) — canonical
  `extract_wiki_rows` / `extract_html_rows` / `produce_cell` /
  `assemble_wiki_marker` shape-agnostic infrastructure.  Producers pick
  the appropriate row extractor; downstream cell parsing, style
  extraction, content via body-text, and marker assembly are uniform.
- **Step 2:** `_process_html_table` migrated to flow through canonical
  pipeline.  Per-cell alignment that the old HTML producer was silently
  dropping for non-rowspan tables (HTML_TABLE path was 49% pure per
  project status) is now preserved automatically — `⟦r⟧` / `⟦c⟧` marker
  prefixes fall out of the canonical chain without special-casing.
  AGRICULTURE Table XIII (UK 1905 livestock numbers) and STEAM_ENGINE
  Load-in-kilowatts table snapshots updated to capture recovered
  alignment.  Tasks #27 (cell-separator `|` collision with marker
  contents like `«BRACE2[2|r]»`) and #28 (viewer renders `<br>` in cells
  as literal text) queued as pre-existing leaks the migration exposed.
- **Step 3 deferred:** wiki `_process_table` migration is small
  architectural work (wiki path already ~99.8% pure per
  [[project_table_family_status]]); the bigger leak reductions live in
  carving `_process_table`'s content-classification fallbacks (image+
  caption bundle, plate-image-layout, structural-formula, tiny-inline)
  out to dedicated classifier labels + producers.  Each fallback hits
  `_process_table` because the classifier missed the shape upstream
  ([[feedback_turn_bugs_into_producer_bugs]] / table-producer-invariant).

### Classifier-catchalls audit (`tools/diagnostics/audit_classifier_catchalls.py`)
First measurement of how bad the classifier-side catch-alls are:

- **DATA_TABLE: 95% pure** (1201/1255 are genuine grids, 54 misclassifications
  — 52 SINGLE-COLUMN leaks, 2 MATH leaks).  Real over-inclusion problem but
  small.
- **LAYOUT_WRAPPER: 0% principled** (84 occupants, ZERO match the principled
  un-pairable multi-image figure role).  Bucket breakdown:
  - 36 data-leak (no images at all — claimed by nested-TABLE detection)
  - 25 uncategorised (edge structural shapes)
  - 9 verse-leak (POEM children — `_is_poem_wrapper_pred` gap)
  - 8 single-figure-leak (1 IMAGE — ICL family rejected, sub-dispatch gap)
  - 6 single-column-leak (`_is_single_column_table_pred` runs after, never
    gets a chance)

Diagnostic: `_is_layout_wrapper` does three unrelated detections bundled under
one label name (POEM-only / nested-TABLE / IMAGE-with-short-content); each
maps to a different proper home.  The label can be deleted entirely once each
of the three detection branches routes to its correct label via predicate fix
upstream.

ICL path itself is **close but no cigar** — when the ICL dispatcher's gate
passes but sub-dispatch returns None, the element falls through to POST_ICL
unlabeled.  That's a catch-all-shaped hole inside ICL: gate said "figure"
but sub said "I can't label it."  Total-function discipline forbids it; the
fix is to either tighten the gate (reject shapes the sub can't label) or
extend sub-dispatch (label everything the gate claims).  Empirically this is
a small bucket — only 8 single-figure-leaks in the LAYOUT_WRAPPER audit point
at this hole.

### Strategic work-order (user's synthesis, 2026-05-29)

The full campaign for eliminating producer bugs in three ordered moves:

1. **Classifier totality first** — every producer receives only the shapes
   it's instrumented for.  Eliminates the entire class of "producer received
   the wrong input" bugs.  This is the LAYOUT_WRAPPER / DATA_TABLE catch-all
   drain, plus the ICL gate/sub-dispatch totality fix.
2. **Producer architecture: canonical decomposition** — table → row → cell →
   body-text (Step 1 / Step 2 done for HTML side; the figure-family analog
   already established in `[[project_icl_family]]`).  Cell content reaches
   body-text in prose-uniform context; one body-text handler set covers
   everything; context-specific bugs evaporate.
3. **What remains is strictly localized** — half the prior producer bugs
   were misclassification, fixed by (1).  The other half are inside one
   producer's body, with no upstream contamination, and trivially debuggable.

Skip (1) and (2)'s producer fixes are debugging in fog.  Skip (2) and even
correct-input producers carry inline content-classification leftovers.
Do them in order and producer bugs become finite and tractable.

### Architectural pivot late in session: the LAYOUT_WRAPPER drain is walker work, not classifier work

Diagnostic on the 36 data-leaks (extending `audit_classifier_catchalls.py`
with per-occupant opener dumps and sampling outer-body structure for
GERMANY / ICELAND / GYMNOSPERMS) revealed:

- These outers DO have substantial content beyond the nested table
  (real data tables with `{{brace2|N|side}}` decoration mini-tables;
  complex timelines with sub-grouping; figure-groups with image-bearing
  nested children).  Not empty attribute envelopes.
- `_is_layout_wrapper`'s detection (2) "has nested TABLE child" is an
  invalid classification signal — having a nested table doesn't
  distinguish anything; many real data tables have decorative nested
  mini-tables, and figure-groups have image-bearing nested tables.
- The misclassification isn't at the classifier — it's that the walker
  separately bounds the nested `{|…|}`, putting it in the outer's
  `inner_registry` where `_is_layout_wrapper` can detect it.

The fix moves to the walker, and along the way collapses to a much
sharper architectural target:

**Universal leaf-shape contract: every shape is a leaf from the
classifier's perspective.**

  - `classify()` returns a flat list of `(label, raw_bytes)` pairs — one
    per outermost atomic shape.  No tree, no `inner_registry`, no
    placeholder substitution coordination across layers.
  - The walker is ONE PASS over the article body, bounding only
    outermost atomic shapes — no recursion into element bodies for
    sub-elements of any family.
  - Every producer owns its own recursion privately, through its
    extractor chain.  The TABLE producer's cell extractor recognizes
    nested `{|…|}` in cell content and recursively invokes the
    canonical pipeline; the FIGURE producer's caption/legend extractor
    does the same for nested figures.  Whether there's actually
    anything left to recurse on is the producer's private decision.
  - The classifier doesn't know or care whether a shape's content has
    sub-elements; each invocation is total over its byte string with
    no parent-context awareness.

The "shape recurses / shape doesn't" distinction (current `LEAF_SHAPES`
at `_classifier.py:342`) collapses — leaf behavior becomes universal.

**Why this matters (captured in [[feedback_recursion_at_the_right_layer]]):**
from every layer's local perspective, there is no nesting.  The walker
sees a flat sequence of outermost shapes; the classifier sees independent
byte strings; each producer sees only its own decomposition.  Nesting
only exists in a global cross-layer view, and no layer needs that view.
Nesting bugs can't exist when no layer is positioned to make them — the
entire class of bugs we've been chasing (LAYOUT_WRAPPER misclassification,
placeholder-substitution coordination, BRACE2-separator collision,
parent-child context predicates) is symptomatic of nesting being visible
to a layer that shouldn't see it.

### Methodology crystallized (2026-05-29, this session)

The flat-walker move is one re-entrant triple — **walk → classify →
produce** — threaded through every producer.  Each producer peels its own
structure (family-specific) then re-enters the triple on its sub-content;
the triple bottoms out at body-text.  `inner_registry` is the **central
evil** from the producer's POV — the artifact that ferries "inside" across
layer boundaries, violating [[feedback_classifier_returns_only_label]].  It
wears two faces of one cause (recursion in the wrong layer): the
producer-facing face (`inner_registry` as a producer input, killed in
Step B) and the classifier-facing face (`classify()` recursing to build
it, killed at Step C).  Full principle in
[[feedback_recursion_at_the_right_layer]].

**Per-family loop (repeat until `LEAF_SHAPES` is universal, then delete it):**
- **A.** Producer-owned recursion: recognize raw, recurse, direct-feed
  tests, prove inertness.
- **B.** Migrate the family's `inner_registry` readers — producers AND the
  label predicates — onto raw-byte discovery; diff the label distribution,
  zero unintended transitions.
- **C.** Add the shape to `LEAF_SHAPES` (`_shapes.py:67`) → `classify()`
  sets `inner_registry = {}` and stops descending.  Recursion goes live
  for that family; the per-family flip with smallest blast radius.

### Progress (2026-05-29, this session)

- **Step A DONE — table family.**  `_table_decompose.py` gained
  `find_nested_table_spans` / `_mask_nested_tables`; `extract_wiki_rows`
  masks nested `{|…|}` so the outer row-splitter can't fragment them;
  `produce_cell` takes an opt-in `recurse` callback.  Dormant in
  production (no caller passes `recurse`; no raw `{|` reaches cells while
  the walker still placeholderizes).  12 direct-feed unit tests
  (`tests/unit/test_table_decompose_nested.py`); 116/116 fast suites +
  20/20 snapshots byte-identical.
- **Step B STARTED — ICL gate `has_image` → raw, PROVEN INERT.**
  `_is_icl_family`'s `has_image` now reads raw via
  `_top_level_image_present` (peel outer → `_mask_nested_tables` →
  `_IMAGE_NS_LINK_RE`); **0 label transitions across 242,252 elements**
  (`tools/_scratch/diff_label_dist.py stepb_base stepb_icl`).
  `figure_child_count` left registry-backed ON PURPOSE — the multi-figure
  GROUP branch is flip-coupled (a container of figures isn't a figure; its
  children speak for themselves once they recurse out).  It **self-
  dissolves at Step C**: registry empties → count 0 → groups reclassify
  automatically; sweep the dead branch then.  Reclassification population
  ≤ 572 (clean article-only `UNPAIRED_FIGURE_GROUP`; the unfiltered count
  of 869 included 297 plate-page hits — 34% pollution, vindicating the
  article-only audit fix) → ≤0.24% of 239,417 article elements.  Clean
  Step-C reference baseline: `tools/_scratch/label_distribution.art_base.json`.
- **Step B — `_is_poem_wrapper_pred` → raw, PROVEN INERT.**  POEM/IMAGE
  detection + the per-cell "just a poem" check now read raw (peel outer →
  `_mask_nested_tables_all` → scan), not the registry/placeholders.  First
  diff surfaced 2 `LAYOUT_WRAPPER → VERSE_TABLE` flips (INTERPOLATION,
  vol 14) the 20-article snapshot suite missed — a masking inconsistency
  (nested *HTML* `<table>` wasn't masked, only wiki `{|`, so a nested
  `<table><poem>` leaked and the outer's `(4).` equation cell was missed).
  Unified both predicates onto `_mask_nested_tables_all` (masks both
  flavors); re-diff **0/239,417**.  `_is_single_column_table_pred` was
  already registry-free (no migration needed).  The corpus diff catching a
  regression the snapshots couldn't = the net working; lessons banked in
  [[feedback_classification_is_regression_surface]] (two-regimes +
  catch-all-exit-trap).  INTERPOLATION logged as a future MATH-drain
  occupant of LAYOUT_WRAPPER (its nested `<table><poem>` is already
  correctly VERSE_TABLE; the outer is a numbered equation system → MATH).
- **Audit-discipline fix.**  All audits scope to article pages until
  plate-land (plates fork to `parsers/plate/`, never reach the element
  classifier).  `label_distribution_snapshot.py` was the lone unfiltered
  audit (now filters `article_type != "plate"`); the table/figure/
  classifier cluster already loop-skips plates, so status.md's
  LAYOUT_WRAPPER / purity numbers stand.  See
  [[feedback_audit_code_discipline]].
- **Stage A — `_is_layout_wrapper`'s nested-TABLE branch REMOVED (invalid
  signal), VERIFIED.**  "Contains a nested table" distinguishes nothing
  (real grids carry decorative sub-tables too); it intercepted genuine
  tables because `_is_layout_wrapper_pred` sits at POST_ICL position 2,
  ahead of DATA_TABLE / single-column / math.  Removed → occupants fall
  through to the correct downstream predicate.  Full-coverage diff:
  **LAYOUT_WRAPPER 84 → 17** (67 transitions, ALL `LAYOUT_WRAPPER →
  {COMPLEX_HTML 28, SINGLE_COLUMN 28, DATA_TABLE 11}`; zero collateral on
  any principled label; tree structure identical).  INTERPOLATION
  render-verified content-preserved (`(4).`/`(5).` + equation-VERSE intact).
  CAVEAT: the `17/0795` MARSUPIALIA `→ SINGLE_COLUMN` rows are the WRONG
  target — pure-figure article, belongs in ICL; Stage A only *relocated* a
  pre-existing ICL miss (was equally-wrong LAYOUT_WRAPPER), Stage B reclaims.
- **CRITICAL audit fix — label-distribution KEY COLLISION + full re-verify.**
  `label_distribution_snapshot` keyed by `vol/page_start/path` with no
  article id.  Many EB1911 articles share a page_start (GERMANTOWN + GERMANY
  at 11/825), so co-located articles COLLIDED on every shared tree path and
  silently overwrote.  Impact was large: collision-free count **341,055** vs
  colliding **239,417** — **~30% of elements were hidden**, so every prior
  diff (incl. the "0-transition" inert proofs) covered only ~70%.  Surfaced
  by the 79-vs-84 two-method gap (snapshot dict vs audit loop) — the lesson
  is don't defer a small counter divergence; small gap, large blast radius
  ([[feedback_verify_the_counter]], [[feedback_audit_code_discipline]]).
  Fixed: key now includes `art.id`.  Re-verified at full coverage — reverted
  to 3bb1b37, captured `fix_orig` (341,055), restored, captured `fix_cur`,
  diffed → **67 transitions, ALL LAYOUT_WRAPPER exits, 0 others.**  So
  ICL+poem are inert over FULL coverage (not just the visible 70%), Stage A
  confirmed, and the two methods now AGREE (both 84).  **`fix_cur` is the
  trustworthy collision-free baseline now; the colliding `stepb_*` /
  `art_base` snapshots are OBSOLETE.**  (Earlier "239,417" / "≤572" /
  `art_base` references above are pre-fix; true total ≈341k, and the ≤572
  figure-group bound must be recomputed on `fix_cur` near Step C.)
- **Stage C — `_is_layout_wrapper`'s POEM-only branch REMOVED (invalid
  signal), VERIFIED.**  "Only POEM children" is also invalid — a data table
  can carry a poem cell.  Genuine verse-wrappers are claimed upstream by
  `_is_poem_wrapper_pred` → VERSE_TABLE; the leftovers reaching this branch
  were all data-tables-with-poem.  Diff (`fix_cur` vs `stepb_lwC`): **9
  transitions, ALL `LAYOUT_WRAPPER → {DATA_TABLE 5, COMPLEX_HTML 4}`, zero
  to VERSE_TABLE, zero collateral.**  Render-verified NUT (4-col
  `Name/Source/Locality/Remarks` grid, poem = Name column) and TEA (variety
  table, poem = sub-races) are genuine data-tables-with-poem.  **LAYOUT_WRAPPER
  84 → 17 (Stage A) → 8 (Stage C).**  `_is_layout_wrapper` now has only its
  IMAGE branch left.
- **ICL-outlier inventory COMPLETE (the remaining 8 + the figure cohort).**
  The 8 LAYOUT_WRAPPER holdovers are all image-bearing figure misses, and
  they resolve to a small, finite set of micro-shapes that converge on ONE
  root — the figure family's component extraction is too rigid
  (`_classify_icl_shape` single-image case returns CAPTIONED_FIGURE only when
  `_image_alone_in_row`, else None):
    * BAG-PIPE×2 — image + `<ref>` footnote(s), no caption (gate=1, sub=None).
    * EGYPT — image + HIEROGLYPH sibling (gate=1, sub=None).
    * ALGAE — image in the `|+` slot + full A–R legend + attribution
      (gate=0: the `|+` caption anti-signal fires on an image).
    * EUROPE / ORGAN — image, gate=0 (anti-signal / carrier miss, TBD).
    * MARSUPIALIA (now in SINGLE_COLUMN, not LAYOUT_WRAPPER) — two-level
      NESTED figure: outer wraps inner[image+attribution] + a separate
      caption row → attribution-as-caption + caption-leaks-to-body.
    * CHESS×2 (DEFERRED) — image + substantive PROSE; possibly a layout-
      unwrap (prose→body, image→figure), maybe not a figure at all; 3+
      plausible readings, decide later.
  Conclusion: do NOT micro-patch each sub-shape (rule-of-three → additive
  anti-pattern).  The total-function fix is the **`_extract_figure_components`
  raw rebuild** (the figure-family analog of the table recursion) — one
  extractor robust to whatever a figure table contains (image→figure,
  `<ref>`→footnote, attribution→attribution, caption→caption, nested→recurse),
  covering BAG-PIPE/EGYPT/ALGAE/MARSUPIALIA together.  Diagnostics:
  `tools/_scratch/inspect_marsupialia.py`, `inspect_lw_holdovers.py`,
  `inspect_element.py`.
- **Figure Step A DONE — raw, recursive figure-component extractor
  (`_figure_decompose.py`), additive/inert.**  `extract_figure_components(raw)`
  → `FigureComponents(images, caption_parts, attribution_parts, legend_lines,
  footnotes)`, RECURSING into nested figure-tables to GATHER (not finalize)
  their components — reusing the table machinery (`extract_wiki_rows`,
  `find_nested_table_spans`) for the nesting, figure-typing layered on top.
  Direct-feed tested (`tests/unit/test_figure_decompose.py`): **MARSUPIALIA**
  (two-level nested → image + attribution from the inner table, caption from
  the outer row; attribution NOT mistyped as caption — the central nesting
  bug fixed at the owning layer) and **BAG-PIPE** (image + 2 footnotes,
  spacer/`<br>` noise filtered).  Not wired into any producer yet.  The figure
  analog of table Step A; proves "recurse in the extractor" on the hardest
  case.  `_assemble_figure_parts` stays unchanged — all the work is extraction.
- **Figure legend descent DONE + VALIDATED byte-identical vs production.**
  Structural rule (`_gather_legend_table`): a no-image nested table inside a
  figure → LEGEND; an image-bearing nested table → recurse as a sub-figure.
  Plus full "recurse all the way down" — the whole legend-table inner is fed
  to the REUSED `_emit_legend_chunk`, so table → poem → per-entry descent
  yields clean `### Subhead.` + `A. …` lines, not a flattened blob.  Caption-
  unwrap fix too (`{{center|…}}` no longer fragments off as junk at the Fig
  split).  **Validated on the full untrimmed ABBEY Fig. 3** (the gnarliest
  legend in the corpus; `tools/_scratch/compare_abbey_fig3.py`): 49 legend
  lines, all 3 csc sub-heads, the full label zoo (FF / X₁X₁ / P₁ / italic
  a–z / `<br>`-folded continuations) — `only in PROD: []`, `only in NEW: []`.
  Fig. 3 is also a *working* figure, so matching it exactly = the approach
  handles full complexity AND won't regress the working set.  Reuse paid off:
  `_emit_legend_chunk` agrees with production's `_extract_poem_legend` here.
  Still additive/inert (not wired into any producer or the gate).

### Next steps
1. **Legend grammar — the LOOSE (non-table) case.**  The TABLE-legend case is
   done and validated (above).  Remaining is a label-ladder sitting LOOSE in a
   cell (not in a clean table) → legend — the "better than production" part,
   for figures whose legend isn't tabular (ALGAE's A–R).  Reuse the ladder
   grammar (`_LEGEND_ENTRY_RE` / `_entries_look_like_legend`); default-safe to
   caption when it's not a confident ladder (no-drop).
   `feedback_hard_means_unencoded_knowledge`.  EGYPT (image+hieroglyph) is the
   other next direct-feed case.
2. **Wire the extractor (figure Step B/C).**  Gate recognizes
   image-anywhere-in-raw (so MARSUPIALIA *routes*, not just extracts); figure
   producers read `extract_figure_components` instead of `inner_registry`;
   `_assemble_figure_parts` unchanged.  Verify on `fix_cur`: figure cohort →
   ICL labels AND the ~4,100 already-correct figures DON'T move (inertness for
   the working set), render-checked.  CHESS still deferred.
3. **Finish `_is_layout_wrapper`** — once ICL claims the figures, drop its
   remaining IMAGE branch + POEM-only branch (likely already dead — poem-
   wrapper runs first) and delete the predicate + dispatch entry: the 95
   lines and the `*300` content-length heuristic gone.
4. **Step B, chem/math predicates** — `_has_chem_brackets(registry)` and
   `_is_math_dominant_layout(…, registry)` also read the registry; each
   denests to a raw scan.  (So "fix the classifier" is a known roster of
   ~6–8 predicates, not "maybe none.")
5. **Step C prep — `inner`-consumers (inert no-op pre-flip):**
   `_is_single_column_table` / `_is_verse_table` / the per-cell checks
   read *placeholderized* `inner` via `_table_grid`.  They read no
   registry, but at the flip `inner` arrives raw and `_table_grid`
   miscounts nested-table pipes — add `_mask_nested_tables_all` so they
   stay correct.  (The flip changes TWO things per element: registry→{}
   AND inner_text placeholderized→raw; both consumer classes must migrate.)
4. **Step B, producers** — `_process_table` / `_process_html_table`
   `inner_registry` reads → raw discovery (Step A's `recurse` wired in);
   `_extract_figure_components` raw rebuild (placeholder/registry-bound)
   so predicate + producer share one raw extractor.
5. **Refs — the global exception** — `<ref name=X/>` reuse resolves
   article-wide (`resolve_ref_bodies` walks the tree).  Flipping a family
   that contains refs (table cells, figure captions/legends) puts those
   refs off-tree, so tree-based resolution misses them.  Ref-*definition*
   collection must become a global raw pre-scan feeding every recursive
   invocation — the one place the locality invariant genuinely doesn't
   hold (see [[feedback_recursion_at_the_right_layer]]).
6. **Step C flip — table family:** add SHAPE_BRACE_PIPE / `<table>` to
   `LEAF_SHAPES`; diff `art_base` vs post-flip; the ≤572 figure-group
   reclassifications are the deliberate, signed-off transition.

---

## Earlier focus (2026-05-28) — Math labelled-equation lift + contributor footers + NOINCLUDE elimination + cross-page table bounding

**Goal:** Drain the `_strip_templates` catch-all by giving every template an
explicit owner.  Three architectural moves landed this session, each tied to
an audit hit cluster: lift block-level labelled-equation templates (the math
half of the audit), lift contributor footers (the 8k-deletion bucket), and
eliminate NOINCLUDE as an element entirely (the chrome bucket plus the cross-
page table cell-row Ts leaks).  Net: 11,964 → 2,666 strip-template deletions
this session (−9,298), with structural improvements that drained the orphan-
markup phases too (phase 6 `|-` orphans 1,809 → 202 — cross-page table cell
rows now correctly bounded).

### Snapshot scoreboard
- **346/346** unit + regression + snapshot tests passing.
- Snapshot regression net unchanged (20/20); all extension work landed byte-
  identical with the legacy paths for the patterns the snapshots cover.

### Architectural principles clarified (memory)
- **`feedback_walker_only_lifts_declared_structure`** — the walker lifts what
  the source structurally declares (named-template wrapper, HTML tag).
  Inline typography whose rendered output flows back into prose stays in
  body-text — its CONTENT isn't a chunk, its OUTPUT is.  Lifting inline
  typography breaks the surrounding processing that depends on its rendered
  bytes (the `<sup>{{sfrac|1|n}}</sup>` regression that surfaced this
  principle).
- **`feedback_dual_use_template_discriminator`** — `{{rh|…}}` /
  `{{RunningHeader|…}}` etc. carry DUAL semantics in EB1911 source: page
  chrome inside `<noinclude>`, inline content layout outside.  Same template
  NAME, different ROLE keyed on noinclude wrapping.  Producer logic that
  ignores the discriminator (e.g. blanket strip the template name) corrupts
  inline content.  STEAM_ENGINE's `{{rh|or|equation|}}` centring an equation
  is the canonical case.
- **`feedback_walker_recognizers_explicit_names`** — the walker may
  enumerate template names it bounds (each is structurally bounded;
  enumeration is part of bounding, not classification).  But comments /
  variable names must describe what the recognizer DOES structurally, not
  what FAMILY the templates belong to — the classifier owns labels.  My
  initial `_MATH_TEMPLATE_NAMES_PATTERN` violated this; renamed to
  `_LABELED_EQUATION_TEMPLATE_NAMES_PATTERN` (structural, not family-named).

### Math labelled-equation lift (#equation/#MathForm1/#ne)
- Walker recognizes `{{equation|…}}`, `{{MathForm1|…}}`, `{{ne|…}}` as
  SHAPE_DOUBLE_BRACE via `_LABELED_EQUATION_TEMPLATE_OPENER_RE` +
  `_find_balanced_template_end` (balanced-brace scanner that masks
  `<math>` / `<nowiki>` / comments — `ne` carries LaTeX content with
  literal `{`/`}` that a `[^{}]`-based regex couldn't span).
- Classifier dispatches the three template names to MATH_EQUATION /
  MATH_FORMULA_LABELED / MATH_NE labels.
- ONE producer (`_process_math_equation` in `elements/_math.py`) handles
  all three labels keyed on template name — per-template arg parsing
  internal to the producer (equation has `tag=` / `pretext=` named params;
  MathForm1 is label-first; ne has three arg shapes: bare, empty-label-
  content, empty-label-content-label).  Output marker `«EQN:LABEL»content
  «/EQN»` with `\n\n` paragraph margins.
- **Inline fractions stayed in body-text.**  Initially attempted walker-
  lift for `sfrac` / `frac` / `mfrac` / `over` / `sfracN` / `EB1911 sfrac`
  / `EB1911 tfrac` / unicode-name variants → broke `<sup>{{sfrac|1|n}}</sup>`
  cases because lifting the inner template put a placeholder inside the
  outer `<sup>` and `_convert_sub_sup`'s translation can't see across.
  Reverted; instead extended body-text's iterative fraction handler in
  `_apply_markup` to cover all 11 corpus variants (previously only
  `sfrac`/`sfrac nobar`/`frac`/`EB1911 tfrac`).  Inline typography stays
  in body-text — the principle that fell out.
- Body-text deletes: dead `_convert_sfrac` (line 129), iterative
  `_ne_labeled` regex block, the `{{equation|}}` and `{{ne|}}` raw-text
  handling.  Body-text no longer owns any math rendering.
- Audit eliminated: equation (29 → 0), MathForm1 (15 → 0), ne (48 → 0),
  sfrac nobar (62 → 0), frac (27 → 0), sfracN (26 → 0), mfrac (2 → 0),
  over (5 → 0), EB1911 sfrac (31 → 0), EB¹⁹¹¹ variants (67 → 0),
  EB₁₉₁₁ ₜfᵣₐc (2 → 0) — ~314 total.

### Contributor-footer lift (~8,290 audit hits eliminated)
- `_CONTRIBUTOR_FOOTER_RE` in walker recognizes `{{EB1911 footer initials|
  …}}`, `{{EB1911 footer double initials|…}}` and the ~20 bare-initials
  shortcut variants (`{{EB1911 TAs}}`, `{{EB1911 WABC}}`, `{{EB1911 JF-K}}`,
  `{{EB1911 HWR*}}`, …) via enumerated alternation + balanced-brace
  bounding (footer-initials forms) or bare-template close (initials
  shortcuts, max 5-char suffix with mixed-case + asterisk/hyphen).
- Classifier returns CONTRIBUTOR_FOOTER for name == "eb1911" (walker only
  lifts contributor footers for that name token, so the discriminator is
  safe by construction).
- Producer returns "" — `extract_contributors` reads the same raw template
  in its own pipeline stage to populate the contributors table, so body
  output renders nothing for these.
- Audit eliminated: 8,072 + 157 + ~60 + 1 (typo `footer  initials` double-
  space) ≈ 8,290 silent-strip deletions.

### NOINCLUDE elimination + cross-page table bounding (the big architectural move)
- **What NOINCLUDE was doing** (before this session): walker element that
  claimed `<noinclude>…</noinclude>` blocks; producer dropped chrome
  content silently (anti-pattern — identical mechanism to `_strip_templates`
  but at a different layer) and attempted to preserve `{|`/`|}` cross-page
  table markers (which its own docstring admitted didn't work because the
  re-emitted markers ran AFTER walker, so they never got paired).
- **What replaced it:** `_transform_text_v2` strips `<noinclude>…</noinclude>`
  BLOCKS wholesale upstream (tags + content), preserving `{|<attrs>` and
  `|}` lines as naked bytes in body raw.  BRACE_PIPE then pairs them
  naturally via its existing scanner — cross-page tables become one
  bounded element.  Inside that element, `_process_table` consumes Ts
  styling in cell-attr position correctly via the existing
  `_extract_table_cells` flow.
- **`SHAPE_NOINCLUDE`, `_NOINCLUDE_RE`, `_process_noinclude`, the dispatch
  entry, the `_noinclude.py` module: DELETED.**  Walker has one less concept.
- **`<pagequality level=… user=… />` self-closing tag** added as a walker
  recognizer (sibling to `<ref name=X/>`) with classifier label PAGEQUALITY
  and empty producer — previously consumed inside NOINCLUDE, now needs its
  own explicit owner.
- **Dual-use templates preserved.**  `{{rh|or|equation|}}` (STEAM_ENGINE's
  centred equation continuation) stays in body as content because the
  block-wipe operates on the noinclude WRAPPING, not the template name.
  Page-chrome `{{rh|XL|TITLE|XL_PAGE/XL}}` was inside `<noinclude>` and
  drops with the block; inline-content `{{rh|…}}` was outside `<noinclude>`
  and survives.  The structural discriminator (in or out of noinclude) is
  preserved by where the block boundary falls.
- **Plate pipeline untouched.**  The block-wipe is in `_transform_text_v2`,
  on the article-only branch after the plate-vs-article fork in
  `transform_articles`.  Plate-title extraction in `parsers/plate/` still
  reads raw bytes including `<noinclude>` headers and finds
  `{{x-larger|TITLE}}` inside.
- **Test infrastructure fix.**  `tests/regression/conftest.py` updated to
  import `detect_boundaries` from its new home in `super_detect.py` (last
  session's rename left the conftest broken).  The 18 abbey/alloys/blank_verse
  regression tests went from pre-existing-failure to passing without any
  real regressions surfacing.

### Audit progression this session
- Session start (post-prior-session): **11,964** strip-template deletions
- After math labelled-equation lift + body-text fraction extension:
  **11,648** (−316, math families cleared)
- After contributor-footer lift: **3,354** (−8,294, footer family
  cleared)
- After NOINCLUDE elimination + block-wipe: **2,666** (−688, chrome
  consumed by block-wipe + Ts 1,107 → 554 because cross-page tables now
  bound properly + Phase 6 `|-` orphans 1,809 → 202)
- **Net session reduction: 11,964 → 2,666 (−9,298 strip-template deletions).**

### What remains (separate future campaigns)
- **Ts** (554 remaining) — HTML-attribute leaks (`<div {{Ts|…}}>`,
  `<td {{Ts|…}}>`, `<span {{Ts|…}}>` etc.) outside wikitable cells.
  Different leak class from the cross-page-table cell-attr cases just
  fixed.  ~282 inside body-prose HTML wrappers, ~169 inside HTML table
  tag attrs (`<td>` / `<tr>` / `<table>`), 10 misc.
- **sfrac** (76 edge cases) — nested-content fractions the iterative
  pass can't unwrap (carries `{{overline|…}}` etc. inside).
- **Cross-reference templates** (~250 hits) — `lkpl` (73),
  `intra-article link` (45), `cite` (29), `9link` (13), `EB1911 article
  link` (16), etc.  Content-loss bugs (link target + display text both
  deleted).
- **Foreign-script content** (~110) — `Polytoⁿⁱc` (46), `pₒₗyₜₒₙᵢc` (45),
  `Greek` (13), `arabic` (9), `he` (7), `latin` (6), `coptic` (1).
  Actual non-Latin characters being deleted.
- **Inline typography decorations** (~1,500) — `x-smaller`, `underline`,
  `smallcaps`, `word-spacing`, `strikethrough`, `nw`, `fs70`, etc.
- **Phases 2-6 orphan markup** — phase 3 (`}}` excess) 522, phase 4
  (`|}` orphans) 36, phase 5 (`{|` orphans) 28.  Down significantly from
  pre-session but each remaining instance is a producer leak to track.

### Memory deltas
- New: `feedback_walker_only_lifts_declared_structure`,
  `feedback_dual_use_template_discriminator`,
  `feedback_walker_recognizers_explicit_names`.

---

## Prior focus (2026-05-27) — Sweeper architecture / element-promotion pattern + dual_line as walker element + chem/math family classification

**Goal:** Internalise the sweeper-antipattern principles, fix several
sweepers at the source, then prove the element-promotion pattern by
moving `{{dual line|…}}` out of body-text and into the walker /
classifier / producer triple — with chem and math now owning their
own dual_line content via family predicates.  Three architectural
insights captured as feedback memories; one significant refactor
landed byte-identical; the audit's top names are now mostly element-
promotion candidates rather than regex-pass candidates.

### Snapshot scoreboard
- **328/328 unit + regression tests passing** (full `tests/unit` + `tests/regression` minus the unrunnable `test_prepare_wikitext.py`).
- AGRICULTURE + STEAM_ENGINE snapshots **rebaselined**: dual_line content recovery (AGRICULTURE: `Hay.|{{brace2|6|u}}` cell was empty pre-fix, now correct; STEAM_ENGINE: `1⅓ lb` was lost, now preserved).

### Architectural principles captured (memory)
- **`feedback_sweepers_hide_bugs`** — INVARIANT, not heuristic: EVERY
  downstream regex/cleanup pass on producer output is hiding an
  upstream bug.  100%, not "often."  Raw source has no redundancy by
  construction → any redundancy/wrong-byte downstream was introduced
  by us → a sweeper deleting it is, by definition, hiding the producer
  bug.  The "this one is benign" feeling is the warning sign, not the
  exception.
- **`feedback_element_production_in_body_text`** — adding a `_convert_X`
  regex pass to body-text's `_apply_markup` for a content-bearing
  template is element production smuggled into the wrong producer.
  The walker should recognize that template as its own element; a
  dedicated producer should render it.  Without walker-level
  recognition, the classifier has no bounded unit to inspect, which
  blocks family routing (chem / math).  Granularity is the gate.
- **`feedback_orthogonal_problems`** — a single surface symptom can
  hide two distinct problems sharing a venue.  Decompose into
  orthogonal problems BEFORE proposing a fix.  Worked example:
  `{{dual line|…}}` audit hits were TWO problems — layout primitive
  (body-text's job, fixed via reorder+balance-brace) AND chem content
  routing (walker-element promotion's job, separate work) — and
  conflating them was the trap.

### ACCURSIUS / detect_boundaries consolidation
- **Bug:** `ACCURSIUS (Ital. Accorso), FRANCISCUS` article body
  opened with `(Ital. Accorso), FRANCISCUS …` — title-bold leaking
  into `segment_text`.  Tracked through layers (`_strip_redundant_title`
  sweeper hiding it) to a 1-character fix at `super_detect.py:119`:
  `parts = _PAGE_RE.split(content)` should have been `…split(body)`.
  `produce_title()` was returning the title-stripped body; the chop-up
  step then ignored it and split the raw content, re-packing the title-
  bold into seg 0.  Body-postprocess sweeper masked the bug.
- **Cleanup:** legacy 299-line per-page `detect_boundaries()` deleted
  from `pipeline/stages/detect_boundaries.py`; `super_detect_boundaries`
  renamed to `detect_boundaries` (only one function in the codebase
  now).  `persist_articles()` kept pure (no implicit wipe);
  `wipe_articles(volume)` added as an explicit public utility; CLI
  `detect-boundaries` and `tools/pipeline/rebuild_volume.py` both
  wipe-then-persist explicitly.  `_wipe_articles_only` duplicate in
  `rebuild_volume.py` deleted.

### Sweeper-elimination playbook applied
- **`_strip_redundant_title`** (body-postprocess) — deleted.  The
  upstream chop-up fix above made it unnecessary.
- **`_patch_img`** (export sweeper) — deleted earlier in same session
  arc; exposed real classifier gaps for figure family (#65/#66/#67)
  rather than being silently absorbed by the sweep.
- **`_strip_templates` catch-all** — focused handlers landed for
  `dual line` (later promoted to element — see below), `lb-` (446
  corpus hits), `overline` (290), `spaces` (289), `0` (247),
  `anchor+` (73), `sp` (72).  Each handler is a producer-level fix:
  recover the bytes the catch-all was deleting.  Combined: ~2000 strip-
  template victims now route to correct rendering.

### dual_line walker-element promotion (#76 + #77)
The reference implementation of the element-promotion pattern,
applied to `{{dual line|A|B}}` (611 corpus instances across 60% math
/ 9% chem / 22% plain layout / 9% scattered):

- **Walker (`elements/_walker.py`)** — `_DUAL_LINE_RE` (4-level brace-
  nesting tolerance, matching `_IMAGE_FLOAT_RE` depth) registered as
  `SHAPE_DOUBLE_BRACE`; opener hint extended.
- **Classifier (`elements/_classifier.py`)** — `_derive_double_brace_label`
  recognizes `dual` template name; consults `is_chem_dual_line` then
  `is_math_dual_line` predicates on the inner content; returns
  `CHEM_DUAL` / `MATH_DUAL` / `DUAL_LINE` accordingly.
- **Plain producer (`elements/_dual_line.py`, new)** —
  `_process_dual_line(inner, text_transform)` does brace-balanced
  top-level-pipe split, drops leading style decoration, strips raw
  args before transform (so decoded entities like `&numsp;` → U+2007
  survive as content), emits `A<br>B`.
- **Chem family (`elements/_chem.py`, new)** —
  `is_chem_dual_line(inner_text)` uses the existing
  `_chem_normalize` + `_is_chem_formula` machinery from `_tables.py`
  (same element-aware test the table classifier uses for
  `CHEMISTRY_LAYOUT`).  `_process_chem_dual_line(inner, tt)` delegates
  to `_process_dual_line` for now (byte-identical); future chem-
  specific rendering goes here.
- **Math family (`elements/_math.py`, new)** —
  `is_math_dual_line(inner_text)` checks for italic-variable spans
  (`«I»…«/I»`) or sub/sup markup, AFTER chem has had first claim
  (sub/sup ride on element symbols in chem context, on variables in
  math context).  `_process_math_dual_line(inner, tt)` delegates to
  `_process_dual_line` for now.
- **Body-text (`transform_articles/body_text.py`)** — `_convert_dual_line`,
  `_DUAL_LINE_OPEN`, `_split_top_level_pipe` ALL DELETED.  The
  smuggled-in producer is gone; the deferred-content-bearing-handlers
  comment updated.  `_apply_markup` shrinks.

**Classification result** (corpus-wide, 611 dual_lines): 58 CHEM_DUAL
+ 264 MATH_DUAL + 294 plain DUAL_LINE.  322 dual_lines now route
through family producers; the remaining 294 are plain-layout cases
(table headers, hyphenations, figure-caption splits) that legitimately
stay with the layout producer.  Output is byte-identical to pre-
promotion (family producers all currently delegate to the shared
layout producer).

**Why this matters architecturally:** before promotion, body-text was
silently rendering chemistry and math content via `_convert_sub_sup`
and other regex passes that lived in body-text but explicitly handled
chem/math forms (per `_convert_sub_sup`'s own docstring: "for
chemistry formulae and math variables/exponents").  Body-text was
hosting two foreign producers in disguise.  Now CHEM and MATH have
their own modules, predicates, and (initially trivial) producers —
future specialisation (formula validation, KaTeX, structural-formula
layout) has a clear home and won't ever touch body-text.

### Memory deltas
- New: `feedback_sweepers_hide_bugs`, `feedback_element_production_in_body_text`,
  `feedback_orthogonal_problems`.
- Updated index entry: prior `feedback_walker_before_producer`
  remains relevant; now reinforced.

### Next session — `_strip_templates` long tail
Audit's top names after dual_line promotion: `ts` (31, orphan-Ts), `nw`
(16, non-wrap), `sfrac nobar` (9, math fraction), `nopt` (8),
`font size` (8, math typography), `xxxx-larger` (6, math symbol),
`smallcaps` (4 — should be «SC» path), `u` (3, underline), and the
long tail.  Each will get triaged by the now-canonical question: is
this a sweeper masking an upstream bug, an element to promote
(walker-level), or a legitimate decoration handler?  The user's
observation: "we'll have moved just about everything into the
producers, or even lower down, into the extractors."

---

## Current focus (2026-05-26 evening) — Ts styling end-to-end + post-rebaseline regression-net recovery + Tier-1 sweeper-audit dismantling

**Goal:** Carry source `{{Ts|…}}` styling through the producer to viewer (cell
*and* opener level, all wikitable producers); then recover the regression-net
signal that an earlier wholesale rebaseline silently destroyed; then audit and
delete the post-producer marker-mutating sweepers the audit flagged as Tier-1
"garbage that must go."  Three workstreams in one session.

### Snapshot scoreboard
- **20/20 snapshot regression tests passing** (`tests/regression/test_transform_snapshots.py`).
- **346/346 unit + regression tests passing** (full `tests/unit` + `tests/regression`).
- Earlier in session: 11/20 → all green via 5 producer-bug fixes, then verified-clean wholesale rebaseline.

### Table-Ts styling — end-to-end (tasks #36/#37/#39)
- **`_cell_styles` toolkit** in `elements/_tables.py` extracts FULL per-cell CSS
  (HTML `align=`/`valign=`/`style=` + `{{Ts|…}}` shorthand) into a list applied
  via `emit_html_cell(…, styles=)`; previously cell styling was dropped on the
  floor.  Plumbed through `_process_complex_table`, `_process_html_table`,
  `_process_chemistry_layout`.
- **Table-opener Ts** — `{|<attrs>` line carries whole-table styling
  (`{|{{Ts|ma|sm92|lh12}}` etc.).  `_table_opener_styles(raw)` extracts it;
  HTMLTABLE / CHEM producers apply it inline as `<table style="…">`; the
  `{{TABLE`/`«PRE`/`{{VERSE` markers gained an optional `[style:…]` slot that
  the viewer reads.  All five wikitable producers now accept `raw` (signature
  change from `(inner, …)` to `(raw, inner, …)`).
- **Paragraph-Ts** — body-text `<p {{Ts|ac}}>…</p>` shape now emits `«CTR»…«/CTR»`
  marker for centred prose.  Center variants (`{{c|}}`/`{{block center|}}`/
  paired `c/s`/`c/e`) all converge on `«CTR»`.
- **Wikisource Module mirror** — `_parse_ts_codes` re-implemented as a direct
  lookup against the wikisource `Module:Table_style/styles` (262 entries) +
  `/aliases` (232 entries), converted via `tools/_scratch/lua_to_py.py` and
  embedded as `elements/_ts_codes.py`.  Replaces a hand-rolled regex chain that
  had wrong scales for `w<N>` (em→%), `m[lrtb]<N>` (em→px), and treated
  `pl15` literally instead of as decimal-encoded `1.5em`.  Adds "missing
  period" heuristic for `pl15`/`pr15`-style shorthand the Module doesn't
  define (1261 corpus occurrences).

### Post-rebaseline regression-net recovery (tasks #38, #46-#50, #30)
**The disaster:** earlier-session wholesale rebaseline (commit `3707dda`)
froze ~40 regressions into 13 snapshot baselines as "expected output."  Tests
went green against the corrupted baseline — full signal loss.

**Recovery method:** diff every rebaselined article against the trusted pre-
rebaseline state (`3707dda^`) via subagent audit, tag each hunk
improvement/regression/neutral, fix each regression at the producer, then
re-baseline ONLY after a verification pass confirmed clean.  Six producer-bug
families fixed:
- **MATH_SEAM / FN_SEAM** (#46, #30) — `«/MATH»; …` / `«/FN»; …` punctuation
  swallowed by `^[:;]+\s*` MULTILINE strip firing on walker-induced fragment
  starts.  Strip narrowed to `^:+\s*(?=\(\d+\))` (equation-indent shape only);
  moved into `_transform_body_text` (initial pre-walker move killed outlines,
  caught by verification pass).
- **PADDING_SCALE** (#47) — see Module-mirror above; `pl15` now correctly
  `1.5em` (was `15em`).  Incidentally fixed `w50` (50% not 50em) and `mt5`
  (5px not 5em) since the Module table covers everything.
- **CELL_STYLES_INHALE** (#48) — `_cell_styles` scanned `attr_part + content`,
  hoisting inner `<span style="…">` declarations onto the cell.  AFRICA
  shipped `border-bottom:1px dashed red` from an annotation span; ALDEHYDES
  duplicated cell content after a malformed inline span.  Scoped to
  `attr_part` only.
- **FINE_WRAP_BREAK** (#49) — `<!-- col. 2 -->` HTML column-break comments
  triggered paragraph breaks mid-sentence (ORDNANCE: `1429, and\n<!-- col. 2 -->\ninto England`).
  Comment-strip now newline-preserving (keeps longer adjacent newline run).
- **TABLE_TO_PRE_FLATTENS_ROWS** (#50) — reflow's PRE/VERSE protect/restore
  regexes didn't match the new `[style:…]` slot; row separators inside
  styled PRE markers got flattened to spaces.  Regex updated.

**The principle that landed:** [[no-wholesale-rebaseline]] — always produce a
tagged diff and get sign-off before writing new baseline bytes.

### Tier-1 sweeper-audit dismantling (tasks #40, #41)
**The audit** (post-producer marker-mutating sweepers) identified
`legend_promote.py`'s promotion family (`_promote_paragraph_legends`,
`_promote_legend_verses`, `_promote_legend_tables`, `_fold_image_attribution`,
`_append_attr_to_img`, `_try_convert_with_attr`, `_try_convert_verse_simple`,
`_bundle_raw_image_with_caption`) as the densest concentration of "garbage
that must go" — exactly the post-classification relabel anti-pattern
([[no-post-classification-relabel]]).

**Finding:** every top-level symbol was imported into `transform_articles/__init__.py`
but NEVER CALLED.  Dead code preserved by the old "leave it around in case"
directive; the user reversed that directive after seeing the rot.
[[delete-dead-code]] captured the new principle.

**Deleted:** `legend_promote.py` entirely, the import block (lines 45-77 of
`__init__.py`), the `tools/_scratch/audit_legend_promote_usage.py` audit
script, and the stale `# ── Figure walker` comment block.  20/20 snapshot
tests held — confirming no live dependency.

**Tier-1 #41 — nested-TABLE inlining** (`_inline_nested_table_markers_in_htmltable_blocks`):
moved from a post-substitution sweep in `_classifier.py:437` INTO
`_process_html_table` as a pre-substitution step on its own DATA_TABLE
children.  The producer now owns the conversion of wiki-table children to
inline `<table>` HTML.  Renamed helper: `_inline_table_marker_as_html`.

### Stale-test cleanup (task #51)
Full-suite run surfaced 7 failures.  1 was an actual breakage from this
session (`SHAPE_FINE_PRINT` dead branch in `_shapes.py:162`, leftover from a
reverted walker-shape attempt — fixed).  6 were stale tests that pre-dated
architectural changes (SHAPE_BODY vocabulary expansion, INLINE_IMAGE rename
of DOUBLE_BRACKET).  All 6 updated to assert current behavior with comments
explaining the architectural shift.  Suite is signal again — a future break
will surface clearly instead of vanishing into a permanent-red noise floor.

### Tier-2/3/4 audit punch list (open)
- **#42** — `_patch_img` in `article_json.py` back-fills empty `{{IMG:fn}}`
  captions from DB; move into FIGURE producer.
- **#43** — `_strip_redundant_title` in `body_postprocess.py` strips the
  duplicate title twice downstream; BODY producer should never emit it.
- **#44** — orphan `\}\}+` / `\{\|` / `\|-` line strippers in `body_text.py`
  L860-873 (dumping ground for table-producer escapes).
- **#45** — orphan-punctuation collapse `,(\s+,)+`→`,` in `transform_articles/__init__.py`
  L302-303 (defensive cleanup for stripped templates).
- **#13** — `_strip_templates` catch-all (Tier-3, ongoing).
- **#78** — INDIGO (vol 14, p514) page-seam wrap renders as a paragraph split.
  Raw: `…phenylglycocoll<ref>…(July 1899).</ref>\n<section end="s2"/>\n␞PAGE:514␞<section begin>(phenyl…`.
  Both `heal_page_seams` wrap rules miss it: the word-anchor rule can't reach
  `phenylglycocoll` across the `<ref>…</ref>` footnote, and the lowercase-
  continuation rule doesn't fire because the continuation starts with `(`.
  So the `\n\n` survives → split mid-sentence.  PRE-EXISTING (the deleted
  `_transform_text_v2` post-pass missed it too — not a regression).  Fix: let
  the seam-wrap bridge skip a complete `<ref>…</ref>` to reach the anchor word.

---

## Prior focus (2026-05-26) — BODY-as-element + catch-all dismantling: `_strip_html` DELETED, `strip_known_wrapper_tags` toolkit pattern established

**Goal:** drive shared catch-all sweeps to zero by making each producer responsible
for its own markup regularization, with shared toolkit utilities composed (not
inherited).  Architectural shift this session: the body-text producer became a
**normal element producer** instead of half-substrate-half-producer.

### BODY-as-element refactor LANDED
- **`SHAPE_BODY`** added; walker emits BODY extracts for every residual prose run
  between extracted elements (`_walker.py::_wrap_body_runs`, gated by
  `_wrap_body=True` at the article entry point only — recursive walks into
  cells/figures pass False).
- **Layout-wrapper-aware splitting** so `{{center|…}}`/`{{larger|…}}`/etc. AND
  `<div>`/`<span>`/etc. wrappers around extracted placeholders stay atomic
  (`_find_atomic_wrapper_spans`).  Without this, `{{center|<math>…</math>}}`
  centered equations would split into two body runs and the brace-counted unwrap
  couldn't pair the wrapper.
- **Classifier** maps SHAPE_BODY → `"BODY"` label; `_PRODUCER_DISPATCH["BODY"]`
  dispatches to a new `_produce_body` wrapper that invokes `_transform_body_text`.
- **`process_elements` simplified:** dropped the `body_transform` parameter and
  the special "body_transform(placeholderized_text)" substrate step.  Article
  assembly is now pure ordered concatenation of element markers — no glue layer,
  no body-substrate.

### `_strip_html` DELETED + Family A wrapper-strip toolkit
- **`_strip_html` deleted entirely.**  The catch-all was silently sweeping any
  HTML tag — including ones that signalled real producer bugs.  Removing it
  surfaced ~14 producer-level leaks that had been hidden.
- **Body `<br>` rule** explicitly owned by `_transform_body_text` (body prose
  `<br>` is a soft line break → space; figure/caption/cell producers own their
  own `<br>` decisions).
- **`strip_known_wrapper_tags(text)`** in `body_text.py` — shared toolkit utility,
  enumerated tag set (`span`, `small`, `big`, `div`, `p`, `ins`).  Explicit list
  so a new wrapper tag in EB1911 source surfaces as a literal tag in output
  rather than being silently swept.
- **Per-producer composition** of the helper, each deciding what to keep vs strip:
  - BODY producer (`_transform_body_text`) — body prose
  - CHEM cells (`_process_chemistry_layout`)
  - Complex-wikitable cells (`_process_complex_table`)
  - REF/FN bodies (`_process_ref`)
  Pattern: each producer knows what markup it needs and what markup it doesn't.

### `_unwrap_layout_templates` brace-counted (Q=V equation fix)
The regex-based version failed when an inner template had an unbalanced literal
brace (`{{xx-larger|√ {}}` in STEAM_ENGINE's Q=V equation).  Replaced with a
brace-counted `_unwrap_balanced` helper that scans `{{` / `}}` pairs ignoring
single braces — `{{center|…}}` now unwraps cleanly even when its content carries
math square-root opening braces.

### Snapshot scoreboard (the regression net)
- Start of session: 16 passing / 4 failing (pre-existing reds)
- After `_strip_html` deletion (catch-all bugs surfaced): 2 / 18
- After Family A toolkit + per-producer composition: **10 passing / 10 failing**

All 6 newly-passing tests that previously relied on `_strip_html`'s silent
sweeping are now passing via explicit producer-owned rules.  Remaining 10 fails
fall into:
- **Enumerable tag leaks** (4 tests): BRACHIOPODA `<br>` (cell context),
  MOLECULE `<sub>`/`<p>`, AGRICULTURE `<tr>`/`<td>`, ORDNANCE table escape
  (168 `<td>` + 24 `<tr>` + 4 `<table>`).  All clean producer-local fixes —
  tasks #21-#23, #22.
- **Content-level differences** (6 tests): ALPHABET, BAG-PIPE, DYNAMICS,
  HYDROMEDUSAE, STEAM_ENGINE, CITHARA.  No tag leaks — these are pre-existing
  reds unrelated to the catch-all dismantling.

### Pattern established (the architectural win)
Every leak that's now visible was previously hidden by `_strip_html`.  Each is
a producer-local fix — exactly what `[[turn-bugs-into-producer-bugs]]` and
`[[no-catchall-cleanup]]` want.  The toolkit pattern (shared utility, producer
composes it explicitly) is the template for `_strip_templates` next (task #13).

### Next on this campaign
- **Task #13** — `_strip_templates` (the surviving catch-all in `_apply_markup`).
  Same shape as `_strip_html` was; enumerate what it actually catches across the
  corpus, route each template to its producer or canonical-marker conversion,
  drive count to zero, delete.
- **Task #18** — split `_apply_markup` megafunction into a named utility toolkit
  that producers compose ad hoc (rather than every producer piping end-to-end
  through one shared transform).  BODY-as-element refactor unblocks this.
- **Task #21** (MOLECULE `<sub>`), **#22** (ORDNANCE HTML-table escape),
  **#23** (BRACHIOPODA cell-`<br>`) — the remaining Family-B per-producer fixes.

---

## Prior focus (2026-05-25) — Honesty campaign: super-walker WIRED + producers on RAW (Stages 1–2 landed; per-family producer queue open)

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

**Family 2 — rendering re-homes (LANDED 2026-05-26).**  Three whole-text passes
re-homed into the text producer `_transform_body_text` (top, before
template/marker handling), so the producer regularizes the source it now receives
raw instead of leaning on Layer A:
- `<!--...-->` strip (`html_comments`) — fixed AFRICA's `<!-- Greenland is
  actually the largest -->` body leak.
- `normalize_unicode` (NFC, subscript-preserving) + `replace_print_artifacts`
  (audited lossless table: `℔→lb`, `℥→oz`, `＝→=`, `＋→+`, …) — fixed
  AGRICULTURE/ORDNANCE/STEAM_ENGINE `℔` glyphs and ALDEHYDES/ACCUMULATOR chem-cell
  `＝/＋` fullwidth glyphs.  Re-baseline was the wrong call: the docstring
  documents these as render-equivalent ASCII substitutions chosen for "font
  portability, copy-paste, and search indexability" — `℔` renders as a box in
  most fonts.  Re-home wins on every axis (search, render, the producer's job to
  regularize); re-baseline would have baked stray glyphs into the canon.

**Family 3 — chem cell comment-strip (LANDED 2026-05-26).**  ACCUMULATOR's chem
producer was leaking column-number markers (`<!--2--><!--3-->…<!--7 -->`) as
bogus cells because `_process_chemistry_layout` parses `<tr>`/`<td>` directly
from raw `inner` — text-producer-level strips never reach it.  Added
`re.sub(r"<!--.*?-->", "", inner, flags=re.DOTALL)` at the top of
`_process_chemistry_layout` AND `_process_html_table` (defensive symmetry — the
HTML-table's generic `<[^>]+>` strip mostly catches comments, but row-splitting
runs first on raw `inner`).  Chem `<table>` cells now match snapshot byte-for-byte.

### Seed-snapshot residual (10 of 20 red — all deferred scope)
After the image family + rendering re-homes + chem-comment strip, the 10
remaining reds split CLEANLY into two deferred families:

**A. Figure-recognition family (4 seeds)** — the walker sees a layout-template
wrap (`{{center|…}}` or float-figure inside prose) and doesn't peer inside, so
the figure-pairing producer never gets the caption+image pair / the paragraph
splits around each float-figure:
| Seed | Shape (raw) | Outcome |
|---|---|---|
| ACCUMULATOR | `{{center|[[File:Fig22]]  [[File:Fig23]]<br>caption}}` | both figures dropped (LAYOUT_WRAPPER, no recognizer) |
| ALPHABET | `{{center|«I»caption«/I»<br>[[File:…]]}}` | caption-before-image dropped (same family) |
| HYDROMEDUSAE | prose with `{{img float|…}}` inline | walker SHAPE_FIGURE break splits paragraph in two; also a NEW-is-better OUTLINE demotion + `inter stitial`→`interstitial` join |
| ORDNANCE | prose with `{{img float|…}}` inline (× many) | same paragraph-split pattern |

All fold into the standing **LAYOUT_WRAPPER drain (~107 mislabels)** + a
SHAPE_FIGURE refinement (keep inline-float figures with their paragraph, only
break standalone ones).

**B. Whitespace-presence (6 seeds)** — table-cell or marker-adjacent whitespace
the producer now receives raw:
| Seed | Shape | Producer to regularize |
|---|---|---|
| AFRICA, AGRICULTURE, ALDEHYDES, STEAM_ENGINE | leading/trailing space in `<td>`/`{{TABLE:` cell | table cell `.strip()` (chem path + html_table path + wiki TABLE marker) |
| DYNAMICS, MOLECULE | whitespace between/before `«EQN»`/`«MATH»` markers | equation/math producer marker-adjacent trim |

Render-equivalent (browsers collapse leading/trailing cell whitespace; inter-
marker space collapses), but the producer should regularize for canonical
markup.  Falls under the standing **table-path purity** + math-producer work.

**Proof the flip lost nothing:** `raw_error=0` corpus-wide; the producer-output
diff (pure-noise filtered) was ~3% real divergence, all bounded to image/figure/
table/chem.  Net: image/figure/table/chem are the work — the SAME producers the
table-path purity campaign (Prior focus) was sharpening, so it folds in here.

**NEXT:** the seed queue has hit the figure-family / table-path frontier.  Next
clean territories are (a) **LAYOUT_WRAPPER drain** (figure recognition inside
`{{center|…}}` wraps — clears ACCUMULATOR / ALPHABET / similar) and
(b) **SHAPE_FIGURE refinement** for inline-float figures (clears HYDROMEDUSAE /
ORDNANCE paragraph-split), and (c) table-cell trim in the producer.  Tests stay
red-then-green per family by design — NOT pushed to production (deliberately,
to keep liberty to break).

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
  ~88 in yesterday's broken deploy); ~3,633 unproofread Wikisource pages.

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

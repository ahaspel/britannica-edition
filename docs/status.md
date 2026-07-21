# Britannica Edition — Status

**Last updated:** 2026-07-19.  Single source of truth for project state.  Snapshot
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

## CURRENT STATE (2026-07-20)

### Session 2026-07-20 — xref-by-KIND · «AL» leak · footnote «template» · perf; SHIPPED + production-verified

The residual xref false-positives root-caused and fixed by resolving each reference by its KIND, plus
a leak fix and two perf wins; a full rebuild (59:08) + deploy landed the whole set on britannica11.org,
**verified on production** (not a local re-render).

- **Xrefs resolve by reference KIND, not one ladder.** The «LN» marker collapsed six raw link forms
  into one, so 6b5 ran a single name-match over embedded wikilinks, `[[Author:]]` citations, and
  asserted EB links alike; `firstword` ("any title CONTAINING the name's first word") then matched
  given-name-first citations against surname-first EB titles (JOHN VENN → McADAM, JOHN LOUDON).
  Measured: 1,075 loose-rung binds, ~89% wrong, 59% naming something EB never covered — so forced-pick
  guaranteed a wrong link.
  - **Embedded links get safe canonicalizations only** (`_XREF_LINK_LOOSE = (fuzzy,)`, no firstword);
    q.v. keeps the loose ladder (EB's own cue asserts an EB target).
  - **Person tier for `[[Author:]]` refs** — 6b4 stops rewriting «AL»→«LN»; the extractor tags them
    `author`; `resolve_person` matches a SURNAME against EB's surname-first titles (particles: Charles
    de Rémusat → RÉMUSAT; initials: W. M. Ramsay → RAMSAY, SIR WILLIAM MITCHELL; richest form only;
    first-given must agree) and ABSTAINS rather than binding a given name. The kind index can't help —
    the dangerous collision IS person-to-person (a modern author's given name vs the saint/monarch of
    that name: BERNARD BERENSON → BERNARD, SAINT).
  - **Self-reference is terminal** unless it carries a section anchor (intra-article jump): 267 → 118,
    all 118 anchored.
  - **Hand-adjudicated ledger** `data/xref_adjudications.json` (git-tracked, accreted like
    `corrections.json`): ONLY `by:user` entries resolve (model verdicts are regression fixtures). Work
    titles → their AUTHOR (Wealth of Nations → SMITH, ADAM; Vanity Fair → THACKERAY) — unreachable in
    code, the link text names no author. Score 81/81.
  - `NameIndex.fuzzy` takes `aggressive` again (was hardcoding the TOC's OCR pass onto inline xrefs,
    296a34a); `superset` binds a single contained word on EB's `Head, Qualifier` inversion (UNIFORMS,
    NAVAL AND MILITARY → UNIFORMS) but NOT without the comma (WEALTH OF NATIONS → WEALTH stays dead).
    **Topic path byte-identical** (populate A/B, all session edits).
- **«AL» leak fixed.** The «AL»→«LN» bake regex used «LN»'s flat `[^«]*` display slot, which stops at
  the first nested marker — so 82 author signatures (`«SC»r. v. h.«/SC»`) never baked and leaked
  through render (which knows «LN» open/close but not «AL»). Widened the three «AL» regexes to 6b4's
  `(.*?)` DOTALL. Corpus: **0 surviving «AL»** (was 82); marker leaks back to the baseline 3.
- **Footnote popup → inert «template».** A footnote body that is a `<table>` (AGRICULTURE fn5) put
  block content in the inline `<sup>`/`<span class="fn-popup">` in the body `<p>`; the parser closed
  the `<p>` at the `<table>` start tag — emptying the popup AND foster-parenting the table loose inline
  (two symptoms, one cause). `render_fn_marker` emits the popup content in an inert `<template>` (its
  own fragment, never closes the `<p>`); `toggleFnPopup` clones it into a positioned popup on demand.
  16 render goldens rebaselined (span→template only). Verified in-browser + on production.
- **Perf — the two laggy pages (user observed ~1s each).** (1) Contributor page fetched + PARSED the
  18.6MB index.json then never read it (a half-finished refactor to contributors.json); dropped the
  dead fetch → renders from contributors.json (1.9MB) only. (2) index.json (18.6MB) exceeds
  CloudFront's **10MB auto-gzip cap** → shipped RAW; `deploy.sh` now pre-gzips it (a stored gzip object
  bypasses the cap; `Content-Encoding: gzip` transparent to `fetch().json()`) → **18.6MB → 2.57MB on
  the wire, verified live**. Article pages were always instant (index.json is off their critical path).
- **SHIPPED + production-verified:** «AL» gone, footnote template live, index.json 2.57MB gzipped
  (7.2×), contributor dead-fetch gone. HuggingFace bundle pushed manually.

**Queued — the leak-cleanup arc (EPUB PRECONDITION).** Residual render-leak tail (51 occ / 0.08%) is
ALL ours; **every leak is a failure to recurse** — `render_leaks.py` reframed as a READ-FLAT detector
([[feedback_leaks_are_core_recursion_bugs]], [[project_leaked_markup_queue]]). Three venues:
section-title→TOC link (`_toc_link`/`_build_toc` do `escape_html(title)` without decoding a title that
is a «LN» — fix: `markers_to_text`); table-cell content not recursed («BAR», `{{nowrap}}`, `{{sc}}`);
link display/target not recursed (`{{sc}}` in `href`/`title`). Then the **EPUB arc** —
`src/britannica/epub/build.py` + `render_article(target="epub")` already produce a valid book (thin
slice); remaining: MathML spike (resolve the Kindle/KF8 risk EARLY — target still emits `«MATHPH»`
placeholder), internal xref links (currently absolute site URLs), topic-TOC nav (only volume browse),
full-corpus build + epubcheck + packaging call. [[project_render_to_python]].

### Session 2026-07-19 (later) — article xrefs through LinkResolver; old cascade retired

The article-xref consolidation ([`docs/xref_resolution_strategy.md`](xref_resolution_strategy.md))
is IN PRODUCTION: Phase 6b5 (`resolve_xrefs_post.py`) resolves every inline xref through the ONE
`LinkResolver` (fill + prose-fish), and the old `xrefs/resolver.py` cascade
(`resolve`/`build_index`/`disambiguate_among`, the LLM xref cache, `hint_kind`/
`matches_disambiguator`, the `resolve_xrefs` stage shim) is DELETED — `build_core_maps` is that
module's one survivor.  **Rebuild-gated** (materializes on the next full rebuild + deploy).

- **Trusted tier (link/q.v.) — always pick.**  `resolve_xref`: Bible/colon target forms, then the
  fill rungs in two tiers (TIGHT exact/alt/fold/subset/superset before LOOSE firstword/fuzzy) over
  BOTH target and display, **more-specific name first**; the fisher keys on a ±140-char prose
  window; the old self-reference rule kept.
- **Untrusted tier (see/see also/cf) — abstain by default.**  `resolve_see`: only a SUBSTANTIAL
  tight match (exact/alt/fold, or subset covering ≥2 content words) that shares the SOURCE
  article's classified-TOC category binds; the shared category doubles as the fisher's bucket.
  The fisher's cosine abstain gate (`trusted=False`) is banked as the resolution-side backstop.
- **Superset guard:** reverse containment (title ⊂ link) needs ≥2 covered content words — kills
  the 1-word component class (BATTLE ⊂ 'Saratoga, Battles of'); 1-word names recover via
  firstword.
- **A/B over the 38,817 materialized records** (production path vs live resolution): link
  **+1,535 gains / −49** (losses dominantly the guard dropping work-title→component junk:
  COMPLEAT ANGLER→ANGLER; ~a dozen diacritic/spelling-variant true losses remain);
  OLD-better changes **88→26**; see survivors **583** clean source-topic binds with **3,618**
  always-pick junk see links dropped.  Topic path untouched by construction (superset/trusted
  are xref-only).  Suite: no new failures (9 pre-existing stale-golden snapshots at HEAD,
  refreeze rides the rebuild).
- **About page folded onto the same resolver + the ONE URL builder** (`render/inline._article_url`)
  — its bespoke lookup fork produced dead `/article/8/0221-e994bf`-style URLs (predates hashed
  stable-ids) and the caps scan split links by re-matching inside them (J.B. Bury, T.H. Huxley) —
  both fixed; SADDLERY→SADDLERY AND HARNESS; collisions pinned (ROUSSEAU, JEAN JACQUES; JAMES,
  HENRY; the ROME treatise).  Verified link-for-link against the old page.
- **Known residue (queued):** singular/plural fill gap (RAILWAY→ATMOSPHERIC RAILWAY over
  RAILWAYS; OILS, BIRD, LIBRARIES — the fill has no stemming, fuzzy fires too late); a few
  paren-alt mis-orders (Senegal→COLONY); ~a dozen diacritic-variant losses (ʽOMAR KHAYYĀM,
  ṢŪFĪISM, MAHOMMEDAN/MOHAMMEDAN).

### Session 2026-07-19 — topic-link resolver redesign (LANDED), 99.3% / 98.6%

Rebuilt `populate_classified_toc.build_resolver.resolve` as FILL / FISH / LOOSEN
([`docs/topic_resolver_redesign.md`](topic_resolver_redesign.md)); wired in and
re-materialized `classified_toc.json`.  **99.3% resolved (was 95%), 98.6% accuracy**
(calibration-corrected against 50 human blind marks).
- **The fisher is where ALL disambiguation lives** (the keystone — see
  [[feedback_fill_dumb_fish_smart]]): bucket CONTEXT (`topic_geo.py` country/state/
  nationality + `topic_subject.py` field/profession — the bucket NAMES the attribute
  and the lead STATES it, a fact not a proxy) → kind → embedding (`topic_fisher.py`
  + `embeddings.py`, fastembed bge-small).  Splits same-name places AND people.
- **Recall is dumb + broad:** word-set FILL, then LOOSEN by the FIRST-WORD rule (any
  article whose title contains the topic's first word → bag → fish).  Coverage
  95%→99%, ZERO regressions; empties 1669→238.
- lead_kind veto (dropped ~150 correct bios) replaced by a deterministic PEERAGE
  detector; ethnic/nature buckets never bind a place.  Deleted dead alias-form code.
- New modules `src/britannica/{embeddings,topic_fisher,topic_geo,topic_subject}.py`
  (+ deps fastembed, numpy).  Cache `data/derived/lead_embeddings.npz` gitignored,
  regenerable via `python -m britannica.embeddings`.
- **Optional leftovers** (user: "the rest is tail-chasing"): the LLM arbiter for the
  tiny same-field residue; 238 unresolved (mostly correct peerage refusals + stray
  section-header entries); a full corpus rebuild + deploy to ship the new TOC.

### Session 2026-07-17 — resolver + contributor consolidation, migrated post-export

The name→article resolution arc consolidated onto ONE kind-aware picker, and the
keystone move: everything that needs the **kind index** (built in Phase 6b3, after
the export) migrated to **post-export patch phases** (the F pattern).  A full local
rebuild (Rebuild 2) is materializing all of the below.

- **F — inline xrefs post-export (Phase 6b4).** The export defers xref resolution
  (`defer_xrefs`): writes raw producer `«LN»` markers + no `rendered_html`;
  `resolve_xrefs_post.py` runs the same resolve→bake→render tail over the exported
  JSONs, AFTER the kind index.  A reorder, not a rewrite; 6b4 replays
  `register_stable_id_dedup` (separate process).
- **C-full — kind-index disambiguation.** `pick_by_kind` gains a `kinds_of`
  supplement (a candidate's topic-bucket kinds ∪ its live lead), threaded through
  `disambiguate_among`→`build_index`; a collision candidate whose opening misleads
  ("on the river X"→river) still qualifies by its bucket.  Degrades to C-core when
  the index is absent.  Adjudicated (agent): the A–E xref changes are **89.8%
  improvement / 5.5% fixable-regression** (residual: fine qualifiers — regnal+realm,
  tribe/place, person-epithet).
- **A2 kind-gate.** A typed topic bucket (Economics>Biographies wants `person`) no
  longer first-wins onto a kind-mismatched decoy when `pick_by_kind` abstains — Léon
  Say / Dover fell to the SAY/DOVER *town*; now a MISS, not a false link.
- **Dirty-title strip.** 24 titles were raw `[[Author:X|NAME]]` / `[[Portal:…]]`
  (the link straddled the title↔body cut, so `_AUTHORLINK` couldn't fire).
  `produce_title` strips the orphaned opening + its orphan `]]`.  Closes the 30
  panel render-leaks AND unblocks DOVER's surname (`GEORGE AGAR ELLIS|DOVER`→`DOVER`).
- **BOGÓ re-slug.** `section_slug` drops accents, so BOGÓ collided with BOG → an
  un-routable `-2`.  `register_stable_id_dedup` now re-slugs the loser on its accent
  FOLD (`Bogó`→`bogo`→`04-0131-c03c3a`, forwarder-routable); numeric suffix only if
  the fold ALSO collides.  Blast radius = 1 article.
- **6b5 — unified post-export contributor resolution.** ALL contributor binding
  moved out of assemble into one post-export phase (after 6b3): signatures (from the
  exported bodies) → **FOOTPRINT** (each contributor's kind profile, from the
  authoritative binds ONLY, so never circular) → vol-29 credits, kind-VALIDATED by
  `contributors/vol29_kind_match.py` (the credit's own disambiguator ∪ the footprint
  pick the article; a kind-mismatched homonym ABSTAINS).  Fixes the ~96 wrong-article
  vol-29 binds a review agent found (Adams-township←historian, Buffalo-city←zoologist,
  Cleveland, Rhea-bird←classicist); Adams *recovered* to CHARLES FRANCIS, Buffalo→the
  animal (via Lydekker's 108-nature footprint), Say J.-B. vs Léon disambiguated.
  140 vol-29 bound, 1155 abstained (miss > false link).
- **Search rewrite (viewer).** One ranked Meilisearch query, accent-folded (shared
  `fold`+`titleRank`+`rankHits` in `search-api.js`), consumed identically by the
  dropdown (top-16) and the full page — so they can't diverge.  Fixes zurich↛ZÜRICH
  and PLATOON-above-PLATO; `home.html` gained a `searchClient` (was title-only).
- **HuggingFace publish is a SEPARATE step** from `deploy.sh`: after a
  content-changing rebuild, also `uv run python tools/publish_hf.py britannica11/eb1911`.

**Pending after Rebuild 2:** bracketed forenames in name-match (SAY, [JEAN BAPTISTE]
LÉON → still bare SAY) + person-broadening (bare surname → the person, now safe under
the kind-gate); the 567 fine-qualifier regressions; a possible contributor-abstain
refinement (1155 is conservative).

---

## RENDER STATE (2026-07-15)

The recursive architecture is in place corpus-wide; this session closed out the
remaining scaffolding (the catch-all preprocess stage, the title double-decider, the
viewer's layout-guessing) and drained several whole leak classes.  **Three principles**
above still govern; every change below is one of *recurse to the end* / *carry the
source* / *render what we carry*.

### Session 2026-07-15 — render collapse: render_paragraph → the mechanical decode_inline

**The body render is now mechanical.**  `render_paragraph` was a flattener — it re-found blocks with
a balanced descent and re-split prose — beside `_split_lines_keep_spans`, which re-derived verse
lines from a flattened string.  Both re-inferred structure the markers already carry.  Fix: move the
block-vs-inline decision UP to the producer.  A sticky `ctx.inline` flag (threaded by `produce_tree`,
set for a TABLE/REF subtree — decoded wholesale by `decode_inline`) lets verse/outline/DHR emit the
form directly — `{{VERSE}}`/`«OUTLINE»`/`«DHR»` at top level, `{{IVERSE}}`/`«IOUTLINE»`/`«DHRI»`
inside a cell/footnote.  The render is then pure token substitution: `decode_inline(body_blocks=True)`
owns every block form in place (page markers, `«SH»`, `«EQN»` grids, `«VERSE»`→blockquote, `«OUTLINE»`,
cols≥10 wide-table wrap) and the browser closes the open-only `«P»`.  No block re-scan, no line
re-split, no span-match regex.

**Deleted** (render): `render_paragraph`, `_find_blocks`, `_fn_span_ranges`, `find_marker_end`,
`_BLOCK_OPENERS`, `_render_outline_block`, `_EQN_PARA_RE`, `_VERSE_BLOCK_RE`, `_IMG_ANCHORED_RE`,
`TABLE_OPEN/CLOSE`, `_TABLE_COLS_RE`, the dormant `dhr_inline` param, and `render/tree.py` (the dead
tree-emitter twin, render_paragraph's only other caller).  Added `_render_title_h1` for the
head-of-body `«TITLE»`.  This is the core of the render-to-Python arc — the `\n\n`-heuristic deletion
+ the viewer-mechanical collapse ([[project_render_rewrite]]).

**Verified.**  Full `--skip-import` rebuild clean (54:45) — corpus render-leak floor UNCHANGED
(`render_leak_marker` 3→3, `render_leak_template` 27→27); suite **419 green**.  Transform snapshots
rebaselined (DHR↔DHRI, adjudicated identical otherwise); render snapshots refrozen from the rebuilt
corpus + regoldened (content preserved by char count, zero leaked markers).  Banked; **rebuild done
`--no-deploy`, deploy pending.**

**Surfaced → queued: footnote popup can't hold block content.**  AGRICULTURE has a table in a
footnote — renders correctly in Notes (block context) but the popup (`<span class="fn-popup">` in a
`<sup>` in a `<p>`) can't hold a `<table>`, so the browser foster-parents it out → empty popup + loose
inline table.  PRE-EXISTING (both old and new render); a popup-DELIVERY bug, NOT a source-render bug
(the marker→HTML render is correct — Notes proves it).  Fix = carry the note body inertly (template /
data payload rendered into a positioned overlay).  [[project_footnote_popup_block_content]]

### Session 2026-07-12 — styler composite · article-wide footnote gather · images+scans off is_local

**Styler producer un-flattened to a COMPOSITE.**  `{{center|…}}`/`{{block center|…}}`/`{{Fine
block|…}}`/… recursed their content to a *marker string* via `process_elements` and returned a
childless leaf — a producer-side flattener, so a nested block (verse/outline/table) inside a styler
was a re-parsed span.  The pipe-form styler is now a composite: `_classify_strip_composite`
decomposes the content into child nodes; `process_strip` substitutes + strips the ASSEMBLED content
(like `_process_cell` — `{{em}}`/`{{spaces}}` padding trims post-produce, an all-empty styler drops).
Body byte-identical corpus-wide; the tree carries styler-nested blocks as real nodes.

**Footnotes gathered ONCE per article.**  `resolve_ref_bodies` is an article-wide gather, but its
only call site (`process_elements_tree`) re-enters at every nesting level, so it ran *per subtree*
with a fragment-local map — the flattener-era footnote scope, silently dropping reuses/continuations
inside table cells and stylers.  Hoisted to a single article pass: it walks the whole tree (recursing
`inner_registry`), and nested `process_elements` INHERIT the finished map via a `ref_bodies=None`
sentinel (`render_fn_marker` already dedups by name).  Recovers dropped footnote anchors/bodies in
**230 articles** (all named/follow-ref) — AGRICULTURE's table-cell `US1` reuses, ALGEBRAIC FORMS /
NEW YORK styler reuses, PEACE CONFERENCES / PO follow-body merges.

**Images: one location-agnostic path.**  Images are extracted source assets, not derived data — so
`data/derived/images/` was a misfiling, and the render's `is_local` branch (`/data/derived/images/`
local vs `/data/images/` web) was a *self-inflicted split* that went imageless locally once the Python
render baked the web path at export.  Unified: files moved to `data/images/`, render always
`/data/images/`, `is_local` dropped from `commons_url`/`render_img`/`_shield_img`.

**Scans: bare anchor.**  Same split a layer down — `_scan_url` baked a full scan URL that
`fixScanHrefs` overwrites wholesale at load (the `back` param is `location.href`, runtime-only).
`_scan_url` + `back_href` deleted; page markers + scan card emit `href="scans.html"`, the JS rebuilds
it.  **`is_local` now steers only article links** (the jsdom-golden stub vs the prod clean URL) — a
real local-vs-web difference, and the only one left on it.

Commits: `26999b4` (styler+footnote), `0aa87b0` (images), `c97d863` (scans); on `50d34ed` (outline
unification — the `:`→OUTLINE recognizer, adjudicated faithful: it honors the author's markup, and
OLD's literal-`:` leak was the actual defect).  Full corpus rebuild in progress to prep the deploy.

### Session 2026-07-07 — {{=}} leak closed · tooltips carry-unless-furniture · normalizer collapse · EPUB arc mapped

**Shipped (full rebuild + deploy, 66:25, exit 0, preflight clean).**  The div-gate (html_tag=92,
the top quality leak) turned out to be the MediaWiki `{{=}}` equals-escape, NOT `{{nowrap}}`:
`<span style{{=}}"…" title{{=}}"…">` leaked as raw text because the three opener regexes key on a
literal `=`.  Fix = one shared `_ATTR_EQ` (`=` OR `{{=}}`) fed to `_SPAN_TITLE_OPEN_RE` /
`_STYLED_WRAPPER_RE` / `_OPENER_HINT_RE`; classifier + producers reuse those regexes, so one edit
fixed the whole chain.  Content `{{=}}` (~1130, math) stays SPACER's post-walk decode — a
context-sensitive decode belongs to the producer that owns the opener context
([[feedback_context_sensitive_is_producer]]); `process_html_style` decodes `{{=}}` in its own
attrs for style-carry.  Live: **0 `style{{=}}` leaks, 0 amended-from leaks** (was ~80 articles).

**Tooltips: carry-unless-furniture.**  `process_span_title` flipped from a Greek/Hebrew
content-proxy to a furniture-title test (`_FURNITURE_TITLE_RE`).  The proxy binned 343
translations + ~100 retroactive death-years along with "amended from" furniture; now every title
gloss carries except transcription furniture — **11,981 tooltips live on hover**
([[feedback_when_in_doubt_carry]]).  Death years render as the faithful `(1838–)` with the year on
hover (tooltip = text unchanged + obviously anachronistic = no fidelity cost, user's call).

**Contributor normalizer collapse — stragglers recovered.**  Unified the three initials-matchers to
the one rich `_normalize_initials`; deleted `_ws_normalize_initials` + the raw-field front-matter
lookup.  Confirmed at the rebuild: `contributors not in DB: 2 → 0` (`W. AY.` Wilfrid Airy + `T. G.
BR.` now fold and match).  Roster 1507 ([[feedback_tune_dont_fork]]).

**Dead code + tests.**  Killed `_TRANSLIT_CONTENT_RE` (dead after the flip) + three false
`strip_attributions` comments (a deleted function describing a superseded footer design —
[[feedback_dead_is_wrong]]).  18 transform snapshots rebaselined the *correct* way
(`_clean_and_heal` on the frozen input, fixtures untouched — NOT `capture`, which drifts input +
double-mangles BRACHIOPODA's quote-run).  Two stale unit tests updated to the current design
(unknown template → `DOUBLE_BRACE_LEAK`, not raise; fuzzy exact-skip was a non-invariant).
**Suite 331 green.**

**NEXT ARC mapped: render-to-Python / EPUB** ([[project_render_to_python]]).  EPUB is easier than the
API (static artifact vs perpetual service).  It forces marker→rich-HTML rendering into Python: ONE
parser + per-target emitters (site-HTML / EPUB-XHTML / MD / text), viewer → thin interactive shell.
Viewer audit: **~49% of the ~2,291 JS lines port mechanically**, ~7% (`\n\n` heuristics) dies,
math→MathML is the one genuinely-new bit, and tables decompose into recursive markers (closing the
"quasi-recursive" hole: today recurses cell content but flattens structure to HTML + re-parses via
DOMParser).  First move: the verifiable Python render of the current viewer output (corpus diff).

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

- **Suite:** **419 green** (render + transform + inline snapshots all rebaselined this session).
- **Rebuild: DONE 2026-07-15** — local `--skip-import --no-deploy` (54:45, clean); corpus render-leak
  floor unchanged (`render_leak_marker` 3→3).  Render-collapse commit banked; **deploy pending** — ship
  the already-built corpus + viewer, nothing partial.
- **Last *deployed* rebuild: 2026-07-07** — full `--skip-import` rebuild + deploy, 66:25, exit 0,
  preflight clean.  (Prior deploys: 2026-07-06 campaign + distribution; 2026-05-17 before.)
- **Working tree:** render collapse banked atop the 2026-07-12 commits (`c97d863`/`0aa87b0`/`26999b4`/
  `50d34ed`).  A pre-existing readers-guide HTML diff (25 files) is unrelated to the collapse and
  un-banked.

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

**Active queue (2026-07-15):**
- **Render collapse (render_paragraph → mechanical decode_inline)** — ✅ **DONE 2026-07-15, deploy
  pending** (Session 2026-07-15 above).
- **QUEUED → footnote popup can't hold block content** — a footnote with a `<table>` renders in Notes
  but not the popup (block content foster-parented out of the inline `.fn-popup` span), leaving the
  table loose inline.  Pre-existing; a popup-DELIVERY fix (carry the note body inertly → positioned
  overlay), NOT a source-render fix.  [[project_footnote_popup_block_content]]
- **QUEUED → MEMORY.md over its load limit** (~58 KB > ~24 KB) — tail entries silently dropped on load;
  needs a compaction pass to one terse line per entry.
- **NEXT ARC → article DISPLAY + URL** (refined 2026-07-15 — NOT an identity/boundary problem; the
  article is fine and complete).  ALGEBRA is ONE correct article; only its *displayed name* and its
  *URL* are wrong (it shows "ALGEBRAB", URL `01-0639-algebrab`).  Three OUTPUT-layer fixes, no pipeline
  surgery:
  1. **Title display — DELETE `recover_title_from_section`.**  It substitutes the Wikisource `<section>`
     id for the printed headword whenever the id starts-with-and-is-longer than the captured heading
     (`ALGEBRA` + section `AlgebraB` → `ALGEBRAB`; `PolandB`→`POLANDB`).  It never *recovers* — it
     *replaces* the 1911-print title authority with transcriber scaffolding, so it wrecks every title it
     touches (even the "good" `TISIO`→`TISIO BENVENUTO` re-spells + de-punctuates the printed form).  The
     `<section>` id is cruft; the title is content-only.  Delete it; fix genuine partial captures
     (`TISIO`) in `_title_span`, never from the id.
  2. **Description — sharpen + CONSUME `body_start`.**  The data largely exists: `WILLIAM I., KING OF
     ENGLAND`'s `body_start` already reads "…surnamed the Conqueror."  Two gaps: (a) it leads with the
     parenthetical (`(c. 1036–1097)`), so a long date/etymology prefix eats the budget before the
     identifying clause — start it at the defining appositive instead; (b) **nobody consumes it** —
     `resolve_one` matches TITLES only.  Feed the surface reference's leftover qualifier ("the
     Conqueror") against candidate *descriptions* (fixes ODO OF BAYEUX → the right William; same for the
     ALEXANDER / PHILIP / HENRY clusters) and SHOW it under the title in search.  Promote `body_start` to
     a first-class per-article field so the resolver can read every candidate.  "Information we already
     compute but neither show nor use."
  3. **URL — NUMBER-ROUTING.**  The number is anchored to the ORIGINAL SCANNED PAGES (not boundary
     detection), so it is stable + unique BY CONSTRUCTION — routing by it is 100 %-safe forever and any
     future name change is free.  Route on the number, slug purely cosmetic; keys become `{number}.json`
     (title lives inside the JSON).  Old slug-based URLs resolve via a **frozen, one-time**
     `old-stable-id → number` bridge, buildable NOW from the current corpus (which still carries both
     coordinates) — append-only-forever for safety, but it never regenerates.  Client-side bridge +
     `<link rel="canonical">` fits the thin shell; edge-301 only if SEO demands.  Its own deploy, after
     the collapse.
- **`{{=}}` div gate · carry-unless-furniture tooltips · contributor normalizer collapse** —
  ✅ **DONE, shipped 2026-07-07** (Session 2026-07-07).  The div gate was the `{{=}}` escape,
  not `{{nowrap}}`; the normalizer collapse recovered the `W. AY.`/`T. G. BR.` stragglers.
- **NEXT ARC → render-to-Python / EPUB** ([[project_render_to_python]]).  The **site-HTML render is
  DONE**: Python `render_article` is the sole renderer (viewer = thin shell), and the **2026-07-15
  collapse finished the mechanical part** — render_paragraph + the `\n\n`/block-scan paragraph
  heuristics deleted, the per-context decoders subsumed into one `decode_inline`, tables decomposed to
  recursive markers (the "quasi-recursive" hole closed).  **Remaining:** the EPUB-XHTML target
  (per-target emitter — a static artifact, easier than the API) and math→MathML (the one
  genuinely-new piece).

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
- `tools/pipeline/post_export.py` — the post-export pass (Phase 6b4): ONE load
  of the corpus, math hints → contributors → xrefs + render, ONE write.  Each
  transform is also runnable alone via its own module's `main()`
  (`annotate_math_markers.py`, `resolve_contributors_post.py`,
  `resolve_xrefs_post.py`).
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

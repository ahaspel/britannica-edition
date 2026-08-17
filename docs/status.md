# Britannica Edition — Status

**Last updated:** 2026-08-17.  Single source of truth for project state.  Snapshot
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

## CURRENT STATE (2026-08-17)

### Session 2026-08-17 — consolidation: the measured-width caches get one owner each

**Both content-addressed measurement caches — math widths and table widths — now
have a single owner for their key and their path, and the «TABLE» grammar four
sites were spelling independently now lives in the lexicon.  Provably inert:
19,788 measured facts identical across the change, 636 tests green.**

The class of bug: a cache WRITTEN by a build tool and READ by the pipeline, with
each side spelling its own key function and its own path.  Nothing fails loudly
when the pair drifts — the reader looks up keys the writer never wrote, finds
nothing, and every hint silently vanishes.  That is what emptied 194 tables'
Expand hints on 2026-08-16 (item 7 below), and the same latent duplicate sat in
the math path (`math_widths._hash` vs `measure_math_widths._hash`).

What moved:

- **`util.strings.content_digest`** — THE content address (`sha256[:16]`, `n=None`
  for the full digest).  Five sites spelled it inline; each keeps its own
  composition (what goes INTO the key) at the call site.  No `or ""` guard on
  purpose: a `None` keying as the empty string is a silent wrong-entry hit.
- **`math_widths.cache_key` / `CACHE_PATH`** — owned by the reader, imported by
  `measure_math_widths`.  Both sides now hold the SAME object.
- **`britannica.table_widths`** (new, mirrors `math_widths`) — `CACHE_PATH` +
  `span_key`.  `post_export` used to reach into a *diagnostics* script through a
  CWD-relative `sys.path` hack to borrow the key; that inversion is gone.
- **The «TABLE[cols:N|wide]» grammar → `markers`** (`iter_table_spans`,
  `balanced_end`, `table_cols`, `table_is_wide`, `set_table_wide`,
  `strip_table_wide`).  Four sites spelled it: the render's Expand wrapper, the
  annotator that stamps `wide`, the cache key that strips it, the measurer's
  `cols` read — two carrying the same regex source verbatim.  `annotate_table_markers`
  now spells no marker at all and came OFF the marker-op OWNERS ledger.
  `_balanced_end` went 3 copies → 2 (the lexicon's is shared by the render).

**Proof (the part that matters).**  Before/after over the real corpus, byte-identical
across 19,788 rows: 4,649 math keys + every `scale_hint` answer; 10,792 table span
keys + cache hit-rates (947 math / 10,984 table entries still hit at the same
rates); `annotate_body`'s output for every article carrying a table; and
`_wrap_wide_tables`' output + Expand counter for all of them (720 stamps → 720
figures, unchanged).  Corroborated end-to-end: 468 articles (all 68 «EQN» ones +
400 random table ones) re-render byte-identical to their stored `rendered_html`.
The EPUB math-asset key was proved separately — 9,298 keys identical, 4,650 SVG
cache hits either way.

**Standing invariant, not a one-shot:** `tests/unit/test_width_cache_identity.py`
asserts writer and reader hold the same key/path OBJECT (equality would permit
exactly the state just removed), that `span_key` is stable under annotation, and
that nested/unterminated spans walk by depth.  Instruments: `dup_functions` 11 → 10
exact clone groups; the `dup_constants` baseline re-accepted, dropping 17 stale
entries (the duplicated «TABLE» regex plus 16 the earlier passes had already
retired) so none can return silently.

**Then `_parse_field` — and it was a four-copy brace walk, not a two-copy regex.**
The ranked item was one function duplicated between `link_frontmatter` and
`build_contributor_table` (both rebuild phase 5.4).  Grepping the CONCEPT found
the family: each also had its own `_iter_entries` and its own spelling of the
entry marker, and two neighbours had written the same brace counter again —
`extract_contributors._iter_footers` and `detect_boundaries._extract_template_content`.
All four exist because a non-greedy `\{\{.*?\}\}` truncates at the first INNER
close, and all four paid for that lesson separately (~2/3 of entries dropped;
Pitcher's `C. {{sc|Wi}}.` truncated to `C.` and collided with Crewe;
`{{x-larger|{{uc|TITLE}}}}` cut at the inner brace).

- **`britannica.wikitext`** (new) — the SOURCE-side lexicon, companion to
  `markers`: `template_end` + `iter_template_bodies`.
- **`contributors.frontmatter`** (new) — the `{{EB1911 contributor table/entry}}`
  grammar: `ENTRY_OPEN`, `iter_entries`, `parse_field`.  Both phase-5.4 readers
  import it; the tool imports the library, as before.
- The twins **had already drifted at the edge**: for an unterminated template
  `link_frontmatter` yielded a garbage slice (rest-of-text minus 2 chars) where
  its twin yielded nothing.  Proved it never fires on the corpus, then made
  "skip it" the single behaviour.  `tests/unit/test_wikitext.py` pins that edge.

Proof: 49,445 rows byte-identical over all 28,780 raw pages — 5,178 entries read
by BOTH readers, every field the callers parse (initials/name/description/
subject1-11/lnksubject1-11), 8,228 footer bodies, 14,030 plate-title reads.
`dup_functions` 10 → 9; the `_parse_field` regex left the constants baseline.

**Next by stakes**: `_mint_ph`/`_new_placeholder`
(placeholder minting, classifier vs walker, core of the walk) → `_normalize_name`
(the contributor-dedup gate and the audit that checks it each have their own copy,
so the audit can disagree with the gate it audits) → the last balanced-scan
copies: `export/markdown._balanced_end` (marker tokens, REGEX opener, -1 on
unbalanced) and `elements/_ordered_list._balanced_end` (braces, returns
len(text) — it GUESSES a close and hands back the rest of the document, the
thing `markdown`'s own docstring warns against).  Both are behaviour questions,
not moves: reconciling the sentinels needs its own corpus evidence.  Also open,
found while grepping: the **split-on-top-level-pipe** family — `plate_parent`,
`detect_boundaries` (twice), `_dual_line`, `_link`, `build_printed_pages` each
walk depth to split a template's args.

### Session 2026-08-15 — CENSUS GREEN.  The corpus resolves every link production does, +1.  DEPLOYABLE.

**All gates pass.**  The one-reader rebuild (commit 4091691, log
`rebuild_20260814_lnreader.log`) is on disk; Phase 6i clean at `INVENTED BY US: 0`;
Phase 6g clean (8 candidates, all acknowledged-distinct); the census gate, corrected
(below), passes at **202 → 203 resolved links, 0 losers, 1 gainer** over the 250
sample.  Record-level check agrees: 186 → 187 resolved panel entries.  The ~370-loss
regression is gone.  Not yet deployed — corpus awaits the user's call.

**The first gate run "failed" at −4, and every one of the four was a counting
artifact, not a lost link.**  The census counted `class="article-link"` anchors,
which conflates two classes: resolved `/article/…` links and the renderer's
`/search.html?q=` fallback for an UNRESOLVED «LN» left in a baked body.
Production's bake left unresolved markers in place (→ search anchors); the current
bake never does — Wikisource external link if the page exists, else plain text.
The four "losses": three citations became **better** links (WS pages of the cited
books — *Ancient Stone Implements*, *Researches into the Early History of
Mankind*), one (a DNB citation with no WS page) became honest plain text.  The
census now counts `href="/article/…"` — resolution, the thing it exists to measure.

**Zero gains was the CORRECT result — "expect gains to appear" was wrong at its
root.**  The resolver port and its +1,535 A/B date to **2026-07-19**
([[project_xref_strategy]]); production was deployed **Aug 11 19:45**, so
production already CONTAINS the port's gains.  And production predates the entire
Aug 12–14 link arc — including 6a04a10, the commit that first put markers INTO
displays — so it never had the display regression either.  Both sides of last
session's prediction dissolve: no gains to appear (they shipped weeks ago), no
losses to recover (production never lost them; only our local corpus did).  The
honest expected census was "parity, ±the fallback-policy delta", which is exactly
what measured.  What the Aug 12–14 arc nets vs production: **+1 link / 250
articles** plus correctness — TARAFA-class links now file EB1911's target with
the printed display (production has the slots swapped), and displays carry their
source markup.

**Two blind diagnostics fixed while adjudicating:**
* Quality report said `Xrefs: 0 resolved, 0 unresolved` — it read
  `xref_count`/`resolved_count` from index.json, which Phase-F (`defer_xrefs`)
  stamps (0, 0) at export since resolution moved to 6b4; nothing back-fills.  The
  fields had ONE consumer, so: fields deleted from the index (18.6 MB client file,
  dead weight), report now reads `data/derived/xref_resolution.jsonl` — the resolve
  phase's own output, where both resolved (30,321) and unresolved (11,044) exist.
* Overlap audit printed `aid=` (DB autoincrement) for its worst-article examples —
  un-followable after any reimport (the two 08-14 logs show identical output with
  every aid shifted).  It now resolves the printed few to titles.

**Process lesson (user's call-out, correct):** most of this was knowable BEFORE
the 45-minute rebuild.  The fallback-policy delta was readable in `_resolve_link`;
the index zeros were a data-contract grep; the gate's anchor-count conflation was
in the census I wrote.  I attached a gate without deriving its expected value
first, so the failure bought archaeology instead of a checked prediction.
[[feedback_audit_fresh_baseline]] — deduce the result, then measure.

**Next, in order:**
1. ~~Deploy~~ **DONE + VERIFIED 2026-08-15** (`deploy_20260815.log`, 18:56):
   production census 203 = 203 zero-delta; TARAFA's corrected slots live; HF
   mirror + Meili reindex clean.  ALSO: the HF dataset card now stamps
   **"Corpus build: YYYY-MM-DD"** ({{GENERATED}} placeholder in
   `download_assets/README.md`, filled by `export/download.py` with the
   manifest's own instant — user: the HF page had no visible update date);
   bundle regenerated + re-uploaded (S3 tar.gz/sha256/manifest/README) +
   republished to HF the same day.
2. ~~Rebuild the EPUBs~~ **DONE 2026-08-15** (`epub_rebuild_20260815.log`):
   sampler 20.0MB/32 chunks + full book 576.5MB/889 chunks/10,664 images, BOTH
   epubcheck 0/0/0; fresh sampler + sha256 uploaded to S3; **eb1911.epub in the
   repo root awaits the user's Payhip swap** ("corrected editions free to
   purchasers").  **NO Kindle build** — the full book never converts to KPF,
   WITH OR WITHOUT Enhanced Typesetting (user, 2026-08-15: ET was already
   disabled and the full corpus still wouldn't load — the blocker is NOT the ET
   check).  The only known bracket: one volume converts (real 78MB KPF), the
   full corpus doesn't.  **KDP ticket DEAD (2026-08-15)** — final answer: "too
   complex, takes too long to process" (a converter timeout called
   "corruption"); their own tech team couldn't open the file; no limit named,
   no escalation left.  **KINDLE CLOSED — NO HOPE (user's verdict,
   2026-08-16).**  The half-corpus probe settled it: vols 1-14 kindle target
   (18,476 articles / 5,352 images / 250.7 MB) behaves EXACTLY like the full
   book — Previewer reaches "enhancing for Kindle reader" (the ET stage) then
   bombs with a hollow "Book conversion successful" and NO artifact; a
   parallel detached CLI run wrote no output directory at all.  Predictable
   from July's bisection (≤6,582 articles pass / ≥7,902 fail; half is 2.3×
   over) — that arithmetic belonged BEFORE the build, not after
   ([[feedback_audit_fresh_baseline]]).  Those ceilings against real
   per-volume counts give **7 parts by articles, ~8 by images** (1-4 / 5-9 /
   10-14 / 15-18 / 19-23 / 24-27 / 28), each shedding ~half its
   cross-references to live-site URLs; the user's bar was two.  DO NOT
   re-probe, build a kindle target, or propose a parts edition.  The user is
   editing docs/download.txt's "Kindle edition ready shortly" line themselves.
   Queued
   structural fix: deploy.sh ships the sampler from the repo root as-is — fold
   the sampler build into the rebuild so it can't go stale.
3. ~~Phase relabel~~ **DONE 2026-08-15**: 1 Clean · 2 Walk · 3 Page map ·
   4 Export · 5 Resolve · 6 Site · 7 Gates · 8 Deploy, sub-steps N.M in
   execution order (the old letters ran 6h before 6f, 6g after 6i2).  Decoder
   comment for old logs at the top of the script (3c→3.1 … 6b4/6b5→5.4 …
   6g→7.5 7→8); all ~40 code references updated — grep for `6b4`/`6b5` in
   *.py now finds nothing.  Docs/memory keep historical numbering; the
   decoder translates.  Own bank.
4. **Two user-caught bugs FIXED 2026-08-15, not yet shipped:**
   * `by:` search operator NEVER worked: the client sent `contributors CONTAINS`
     — an operator no deployed Meilisearch supports (400 → shown as zero
     results) — and search-api.js's substring gate dropped every hit of a bare
     `by:Name` anyway (empty q).  Now: client post-filter on the hit's own
     `contributors` field; bare `by:Name` searches the contributors attribute
     (`attributesToSearchOn`).  Verified in-browser locally: `by:Bury` → 10,
     `empire by:Bury` → ROMAN EMPIRE, LATER.  SHIPPED (2026-08-15 second
     deploy) and verified on production.  `by:Bury` → 10 is CORRECT — user
     confirmed it against the contributor index (binding is conservative:
     signed articles only, never guesses); an earlier "local index is stale"
     note here was wrong.  Local reindex when wanted:
     `MEILI_MASTER_KEY=britannica-dev-key ARTICLES_DIR=data/derived/articles
     uv run python tools/pipeline/index_search_ec2.py`.
     **Operator-only queries are a BROWSE (user spec 2026-08-15)**: `min:10000`
     alone now answers with EVERY qualifying article (632, paginated) via the
     client-side index — the dead `searchTitle` (never called since the mode
     collapsed to fulltext-only) refit as `browseOperators`, reading STRUCTURED
     operator values from `parseQuery` instead of regexing its own filter
     string.  `by:` (no contributors column in index.json) stays on the server
     path, limit 1000 when bare.  Also killed en route: `type:plate` always
     returned empty — parseQuery emitted `article_type = "plate"` while
     search-api.js appended its default `NOT plate` (plates-only AND not-plate
     = nothing); index.html now passes `excludePlates:false` and parseQuery's
     filter owns the plate default.  Verified: `min:10000` → 632/7 pages,
     `type:plate vol:4` → 14 plates, `empire by:Bury` → 1.
     **Quoted phrase queries also never worked (user)**: Meilisearch reads
     `"battle of hastings"` as a phrase and returns hits, but the client's
     substring gate/ranking counted the RAW query — quote characters included —
     against body text, so every phrase query died at zero.  Quotes are
     delimiters: `fold()` (the one equivalence owner — gate, ranking,
     typeahead) now folds straight+curly double quotes away like accents, and
     the snippet extractor / viewer forward link get the unquoted phrase.
     Verified: `"battle of hastings"` → 17 results, highlighted snippets.
   * The h1 DROP-CAP split an HTML entity: `"SURVILLE, CLOTILDE DE,"` (the
     quotes are EB1911's own — the persona is apocryphal) escapes to
     `&quot;…`, and wrapping the first CHARACTER produced `<span>&</span>quot;…`
     — a big ampersand and literal `quot;` on the page.  The drop-cap unit is
     now one rendered glyph (whole entity); test in
     `tests/unit/test_title_dropcap.py`.  RENDER change → lands in
     rendered_html on the NEXT REBUILD (1 article affected; the other two
     escaping-first-char titles are `'''AMPHITHEATRE'''`/`'''Plate II.'''`
     plates — raw wiki bold in plate titles, belongs to the title-extraction
     arc).
5. **Sweeper campaign K-series (2026-08-15, ledger in docs/sweeper_removal.md):**
   K2 (index.html JS mini-decoders over provably-plain inputs) and K3 (five
   dead pre-port render functions in viewer.html, incl. renderImg's
   payload-eating alt sweep) DELETED + browser-verified; `test_viewer_parity`
   inverted to pin the ABSENCE of a JS slug copy.  **K1 DISSOLVED 2026-08-16**
   (full detail in the ledger): both ancillary builders now render through
   the ONE pipeline (`ancillary_render.render_pages`); one «AL» reader
   (K1.0) rewired extractor/bake/contributor-pass; preface + prefatory-note
   pages regenerated, browser-verified (links, TOC, footnotes, drop-cap via
   ::first-letter).  EN ROUTE, TWO PIPELINE FIXES THAT NEED THE NEXT FULL
   REBUILD: (a) dehyphenator ASCII-fragment bug — accented words were voted
   by ANOTHER pair's key (`arrièrepensée` ships in 24-0508); one Unicode
   alphabet + map rebuilt; (b) USER RULING: the hyphen vote repairs BREAKS
   only — contiguous hyphens are print (10,540 sites across 4,971 articles
   now carried), EXCEPT shoulder headings (narrow-measure inserts) which
   vote contiguously ("Differentiation", stable slug).  corrections.json
   +20:229 (`lo-in`→`10-in.`).  16+1 snapshots adjudicated + rebaselined;
   628 green.  **K4 CLOSED 2026-08-16** — the survey proved the whole module
   dead (`extract_contributor_bios`: strips never fire, bios come from
   build_contributor_table, CLI-only caller nothing invokes) → deleted, and
   the one-true-path audit's FIX-FIRST entry resolved.  **K5 (user-caught):
   plate tables were measured/stamped `wide`** — 123/535 plates offered the
   Expand treatment on full-margin pages; annotator now forces the strip
   side for plates (decorate hook passes the payload; measurer skips plates)
   — heals at next full rebuild.  **K-RATCHET LIVE 2026-08-16**
   (`test_marker_op_ratchet.py`): marker string-ops outside the OWNERS
   ledger fail the suite; viewer JS pinned at zero; ghost-pruning +
   vacuous-pass guards; live-fired red.  Flagged en route:
   `disambiguation.py`'s private token-strip → `markers_to_text` (the one
   converter).  631 green.  STILL OPEN:
   capture_transform_snapshots.py broken (no meta.json, hash-stem
   filenames) — repair queued.
6. **EPUB wide math + tables (2026-08-16, epub.css only):** display-math
   SVGs (ex-sized; widest ~100ex) had NO width clamp — narrow readers CLIP —
   now `svg.math-display { max-width:100%; height:auto }`, the shrink-to-fit
   guarantee kindle PNGs already had; measured-wide tables (the
   `wide-table-wrap` figure every target already carries) step down to
   0.75em (`.wide-table-inline table`) since reflowable readers don't scroll
   overflow.  Vol-1 sampler rebuilt, rules + classes verified in-artifact,
   epubcheck 0/0/0.  The SHIPPED sampler/Payhip book predate this — next
   EPUB refresh picks it up; narrow-screen reader testing remains the open
   verification.
7. **2026-08-16 REBUILD (hyphens + K5 + corrections) — BUILT, ADJUDICATED,
   AWAITING DEPLOY.**  44:05, gates green (run twice — see below).  Content
   diff vs `fingerprint_pre_rebuild_20260816.tsv`: 0 disappeared/new, 5,113
   CONTENT changed, words LOST 125 — ALL adjudicated: plate Expand chrome
   leaving (user-confirmed count), plus a handful of legitimate NEW wrap
   joins (the separator rule UNSHADOWED wrap pairs the contiguous match used
   to consume first: `soda-contain- ing`→`soda-containing`).  Spot-verified:
   AFRICA `table-land`/`sea-board` back, ORDNANCE `10-in.`, plates
   wide-stamped: 0.  **FOUND + REPAIRED EN ROUTE: the width cache keys on
   span BYTES, so tables whose interior text re-hyphenated cache-missed and
   SILENTLY lost legitimate Expand hints** (INSTRUMENTATION −2 buttons) —
   ran `measure_table_widths` (194 changed spans; cache now covers all
   10,308) + `annotate_table_markers` (24 articles re-annotated +
   re-rendered), INSTRUMENTATION verified healed, BOTH gates re-run green
   on the final corpus.  STRUCTURAL (queued): the uncached-span→silent-strip
   channel — an unmeasured span should keep its prior hint or count LOUDLY;
   and measure→annotate isn't a rebuild phase, so any content-changing
   rebuild can re-open this hole.
8. Fold `_resolve_bio_articles` onto the resolver (bind-for-bind simulation first).
9. ~~The prearc worktree (0a39f49)~~ REMOVED 2026-08-16 after the deploy
   verified — the «LN» arc's last piece of scaffolding.

### Session 2026-08-14 (later) — THE LINK ARC REGRESSED.  CAUSE FOUND, NOT FIXED.  DO NOT DEPLOY.

**The corpus on disk loses ~370 links relative to production.  Production is the
better site.  Nothing has been deployed.**

**Cause (established, with evidence).**  The `«LN»` marker grammar is written out
in at least three places, and only ONE was fixed:

    extractor.py:95            «LN…:([^|]*)\|([^«]*)«/LN»     <- still the old grammar
    article_json._resolve_ln_markers                          <- fixed (scan)
    markers._LINK_RE                                          <- unchecked

A display containing ANY marker (`«SC»Parasitic Diseases«/SC»` — a cross-reference
set in small caps) does not match `([^«]*)`, so the extractor produces NO xref for
it; with no xref there is no `target_article_id`; with no bound target the bake
strips the link to plain text.  Silently, because a missing xref is
indistinguishable from a link that legitimately does not resolve.

    SCARLET FEVER  walker : «LN:Parasitic Diseases|«SC»Parasitic Diseases«/SC»«/LN»
                   xrefs  : 0
                   bake   : (no «LN» left)

This is ONE cause for both symptoms.  The losses are marked-up cross-references.
The zero gains are the same thing: the 255 marked-up displays "recovered" in
`_resolve_link` were fixed in the SECOND half of the path while the first half
still drops them, so not one could ever reach the corpus.  And the
inverted-argument rule moved markup INTO 21 displays deliberately, converting
working links into ones the extractor cannot see (TARAFA).

**The fix**: the `«LN»` marker must be recognised in exactly ONE place, extractor
included.  Verification is the CENSUS, not a marker diff.

**Why it took six probes.**  Every measurement I took was at a level the pipeline
does not use — marker diffs, title-index membership, and bare `resolve_xref`
calls (which default to `embedded=False, trusted=True` and take a LOOSER tier
than the pipeline's `embedded=True`).  All of them said the arc was working.  The
first honest number was the census.  See [[feedback_measure_at_decision_site]].

**Established along the way (keep):**
* The resolver is NOT at fault — a pre-arc worktree (0a39f49) gives byte-identical
  embedded results.  Comma fold and alias abstention are both exonerated.
* The embedded tier declines comma-inverted targets (`SOMALILAND BRITISH`,
  `GROUPS THEORY OF`) with `by_norm cands=0` — PRE-EXISTING, not this arc.  Those
  census "losses" may be a route that stopped being taken, not a regression.
* Phase 6i (mangled-marker gate) is clean at `INVENTED BY US: 0`.

**The census is the missing gate** (`scratchpad/link_census.py`): sample
production vs local, count `class="article-link"`.  It belongs beside Phase 6i —
mangled markers must be zero AND resolved links must not go down.

**Next session, in order:**
1. One `«LN»` reader, extractor included; check whether the panel is a fourth.
2. Re-run the census — expect losses → 0 and the gains to finally appear.  This is
   a hypothesis; four predictions were wrong today.
3. Then rebuild, then deploy.
4. Only then: fold `_resolve_bio_articles` onto the resolver (see below).

**Do not kill a rebuild past Phase 4** — that phase clears `data/derived/articles`,
so stopping there destroys the corpus rather than pausing it.  A `prearc` worktree
at 0a39f49 is on disk under the scratchpad; keep it until this closes.

### Session 2026-08-14 — rebuild adjudicated; two link regressions; the mangled-marker gate

**REBUILD PENDING RE-RUN — the corpus on disk carries four known defects, all fixed
in code, none deployed.**  `./tools/rebuild_all.sh` then `./tools/deploy.sh`.

**Adjudicated the 2026-08-13 rebuild** (453 articles changed: 34 gained, 214 same
word-count, 205 lost).  195 losers came in under the ceiling their own links could
account for; the other 10 were settled EXACTLY by fetching the pre-rebuild JSON from
production — the deploy had not run, so the live site *was* the old corpus.  Eight are
the link fix working (`Munzinger, Werner`→`Werner Munzinger`, `Cope, Edward Drinker`
→`Cope`).  Two were regressions:

1. **The swap printed Wikisource's spelling over EB1911's.**  STILT's
   `{{1911link|Oystercatcher|Oyster-catcher}}` files the wiki page first and the
   printed words second; our titles come FROM EB1911, so the side matching a filed
   title is the printed side (`OYSTER-CATCHER`, vol 20 p 462).  Length cannot
   discriminate — the hyphen alone makes the printed spelling one character longer.
   40 links / 28 pairs, all EB1911 compounds (`Bag-pipe`, `Tread-mill`, `Ear-ring`)
   rendering as modern closed-up forms.  Fold-equal now keeps the target and shows the
   filed spelling; the decision moved out of the closure into `swapped_link()`.
2. **`subpage_target` mangled markers.**  It split link targets on `/`, and a close
   marker's slash is not a path separator: `«/I»`→`«#I»`, which fails the 3-part «LN»
   opener grammar (`[^|«]*`), so the marker collapsed to its 2-part reading and 17
   links rendered with the filename in the href and a raw pipe in the anchor text.
   Path work now holds markers aside.

**THE MANGLED-MARKER GATE (`tools/diagnostics/mangled_markers.py`, Phase 6i).**  The
leak oracle is structurally blind here: `find_leaks` matches WELL-FORMED markers, and
a mangled marker is not one, so `«#I»` read as clean everywhere.  The gate compares
each output's unaccounted guillemets against the article's own RAW SOURCE — zero false
positives, no baseline, nothing to keep current, because the source is static.  It
found the 12 `«#I»` articles plus two standing bugs no one had seen:

3. **`_render_eqn` read its label to the first `»`**, so `«EQN:«BR»(15)»` gave the
   label `«BR` — equation number lost, mangled marker shipped.  The `«EQN:LABEL»`
   contract (plain text; the renderer owns the parens) is now enforced in the one
   producer every «EQN» passes through.  Also fixes MECHANICS' `((8))`/`((9))`.
4. TIMOTHY's duplicated footnote text turned out to be BY DESIGN (inline + Notes), and
   killed the count-based comparison — hence signatures, not counts.

**Guillemets, settled.**  Of 253 unaccounted in the corpus, 17 were ours (all of the
above); the other 108 in 25 articles are **Wikisource's own mojibake**, proven by
fetching the live page — byte-identical to our copy, `108Â° 38' E.` and all.  None are
French quotation marks: there is no legitimate bare `«` in EB1911's text.  The wider
class is 677 sequences in 58 articles (0.16%), 91% in twenty, almost all volume 25
unproofread math.  **A blanket `Â°`→`°` repair is a trap** — `(957Â°)` is 9570,
`(173Â°)` is 1730, `t0 lÂ° wer` is "lower"; the encoding repair would be right and the
character still wrong.  Per-instance `corrections.json`, deferred quality bucket.

Suite 527 → **573**.

### Session 2026-07-27→29 — Kindle campaign: oracle solved, CASTANETS refuted, converter is non-deterministic

**Oracle root cause (SOLVED, supersedes every daemon/cache/settle theory of 07-27/28):
Kindle Previewer launched as a child of the sandboxed bash shell self-exits in ~2s** —
clean exit, rc=0, no Summary, arguments never processed (`-help` is equally mute); its
own log (`~/.kindle/KPR/log/KPR.Log`) shows init → "Logger Terminated" per invocation.
**Launched detached via PowerShell `Start-Process`, the same book+args convert
reliably.**  Every mute-era verdict is void.  Protocol now: PowerShell runner, ONE
exclusive queue, unique file copy per conversion, poll `-output` for Summary_Log.csv,
Stop-Process the lingering app between runs (single-instance).

- **Vol-1 kindle: "Supported" again** (third clean pass; also user-GUI-validated r16).
- **CASTANETS 2×2 replication (user demanded: real or bogus?): BOGUS.**  Identical
  bytes of the original vol-5 probe: run1 Not Supported, run2 **Supported**; shifted
  probe: Supported ×2.  **Amazon's ET check is NON-DETERMINISTIC on identical input.**
  The "positional/byte-offset bug" was sampled noise; `--nudge` retained only as a
  harmless rebuild knob.  Corollary: any single Not-Supported verdict is meaningless —
  measure pass RATES; a passing conversion (the KPF) is what ships.
- **Full-book ET verdict: IMPOSSIBLE — Amazon gates ET on a per-book entity-count
  ceiling (2026-07-30 scale bisection, 11 books).**  Full book fails 4/4 in 5-6min
  (fast structural reject; a real conversion takes 27-40min).  Ladder: vols 1-3
  (58MB) Supported · 1-4 Supported · 1-5 (91MB) fast-fail — then axis kills:
  1-3 FULL-images (198MB!) Supported → SIZE dead; 1-5 @600KB-chunks (spine 758 <
  every passing book) fast-fail → SPINE dead; 1-4 @40KB-chunks (manifest 4,285 ≈
  failing 4,291) Supported → MANIFEST dead.  Surviving axes, perfectly monotone:
  **images ≤1,470 pass / ≥1,866 fail; articles ≤6,582 pass / ≥7,902 fail**
  (correlated — exact constant unresolved, product-irrelevant: the full book is
  ~6× beyond either).  Undocumented (KDP help checked).  **Product consequence:
  the complete single book ships as a STANDARD-format Kindle book (conversion
  "Success" every run — renders on all Kindles, just without ET niceties);
  ET stays a per-volume property (any single volume is far under the ceiling —
  vol-1 sampler proven).  `--chunk-target` flag added to build.py (bisection
  tool; also the knob if Amazon's ceilings ever move).**
- Castanets probe article restored byte-identical after replication builds
  (`castanets.orig.json` hash-verified earlier in the arc).

### Session 2026-07-31 — cover scan · site-mirrored labels · link policy · FTS

**LAUNCH (2026-07-31 evening):** full site rebuild (53:43, all gates green — materialized
the ported xref strategy, vol-29 contributor credits, fold_cell_attrs, repaired guide
pages) → deploy (17 min, S3+CloudFront+Meili 37,226 docs+HF) → **VERIFIED LIVE**:
download.html sells the EPUB at $39.99 via Payhip (payhip.com/b/ifyaR), fresh build
(549.6MB) swapped in, production search answers.  **KINDLE: the full book NEVER
converted — anywhere.**  Local "Conversion Status: Success" was HOLLOW (vol-1 Success
→ real 78MB KPF; every full-book Success → EMPTY output path, no artifact; cloud KDP
rejects with a generic error).  Lesson re-learned at cost: DEMAND THE ARTIFACT, never
a status string.  KDP support ticket ESCALATED (answer promised ~2 days); options if
"no": vol-1 sampler (proven KPF) or 4-6-part series under the proven ceiling
(≤ ~6,582 articles / ~1,470 images per book).  HN follow-up post: first attempt
dupe-swallowed (same URL, 3-month-old 353-pt thread), download.html attempt flagged;
mod email sent, second-chance pool expected.  Store assets: eb1911-cover.jpg
(portrait/KDP) + eb1911-cover-square.jpg (ink ground/Payhip).  Titlepage count now
36,691 plain articles (535 plates excluded; user matched all copy to the home page).

**Per-article topic references (user caught the gap):** the site's "In: Category ›
Sub" line is a client-side overlay — the BOOK bakes it: topic tree + page names
precomputed BEFORE pass 1 (one owner — the topics section reuses them), each staged
article appends a `topic-refs` section, every path element linked to its topic page.
Full book: **34,468 articles carry refs** (≈ the toc's ~95% link-resolution rate;
residual = resolver tail, not book loss).  Works on BOTH targets (plain links).
**PUBLICATION CANDIDATES: eb1911.epub 550MB 0/0/0 · eb1911-kindle.epub 554MB.**

**TOC top restructure (user spec, LANDED):** `Introduction` group (To This Edition —
the user's REVISED introduction.txt · Editorial Preface · **Historical Preface** =
the Prefatory Note) then `Search` group (Title · Full-Text), then Volumes/Topics/
Contributors/Guide.  **Preface to the Index REMOVED** (user: the book's own indices
supersede it).  Payhip file cap verified: 5GB/file — the ~550MB EPUB is fine.

- **Cover (complete edition):** the site's Volume I title-page photograph cropped to
  the FLAT printed page (no leaf edges/backdrop; `_TITLE_PAGE_CROP` fractions),
  scaled to 2560px; volume builds keep the drawn mark.
- **Volume TOC labels: the site's rule VERBATIM** (index.html volArticles/
  volRangeWords — user: 100% correct): plain articles only, ws_page order with
  ws_page_end tiebreak, first word of first/last titles.  All 28 book labels match
  the site byte-for-byte.  (Two invented heuristics — folded min/max, plate/ligature
  patches — were WRONG; mirror the working implementation, don't invent.)
- **Link policy (user: internal-first):** unresolved «LN» xrefs render as PLAIN TEXT
  in book targets (href-less `<a>`; no site search-box dead ends — 618→0); guide/
  preface contributor citations rewrite to the in-book appendix on exact canonical-
  name match (2,041 site links → 17 honest misses).  KEPT: Wikisource 784, Wikipedia
  18, Gutenberg 3, title-page provenance link.
- **Title search: token-set matching** — multi-word queries need every token to
  match a title word (whole-word, else prefix), ANY ORDER: "HENRY JAMES" now finds
  "JAMES, HENRY" (print inverts names); single-token queries keep the site tiers
  exactly; shorter-title tiebreak.  Plate captions excluded from the search table
  (`article_type == "article"`, 36,691 rows).
- **FULL-TEXT SEARCH (epub/fts.py — the ebook's big win):** whole-corpus inverted
  index embedded as `fts-data.js` (~30MB, +5% book): 36,691 docs / 387k folded
  terms / 12.9M postings, delta+varint in a 64-char CDATA-safe alphabet; terms in
  >27% of docs dropped and ignored in queries.  Own page (`fulltext.xhtml`, TOC
  entry after Title Search) so title lookup stays instant; AND-of-words, article
  granularity, title-boosted ordering; NO phrases/snippets (positions would 3-5×
  the bytes — Meilisearch keeps those).  Node harness drives the REAL asset:
  encode→decode→intersect proven.  Kindle: excluded with the rest of the scripted
  UI (native search is already fast).  Thorium keyboard note: app-level key grab
  = reader limitation; the tap letter row is the accommodation.

### Session 2026-07-30 — EPUB front matter · Reader's Guide · flat TOC

**Front matter (epub/front_matter.py):** Introduction (docs/introduction.txt — plain
text, `#`-comments, page omitted while empty; SEEDED from the site About essay for
the user to adapt) · the 1910 Editorial Preface · the Index Preface — both extracted
from the static site pages (script-attrs dropped, footnote back-links retargeted to
real `#fnref-N` anchors, site-relative hrefs absolutized, wiki-indent colons
stripped), then through `to_xhtml_body` like every baked body.  **Reader's Guide
(epub/readers_guide.py):** hub → 6 parts → 65 chapters as back matter; article
citations (`/article/{stem}`) resolve presence-aware against the anchor map (absent
→ site URL); analytics `<script>` tags stripped at extraction (they ride INSIDE the
chapter pages' content div — 124 epubcheck errors); the one guide illustration
bundled; **8 malformed source hrefs dropped (a literal `<a href=` nested inside
`contributors.html?q=` — build_readers_guide.py generator bug, LIVE ON THE SITE,
site-side fix queued)**.  **Flat TOC (user: 1,000+ nav lines unusable, ~70 fine;
collapse can't be relied on across readers):** top-levels only — Title Search ·
prefaces · 28 flat volume entries · top topic categories · contributor A–Z quarters
· Guide parts; ALL detail behind click-through hubs (NEW volume-NN.xhtml hub =
volume's range list; ranges/topic subtrees/chapters excluded from nav).  **Volume
labels = printed-spine ranges** (accent-folded alphanumeric first-word min/max,
ligatures expanded, plate CAPTIONS excluded): "Volume 1 · A – ANDROPHAGI" (page-order
last stem gave ANDRONICUS — wrong).  Vol-1 control: **epubcheck 0/0/0** with all of
it.  Full EPUB + kindle rebuilds IN FLIGHT (first with cover page on the epub).

### Session 2026-07-26 — EPUB single book: chunk-packed, gated, epubcheck-CLEAN at full scale

**The whole edition builds as ONE valid EPUB.**  `eb1911.epub`: 37,226 articles in 878
~300KB chunks, 10,660 images, 1.44GB — **epubcheck 5.1.0: 0 fatals / 0 errors / 0
warnings**, all four build gates green.  The vol-1 control artifact (`eb1911-vol01.epub`,
65.5MB, 31 chunks) is equally clean — the scale-vs-markup comparison artifact.  Both at
repo root, built by `python -m britannica.epub.build --volume 1 | --all [--target kindle]`.

- **Chunk packing (`epub/pack.py`, NEW).**  Articles pack in spine order (volume → page →
  title → stem, the article_sort_key order) into ~300KB chunks; every article opens at
  `id="a{stem}"`; ALL per-article ids/fragment-hrefs namespaced `a{stem}-…` so articles
  share files without collisions.  An oversized article (>450KB) splits at section
  boundaries — `split_article` is a pure function of the staged bytes, so the plan and
  emit passes agree by construction; each footnote aside travels with its noteref's piece
  (popups stay same-document); FRANCE spans c0303–c0307 with inbound section links landing
  mid-article.  The seam is a TOKEN CONTRACT: the render's EPUB link policy
  (`epub_bundled=LINK_TOKENS`, an object now, not a set) emits `epublink:{stem}#section-…`
  / `epubcontrib:{slug}`; the PACKER — the only stage that knows chunk assignment —
  materializes real hrefs at chunk close, presence-aware (absent stem → live-site URL).
- **Gates (all hard, before zip):** every article anchored exactly-once (37,226) · no
  duplicate ids per file · every internal href resolves to a real file#id · text
  preservation (`split_invariant` = ordered non-aside text + aside multiset; chunk
  resolution = exact text equality).  Missing/remote images placeholder + LOUD log —
  **69 corpus-referenced images absent from data/images + ~11 remote Wikimedia score
  hotlinks: queued for mirroring** (source-side gaps, the site shows the same).
- **Nav at scale:** two-level — 28 volume entries (labels derived first–last, e.g.
  "Volume 1 · A – ANDRONICUS") + A–Z letter-index pages + the contributors appendix
  packed like articles (4 files, byline links resolve to the right one).  878 manifest
  chunk items instead of 37k per-article files.
- **XHTML5 conformance layer for already-baked bodies** (`xhtml5_sanitize` + ET-pass
  fixups; every class regression-tested): legacy table attrs → `data-*` (incl. td@scope,
  non-cell colspan, border∉{"",1}); style-attr filtering that is ENTITY-SAFE (`&quot;`
  ends in `;` — naive decl splits cut inside it, the fatal class) and drops junk decls
  (`width:;`, `width=5%`, brace-leaks, odd-`&quot;` values, EPUB-banned direction/
  unicode-bidi → `dir` attr); `ul`-under-`ul` → into previous li; block-in-phrasing →
  `display:block` span (p/div) or wrapper→`display:inline` div (table/list/heading, an
  `a`'s href carried as data-href); invalid XML attr names dropped at the ET boundary;
  junk-suffixed image names (`….jpg_‎`) bundled under cleaned names; page-marker spans
  baked inside a «TR» attr slot lifted out pre-parse (1 corpus instance, vol 23 p. 704 —
  the site carries the same junk attrs silently; pipeline fix queued).
- **Producer fixes (materialize next rebuild):** `fold_cell_attrs` empty-value guard
  (`width=` → nothing, was `width:;`); `_EPUB_SEC_HEAD_RE` TEMPERED (a heading whose
  «/SC»«/CTR» close is malformed falls back to the generic decode instead of swallowing
  following paragraphs into the h3 — CONTINUED FRACTIONS); footnote/section target checks
  widened `== "epub"` → `in ("epub","kindle")` (Kindle strips JS — site-form popups would
  LOSE footnote content in the kindle build).
- **Math:** collect→generate→render; 5,188 unique equations corpus-wide, SVG inline
  (epub) / PNG (kindle target, exists but unexercised this session).  epubcheck jar in
  scratchpad; java 11 local.
- **IMAGE DIET (user-directed same session; the "per-volume / no-image" fork was a
  false choice — one book, all images, display resolution).**  `epub/images.py`:
  long side capped 1000px (retina at the ~590px column), best-of encode per image
  (JPEG q60 for halftones vs 64/128-colour palette PNG for line art), grayscale only
  when the plate IS monochrome (colour plates keep colour), original kept when smaller;
  content-keyed cache `data/derived/epub_img_cache/` (math-assets pattern — rebuilds
  re-encode only new/changed).  Bundled extension may differ from source; manifest
  media-type keys on the bundled name.  Quality eyeballed: line art crisp; the dense
  state-map class readable at county/town level (densest hamlet names soften — the
  site's full-res remains the archival copy; per-class cap bump is a one-liner if
  device tests want it).  **Result: images 1,368MB → ~150MB in-book; the FULL book
  1,440MB → 543MB** — inside KDP's 650MB upload limit (200MB was only ever the
  Send-to-Kindle personal-docs cap, not a sale channel).  `--images full` keeps the
  archival build.
- **Titles are now findable by reader search** (user caught it in Thorium: body text
  matched, titles didn't).  The site's drop-cap span SPLITS the h1's text node
  ("D"+"YNAMICS") — invisible on the site (Meilisearch), fatal in a book whose only
  search is the reader's text search.  EPUB targets render the h1 as one plain text
  node; the A–Z letter index is the browse surface.  Verified in the shipped bytes.
- **A–Z index is two-level, the site's browse model** (user: one flat letter page =
  ~20 page-turns to FRANCE).  index.xhtml lists each letter's ~100-article ranges
  (site PAGE_SIZE=100; labels = first-3-chars of first/last titles, "FOX–FRA"), each
  range its own small page — one click into any article's neighbourhood; 385 range
  pages.  Ranges sort by ACCENT-FOLDED title, not spine position (print quirks put
  FRANCE, PLATE III after FYZABAD in reading order; labels display raw forms like
  HĀJ/CÆS exactly as the site slices raw titles).  **The NAV TOC nests the same
  model** (user: a flat volume entry gave Thorium nothing to expand): each of the
  28 volume entries carries its spine-ordered ~100-article ranges as a second nav
  level — and each range entry opens a HUB PAGE listing its ~100 article links
  (user: a range that jumps into the TEXT leaves ~50 page-turns to the target; the
  site model shows the TITLE LIST).  **3 clicks to any article**: volume → range
  hub → article.  The volume link itself opens its first hub (NAV-011: nav targets
  must be monotone in spine order — back matter rides in nav order: browse hubs →
  search → topics → A–Z → contributors).
- **TOPICS (user requirement): the classified TOC as nav + hub pages.**  519 nodes,
  depth 4, 36,193 entries (35,955 resolved) from classified_toc.json: one page per
  node in DFS preorder (breadcrumb + notes + child links + article links; notes'
  offset-links resolve to topic pages via a first-wins name map; unresolved index
  entries render unlinked — faithful, no fake binds); the full tree nests under
  "Topics" in the Contents panel.
- **TITLE SEARCH (user: reader search scans ~500MB linearly, unusable order — the
  format has no index).  A SCRIPTED search page** (EPUB3 scripted content,
  `properties="scripted"`; Thorium runs it): embedded [title, href] table (~1.7MB,
  all 37,226), ranking = the site's fold + titleRank tiers PORTED from
  search-api.js (one ordering spec) — instant, Meilisearch-ordered title lookup.
  Script-stripping readers (Kindle) see a fallback pointing at the A–Z index.
  Full-text ranked search stays the site's job (a text index would rival the book).
- **Kindle Previewer rejects the epub-target book** (user: hangs "preparing", fails
  despite "conversion successful" log) — diagnosis: inline SVG math (Kindle renders
  no SVG — the documented reason the kindle target exists) and/or scale.  Ladder:
  `eb1911-vol01-kindle.epub` (`--target kindle`, PNG math) through Previewer first
  to separate format from scale.
- **KINDLE ROOT CAUSE FOUND (2026-07-27, a day of black-box forensics): vol-1 now
  converts, Enhanced Typesetting SUPPORTED.**  The killer: `.mirror-h { transform:
  scaleX(-1) }` — ONE stylesheet rule, 18 mirrored letterforms, ALL in ALPHABET.
  Amazon's ET pipeline rasterizes every transformed node (PhantomJS); its rasterizer
  cannot size bare mirrored text → E00192 ×8 → the whole book "Not Supported" (the
  GUI shows "internal error", the log "conversion successful" — neither names the
  node).  PROVEN by capturing the rasterizer's worklist mid-conversion (phantomjs
  cmdline → workListFile → 18 node items = the book's 18 mirror-h spans exactly).
  Kindle css drops the rule (letterforms unmirrored there — ET's own mirror path IS
  the crash; site/EPUB keep true mirroring).  QUEUED (user-agreed): restore fidelity
  by pre-rendering the 18 mirrored glyphs as sized PNGs at build (Playwright, the
  math-PNG machinery's shape) — kindle shows TRUE mirroring as inline images, no
  transform for ET to choke on; rides the next kindle build round.  En route, real classes fixed: brace
  scaleY→font-size, scripted page off kindle, apostrophe image names (Amazon doesn't
  XML-decode manifest hrefs), explicit img width/height attrs, per-equation-resilient
  math PNG generation, per-target css.  FALSE TRAILS (each refuted by measurement):
  duplicate titles, nested tables, monster tables, math PNGs, and a phantom
  ALEXANDER-I boundary invented by a FLAKY ORACLE — orphaned KPR_NCD.exe daemons
  (Previewer is single-instance; broken $_-mangled kills left zombies) made
  bisection verdicts unreliable; protocol now: taskkill KPR_NCD between runs,
  timeout counts as choke, verdict files (conversionLog.csv + conv_temp/
  {errorInfo,featureInfo,metrics}.json + conversionReport.ion) read EVERY run —
  ~100 signals instead of 1 bit.  KP CLI: `"Kindle Previewer 3.exe" book.epub
  -convert -output DIR -locale en` — headless probes, no GUI clicking.
  **SCALE: local Previewer cannot convert past somewhere in (21MB, 249MB]** — full
  (578MB) and half (249MB) both die SILENTLY pre-rasterizer ("successful" 2-row log,
  GB of intermediates, empty outputs); the 3GB `-Xmx3072m` heap was overridden to
  12g via `_JAVA_OPTIONS` (env opts are processed last → win) and the half STILL
  died → the ceiling is native/hardcoded, NOT Java heap.  CONCLUSION: Previewer
  verifies CONTENT, KDP's server verifies SCALE (the only untested variable).
  User verdict (vol-1 kindle GUI): opens, looks good, behaves well — tables, math,
  glyphs all fine (mirroring pending its PNG upgrade).  **COVER added (user req):
  build-time drawn 1600×2560 in the site mark's language (cream #f5f1eb, ink
  #2c2416, double-rule frame, EB medallion, Georgia, auto-fit title), per-book
  subtitle, cover-image property + kindle legacy meta, cover.xhtml first in spine.**
  Overnight chain (in flight): all artifacts rebuilt with covers + kindle
  content-verification batches vols 2–28 in threes → full content coverage
  locally; then the KDP draft upload is the single remaining test.
- **THE POSITIONAL CONVERTER BUG (2026-07-28, CASTANETS) — the last and strangest
  class.**  Vol-5 bisected (11 monotone rounds) to a 254-word pure-prose stub;
  probe series: body-swap passes · Greek-xlit-removed passes · **the IDENTICAL
  span shifted ~100 bytes passes** → Amazon's ET rejection is BYTE-OFFSET-
  dependent (chars common corpus-wide; no power-of-two file-offset correlation —
  the sensitive offsets live in their internal transforms).  Undetectable
  locally, ~1 strike per few hundred MB, any global byte shift dislodges it.
  Operational fix: `--nudge N` shifts every chunk's offsets; protocol = convert →
  silent Not-Supported (EMPTY errorInfo) → rebuild nudge+1 → reconvert.  Also:
  table SPLITS now respect rowspan extents (a cut through a span left dangling
  rowspans = silent reject, 3 self-inflicted; belt-clamp + boundary rule,
  regression-tested).  Full-book nudge-retry conversion IN FLIGHT.  Also en
  route: single-vol probes PASSED vols 6,7 (giant-table + overlap fixes proven);
  vol-1 + cover passes; suite 495.
- **DIET ALPHA BUG (user: "the full epub blacks out inline glyphs in A") — v1 diet
  DROPPED the alpha channel**: `convert("L"/"RGB")` composites transparent glyph
  backgrounds onto BLACK — the A letterforms shipped as solid-black 140-byte
  1000px rectangles (the user's fine-looking "vol 1" was a pre-diet import in
  Thorium's library; both r6 books actually carried the same black bytes —
  byte-compare proved it before the theory).  Fix: alpha-bearing images keep
  alpha — no JPEG, FASTOCTREE palette PNG; params tag bumped `a1` → full cache
  re-encode; regression test (transparency + strokes + background all survive).
- **Thorium at full scale (user, real hardware): the 1.44GB pre-diet book imported in
  seconds and reads fine** — the single-book question's first hardware answer is YES.
- Suite **488 green** (16 new pack/conformance/diet tests + 1 fold test).  Site render
  byte-untouched (`bundled=None` + target="site" paths identical; suite proves it).
- **FOUR-BRANCH NAV (user spec): Contents = Volumes · Topics · Title Search (A–Z
  as child) · Contributors (A–G/G–M/M–S/S–W).**  "Volumes" is a span group header;
  branch order follows spine order per variant (NAV-011).  Search page gained a
  TAPPABLE LETTER ROW (user: Thorium swallows keyboard input into content docs —
  clicks always work); lookup pages are FRONT MATTER (user: buried below 28
  volume rows).  `dcterms:modified` = BUILD TIME now — a fixed constant made every
  revision the same publication identity, so reader libraries silently kept OLD
  imports (the missing-topics and glyph false-trails both traced to this).
- **FINAL ARTIFACTS (repo root, ALL epubcheck 0/0/0, r10):** `eb1911.epub` —
  37,226 articles / 870 chunks / 10,660 images / **559MB** / 942 nav links;
  `eb1911-fullnav.epub` — the EXPERIMENT: all 37,226 articles as a third nav
  level (38,168 links, 2.3MB nav) — decides whether Thorium's native panel
  search replaces the scripted page; `eb1911-vol01.epub` — 17.6MB control;
  `eb1911-vol01-kindle.epub` — 21.6MB (PNG math, Kindle Previewer ladder).
  Suite 489.
- **REMAINS (validation ladder):** the rest of the hardware ladder — Calibre, Kindle
  Previewer conversion, Kobo sideload (first-open pagination + FRANCE page-turns),
  Send-to-Kindle only if that channel matters (559MB exceeds its 200MB cap; KDP is
  the Kindle sale channel); mirror the 69 absent + ~11 remote score images into
  data/images; the vol-23 attr-slot page-marker pipeline fix; image-cap tuning per
  class if device tests ask.


### Sessions 2026-07-23/24 — SWEEPER-REMOVAL CAMPAIGN COMPLETE; SHIPPED + production-verified

The junk-removal campaign ([`docs/sweeper_removal.md`](sweeper_removal.md) — the full
per-item ledger) is CLOSED, rebuilt (55:26, exit 0), DEPLOYED, and verified on
production.  Every inventory item resolved:

- **J1 noinclude `{|`/`|}` rescue DELETED** — the guarded extractor bug died with the
  whole-volume architecture; the rescue itself was silently swallowing whole pages
  (LIBRARIES ws 573/584 — **recovered, production-verified**) and chopping cross-page
  tables (INDIANS 19→10 spans).  83-article A/B: zero loss.
- **J2 `close_unclosed_attr_quotes` DELETED** — unterminated-attr-quote tolerance moved
  to the attr READERS (`_KV_RE`, `_SPAN_TITLE_OPEN_RE`: a value never crosses its tag's
  `>`); the repair had been injecting quote chars into OCR prose.
- **J3/J4/J5 preprocess conversions RELOCATED** — `<bdo>`/`<small>`/`<big>` are
  walker-lifted TAG-IMPLIED stylers; `{{{name|default}}}` decodes in `fold_cell_attrs`
  (attr context) + a PARAM_DEFAULT element (prose).  **The preprocess discipline ledger
  is CLOSED: chain == VETTED** (J8 `_decode_entities` ruled VETTED — transport decoding),
  enforced live by `test_preprocess_discipline`.
- **J6 `_contain` ACQUITTED** — browser-verified real (unclosed opens nest the xref card
  inside the article card; mid-body stray closes spill 47/63 paragraphs out of
  `.body-text`); it IS the minimal byte-preserving balancer.
- **J7 xref re-scan GONE end-to-end** — recognition producer-stamped at the site
  (`«LN[w]:window»` at `(q.v.)`, `«LN[see/see_also]:window»` at see-cues; windows =
  UNASSERTED extents the resolver cuts against the title index — tier-major spans,
  minimal-cut-per-candidate, window-coverage pick, grow-to-title display);
  `_wrap_resolved_xrefs_in_body` + `_looks_bibliographic` + `_protected_ranges` + the
  whole extraction armory DELETED.  Resolution upgrades (all data-adjudicated):
  tight-multi sees bind topic-free (+223), fisher-cosine backstop for single-word sees at
  τ=0.65 (+60), qv folded into link policy (its loose ladder produced only junk).
  **Xref ledger vs prior production: link +86 · see +386 (525→911) · see_also +62 ·
  author ±0 · net +429 resolved, −37 junk binds dropped.**
- **Rebuild adjudication**: zero visible content loss (54 nominal losers all dissected —
  panel deltas, 2 byline homonym relocations, J1/J2 junk-chrome removal); render-leak
  floor IMPROVED (template 27→23, tag 22→20, attr 5→4); topic index 99.995% identical
  (2 fuzzy-tier coin-flips, both pre-existing-wrong; pins queued).
- **Leak audit instrument REPAIRED** (had crashed on every article since `page_number`
  left ElementContext; verse mask predated `{{IVERSE:}}`): honest reading **BROKEN 159
  in 56 articles (0.15%)** — ~135 OCR pseudo-tags, 9 unpaired styler names missing from
  the paired-wrapper registry (queued), 2 `<chem>` (parked).

**Also this session:**
- **Wide tables by MEASUREMENT** — the cols≥10 proxy (wrong ~60%: 180 false wraps, 615
  missed overflows incl. CONSTELLATION) replaced by the math-style pipeline:
  `measure_table_widths.py` (browser-measured vs the fixed 590px body column, hash-keyed
  cache) → `annotate_table_markers.py` stamps `«TABLE[cols:N|wide|`, wired into
  post_export → render keys on the fact.  886 wide tables; 434+49 articles re-rendered.
  **Ships NEXT deploy** (finished after this deploy's sync).
- **Vol 7 scan-leaf fix** (user-reported): leaves 33-34 = CONSTELLATION Plates I/II →
  UNNUMBERED_LEAVES + TRUSTED_RUNS[7]=(35,13,41,19), scan-verified; leaf-side only
  (36,691 baked citations, 0 mismatches); **live on production**.
- **`tools/serve.py` speaks production's URL space VERBATIM + is_local ELIMINATED**
  (2026-07-24, user-requested): serve.py 200-serves viewer.html for `/article/*`
  (CloudFront-style rewrite, was a 302 to `?article=`), aliases `/data/articles|scans/*`
  + `/data/*.json` → data/derived, `/download/*` → data/derived/download, and the
  `/search-api/*` proxy REWRITES Authorization to the local dev key (clients always send
  the prod key).  Then every local/production switch died: `filenameToUrl` lost its
  isLocal param; all `IS_LOCAL ?` ternaries (DATA_BASE/MEILI/TOC/scans/nav bases) went
  to the production form; the `document.write` base-injection head snippets became
  static tags (hand pages + all 5 page builders, generated pages regenerated);
  viewer.html's `fixArticleHrefs` rewrite layer DELETED and the history fork reduced to
  the clean-URL branch (the `?article=` dev form still loads and canonicalizes);
  Python render dropped `is_local` end-to-end (`_article_url`/RenderContext/
  render_article/_build_xref_href + callers) — the production output is byte-identical
  (`/article/{stem}` was already the baked form), so NO rebuild needed; goldens
  rebaselined (adjudicated: 180 changed lines, every one exactly `.json`-in-href
  removal, +2 inline records); check_deploy_refs.py simplified (ternary/doc.write
  parsing gone; `/data/derived/` in shipped HTML now rightly 404s as a leak).
  472 tests pass; server restarted; curl 18-point + Playwright 6-page smoke all green
  (zero console errors; address bar canonicalizes).  Viewer pages ship next deploy.
- **GoatCounter bot-gating** (user): `gc-gate.js` counts on first human input; deployed.
- HF publish now runs inside deploy.sh automatically (write key cached).
- **MAPS ARC, slice 1 LANDED** (2026-07-24, user's revised spec — Map link like Plates,
  double-click inline thumbnail, Perthes maps also linked to Stieler originals, both
  colour versions in the download):
  · `data/maps.json` — hand-curated registry (like corrections.json): 15 confirmed
    EB1911 Perthes plates bound to 17 articles (england_and_wales → ENGLAND+WALES,
    north/south_america → also AMERICA), plus unbound russia (Stieler Bl. 1+2) and
    china rows awaiting confirmation the printed volumes carried those plates.
  · `tools/maps/process_stieler.py` — Rumsey zips (data/raw/maps/, NOT deploy-synced)
    → page-cropped display (~3200px) + full-res JPGs in data/images/maps/.  Crops are
    HAND-TUNED fractions per map, each verified against _previews/ overlays (auto-crop
    was defeated by content-dark maps + the bright fore-edge stack); 9 masters done —
    8 atlas photos + the Australia composite (already edge-to-edge).
  · `maps.html` — mechanical registry viewer: #id → EB1911 plate + "the Stieler
    original" (multi-sheet aware, russia shows Bl. 1+2); no hash → gallery of the 15
    confirmed maps (unbound rows hidden until adjudicated); europe's broken plate
    falls back to the Stieler with a "good scan wanted" notice.
  · viewer.html — Map link is a client-side overlay from the registry (topic-overlay
    precedent, no rebuild needed): "Map: Switzerland" in the Plates slot; double-click
    on the inline thumbnail (SOUTH AFRICA only, per inline_file) → maps.html#id.
  · Download: `build_maps_bundle()` (export/download.py) → eb1911-maps.tar.gz
    (228MB, 35 files + maps.json as manifest; every referenced file must exist or it
    raises).  Kept SEPARATE from the corpus bundle (agent dataset stays lean).
    deploy.sh ships the bundle + maps.html + /data/maps.json; download page rewritten
    (docs/download.txt "The maps." section) and regenerated.
  · Playwright-verified locally: gallery 15 · #switzerland both images · Map line on
    SWITZERLAND + WALES (shared plate) · SOUTH AFRICA dblclick lands on #south_africa.
  · REMAINS: confirm russia/china plates (then bind articles); better europe plate +
    the missing pristine encbr11 scans (user fetching from Rumsey); Emery Walker
    colour maps (the non-Perthes rest) — registry rows as scans land; production
    verification after next deploy.
- **DETERMINISM ARC (2026-07-25, user-directed: "fix determinism first, then
  redeploy") — PROVEN: two consecutive Phase 4→6b4 builds fingerprint-IDENTICAL
  (37,226 articles, 0 diffs).**  The 2026-07-24 rebuild adjudication caught xref
  targets, plate parents, and bylines flipping between identical-code rebuilds —
  parallel Phase 2 changes DB heap order and row ids, and every positional
  tie-break inherited it.
  · `article_sort_key` (export/article_json.py) — ONE content-derived total order
    (volume, page range, title, section slug = the stable-id's own hash source) —
    applied at every seam a chooser feeds from: the export loop (→ index.json →
    every LinkResolver candidate list), global title→filename maps (uniform
    deterministic FIRST-wins), stable-id dedup (was keyed on per-rebuild row ids),
    xref/contributor post-phase feeds, the vol-29 roster title map, and the
    frontmatter linker (whose subject SETS also iterated hash-randomized and whose
    footprint disambiguator scores against binds made earlier in its own loop —
    the SAMARA town/government flip).
  · Semantics still decide wherever semantics exist: the fisher is order-
    independent (verified: PLEIADES-from-ORION picks mythology with the bag
    reversed); order only breaks true dead-heats.  The ORION flip traced to the
    TOPIC MAP (an upstream resolution output) gating the fisher off via the
    single-match short-circuit — deterministic inputs now keep the gate stable.
  · CORROBORATION PRINCIPLE (vol-29 credit binder + frontmatter linker): a credit
    naming an article its contributor is ALREADY bound to (footer signature =
    segment-ownership ground truth) is a corroboration of that bind, never a
    mandate to bind a different homonym.  Adjudicated effect: bylines moved to
    the SIGNED sibling across ~60 homonym families — ASIA's three authors off
    the 214-word Roman-province stub onto the 36k-word continent; BRAZIL, ANNE,
    SAMARA/SAMARKAND/KURSK/IONIA all verified same pattern (footer seqs on the
    keeper, guessed credits absorbed).  DAVID false-positive (Welsh princes
    minted W. R. Smith's biblical-David credit) caught by adjudication and
    killed by the same rule.
  · Aurora plates re-parented to AURORA POLARIS via a NEW image-name signal tier
    in plate_parent.py (Commons "1911 Britannica - <Article> - …" filenames name
    the parent; the running head says only "Aurora" — five same-page articles).
  · Wide-table annotation moved INSIDE the resolve→render loop as a `decorate`
    hook on the FINAL baked body (the width cache keys on span bytes; annotating
    before «LN» targets bake silently cache-missed every linky table — the
    13-article gap).  post_export gained a ONE-SHOT guard: zero extracted xrefs
    on a full corpus = already-baked bodies → RAISE before writing (a re-run on
    baked bodies stripped 11,474 articles' window displays mid-arc; recovered
    by re-running Phase 4+; DB was never at risk).
  · rebuild_all.sh Phase 6h also rebuilds the maps bundle now.
- **Post-deploy page fixes (2026-07-25, deployed via deploy_html.sh + verified)**:
  · index.html volume legend/label agreement — volumes.json's first_title/
    last_title are ORPHANED stale fields (no pipeline writer; vol 9 said "E");
    ONE shared derivation now (volArticles + volRangeWords, first word of
    first/last page-ordered titles, both display sites).  volumes.json's title
    fields now unread → cleanup-campaign candidate.
  · Maps relocated per user: ancillary.html gains a "The Colour Maps" panel
    (registry-driven list); maps.html is a single-map display surface in the
    site card chrome; hashless → ancillary.html#maps.  download.txt edited by
    user + regenerated.  deploy_html.sh now ships no-cache (was max-age=300,
    against the 2026-07-15 rule).
  · **Homonym-link survey** (user-approved follow-up work item): 1,998 baked
    links land in ≥2-member same-title families; lead-cosine oracle: 1,353
    agree · 293 close · 352 decisive disagreements (UPPER bound — includes
    intentional hatnote cross-links like COLOPHON→COLOPHON).  CONCERT→ALLIANCE
    binds the Ohio town on production (confirmed wrong).  Proposed fix: route
    family ties through the fisher WITH prose context; adjudicate a sample of
    the 352 first.  Artifacts: family_links_survey.json / family_map_survey.json /
    family_disagreements_survey.json (repo root).
  · 472 tests green throughout.  **DEPLOYED 2026-07-25 + PRODUCTION-VERIFIED**:
    maps.html gallery (15) · #switzerland both images · Map line on SWITZERLAND ·
    SOUTH AFRICA dblclick → #south_africa · eb1911-maps.tar.gz (228MB) served ·
    ASIA byline on the continent (T.H.H./P.La/R.S./C.El), stub empty · Aurora
    plates ↔ AURORA POLARIS both directions · CONSTELLATION leaves 31–36 + all
    3 expand buttons (probe note: label is "Expand (N columns)" WITH parens) ·
    ORION → mythology PLEIADES · SAMARKAND byline on the signed sibling ·
    zero console errors.

**Production-verified (all six):** LIBRARIES recovery · SILESIA's Breslau + Seven
Years' War (q.v.) links · FROISSART see-bind in panel · vol 7 scan leaves · gc-gate.js ·
SAMARA byline on the government article.

**Queued (new, small):** paired-wrapper registry names (`left margin`, `outdent`,
`dent`, `flex wrap centre`) · MARCH/BEJA TOC disambiguation pins · GEOMETRY-ANALYTICAL
see class (cue followed by link + «SC» qualifier) · DIEGO particle-count refinement ·
0.60–0.65 cosine band (~100 sees, needs adjudication).

## PREVIOUS STATE (2026-07-20)

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

- **Suite:** **472 green** (transform + render snapshots rebaselined through the campaign,
  each adjudicated before writing).
- **Last *deployed* rebuild: 2026-07-24** — the campaign rebuild (55:26, exit 0), deployed by the
  user, **production-verified** (six-point checklist above).  HF publish rode the deploy.
- **Pending for next deploy:** the wide-table measurement work (886 tables re-annotated +
  re-rendered locally after this deploy's sync passed).
- **Working tree:** clean at ship; per-item commits banked throughout the campaign.

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

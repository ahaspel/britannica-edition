# Junk-removal campaign — master plan and full inventory

Opened 2026-07-23.  This is the ONLY active work: no builds, no deploy, nothing
shipped until every item below is gone.  Each removal is verified in isolation and
one at a time; a single clean rebuild at the end is the corpus-wide proof.

## The governing rule ([[feedback_transform_only_two_places]])

There are exactly TWO places it is legitimate to transform the raw source:
1. **The preprocessor** — extremely limited, designed only to ELIMINATE WIKI
   CRUFT (removal).  It must not convert one construct into another.
2. **The producers.**

Anything else is a sweeper.  The operative line is **removal vs conversion**:
removing cruft (noinclude, comments, chrome, editorial annotation, trailing
whitespace) is legitimate preprocess; converting one construct into another
(`<bdo>`→`<span>`, `{{{x|d}}}`→`d`) is producer work wherever it sits.  A
context-free CONVERSION is still a producer's job — context-freeness is
necessary, not sufficient, for preprocess ([[feedback_context_sensitive_is_producer]],
loophole closed 2026-07-23).

Why this class recurs (the mechanism, not ignorance of the rule): the standing
quality report counts LEAKS in `rendered_html`.  A sweeper exists to stop a leak,
so writing one makes the only measured number go DOWN — it scores as success at the
moment it is written.  The fix is to make the discipline executable and the
violation show as a regression, not to write more rules ([[feedback_sweepers_hide_bugs]]).

---

## FULL INVENTORY (8 items)

### Sweepers — compensate for a downstream bug (fix upstream FIRST, then delete)

**J1. `{|`/`|}` rescue** — ✅ **DONE 2026-07-23: DELETED, no extractor fix needed —
and the rescue itself was causing production content loss.**
`strip_noinclude_blocks` is now the plain wholesale strip.  Findings, in order:
  * **The upstream bug is already dead.**  The "extractor pairs a `{|` with a
    `|}` many pages later, swallowing prose" failure belonged to the pre-stream
    architecture; the whole-volume preprocess + the ONE balanced matcher pair a
    continuous cross-page table correctly.  A/B over ALL 83 affected articles
    (116 noinclude-table-marker pages; article-scope raw-stream walk, rescue vs
    plain strip): **plain strip loses ZERO words anywhere** — including UNITED
    STATES, THE (Climate/Fauna/Population intact, the original pin).
  * **The rescue was the loser.**  Wikisource wraps some pages in a 2-column
    layout table (`{|cellpadding…` in the header noinclude, `|}` in the footer
    — print-mimicry for the standalone page view).  The kept opener wrapped the
    page's MAINSPACE PROSE in a bogus table whose parse dropped it whole.
    Production-verified: **LIBRARIES is missing ws pages 573 and 584 from the
    shipped body** (probed all 116 pages against the shipped corpus; those 2 are
    the only full-page losses — elsewhere the article boundary happens to split
    the kept pair and the lone halves fail open).  The A/B also shows the rescue
    dropping table content in ~25 more articles at page seams; exact per-article
    recovery lands in the rebuild diff.
  * **The rescue also chopped structure**: a continuous table re-closed/reopened
    at every page seam (INDIANS, NORTH AMERICAN's 13-page table: 19 «TABLE»
    spans → 10; FRANCE 57→54; JAPAN 69→65).
  * Sweeper poetry ([[feedback_sweepers_hide_bugs]]): the guard written to stop
    content loss was, by 2026, the only thing CAUSING content loss.
  * Pin updated: `test_noinclude_halves_are_not_transcluded` now asserts table
    delimiters strip with the rest (the old carve-out is disproven and gone).
  * Harness note: article-scope A/B joins WHOLE raw pages, so its A-side
    overstates loss where an article boundary would split a kept pair —
    production truth was established by probing the shipped bodies directly.

**J2. `close_unclosed_attr_quotes`** — `pipeline/stages/source_cleanup.py`.
Repairs a tag with an odd number of `"` by inserting one before the `>`.  Upstream
bug: the missing quote makes the figtable DOMParser swallow the rest of the cell
(ABBEY Fig. 10).  363 corpus-wide — a class, not a typo list.
Method: route the class through a producer (or `data/corrections.json` if instances
are individually addressable) → delete the repair → diff.

### Misplaced transforms — construct conversion in preprocess (relocate to producers)

**J3. `_normalize_bdo`** — ✅ **DONE 2026-07-23.**  `<bdo>` is now a walker-lifted
TAG-IMPLIED styler: lifts ungated like `<ins>` (`_TAG_STYLER_RE`), routes to
HTML_STYLE, and `_html_style_peel` derives `unicode-bidi:bidi-override;
direction:X` from the tag — the same shape as an attr style.  Preprocess
conversion deleted; ledger shrunk.

**J4. `_normalize_size_tags`** — ✅ **DONE 2026-07-23.**  `<small>`/`<big>` ride the
same TAG-IMPLIED styler path (`font-size:smaller/larger` derived in the peel).
Verified the honest way (below).  Two findings along the way:
  * **`walk_article`-based A/B is VACUOUS for preprocess changes** — it joins
    stored `ArticleSegment.segment_text`, which was cut from the OLD-preprocessed
    stream, so both sides walk already-converted text.  The first "251/251
    byte-identical" was this trap ([[feedback_verify_the_counter]]).  The honest
    per-item harness: RAW page → corrections+quote-runs → OLD chain (deleted
    conversions replicated verbatim) vs NEW `_clean_and_heal` → `process_elements`
    → byte-compare.  All 176 affected raw pages identical except two FRONT-MATTER
    pages (vol14 p8 / vol27 p10, below each volume's ARTICLE_WS_RANGE start; the
    diff is inside a raw-carried `{{EB1911 contributor table/entry}}` arg, and no
    front-matter consumer runs preprocess — Phase 1b parses raw wikitext).
  * **Bounder/peeler mismatch fixed** (SLOVENES, `<small caps>A.D.</small caps>`):
    the walker's balanced matcher accepts a junk-attred close tag, but
    `_html_style_peel`'s trailing strip (`</tag\s*>$`) did not — the consumed
    closer survived into the recursed inner and re-emitted as a stray `«/SPAN»`.
    Strip now `</tag\b[^>]*>$`, matching what the bounder bounded.  This was
    latent for `</span junk>` too.
  * The walker's `_OPENER_HINT_RE` must list every liftable opener — the first cut
    omitted `<bdo`/`<small`/`<big` and the lift silently never fired (caught by
    the transform snapshots, NOT by the vacuous A/B).

**J5. `_resolve_param_defaults`** — ✅ **DONE 2026-07-23.**  Corpus survey: 11
`{{{name|default}}}` instances, ZERO bare `{{{name}}}`.  Every ARTICLE-space
instance is in ALGEBRA's one table (ws 01-0640), ALL inside attr slots — so the
decode moved to `_table_fold.fold_cell_attrs` (the slot's producer, like the
`{{=}}` attr-decode); the other 4 instances are vol 1 front matter (ws 3–4,
outside ARTICLE_WS_RANGE, no preprocess consumer).  Plus the landmine the
harness itself tripped: a PROSE `{{{name|default}}}` CRASHED the classifier
(the generic `{{` matcher bounds it two-of-three; `_derive_double_brace_label`
raises on the un-template-like raw) — against [[feedback_honesty_surface_failures]].
Fixed properly: `_PARAM_REF_RE` bounds the construct whole in the walker →
classifier routes `PARAM_DEFAULT` (recurse-slot family) → producer renders the
recursed default / carries a bare one literally (faithful leak, never a crash).
Verified: ALGEBRA + both front-matter pages byte-identical old-chain vs new.

### Render-layer

**J6. `_contain`** — ✅ **RESOLVED 2026-07-23: KEEP — acquitted, off the junk list.**
The open question is answered empirically: **the escape is REAL and VISIBLE in a
real browser against the production CSS.**  Method: the actual `viewer.html`
served locally, article JSONs re-rendered with `_contain` patched to identity,
headless Chromium (Playwright), DOM + computed-layout + screenshot comparison.
The 46 unbalanced articles (corpus scan of «DIV»/«SPAN» marks) split three ways:
  * **32 unclosed opens** — without `_contain`, `body-text`'s own close tag is
    consumed by the stray div, and the Cross-references / notes cards after it
    parse as CHILDREN of the article card: visible box-in-box nesting, no card
    gap (screenshot-verified on CONTINUED FRACTIONS).
  * **5 mid-body stray closes** — the worst class: everything after the stray
    spills out of `.body-text` and loses its layout.  Measured on AURORA
    POLARIS: 47 of 63 paragraphs land outside `.body-text`, shifted 112px left
    (LIBRARIES has 194k chars after its stray).
  * **11 tail stray closes** — benign either way (only whitespace text nodes
    shift; DOM effectively identical).  (48 strays across the 46 articles —
    QUEENSLAND carries three.)
So deletion is off the table, and no replacement is needed either: `_contain`
already IS the "minimal byte-preserving div/span balancer" this item's fallback
specified — a 15-line depth counter with exactly the HTML5 fragment-parsing
semantics (drop a depth-0 close, close standing opens at the end), applied at
the `body-text` boundary where the styling contract lives.  It is legitimate
whole-body containment, not a sweeper: "is there a matching open?" is context no
producer can have ([[feedback_recursion_cannot_provide_context]]), and it is
blind to WHY a half is unpaired — that stays the producer's business.  EPUB
never needed it (`to_xhtml_body`'s html5lib parse applies the same semantics),
but it is harmless there.  Pinned by
`test_unpaired_styler_marks.py::test_body_fragment_cannot_close_its_own_container`.

### Unaudited — may add items

**J7. Late passes that RE-SCAN PROSE for an unmarked signal** (a CLASS, corrected
2026-07-23 from an earlier overreach).

CORRECTION: this was first recorded as "raw-source-changing junk."  Applied
strictly, that is WRONG — NONE of these touch raw source.  They run post-walk on
the produced marker stream, so the two-places rule (raw source) does not govern
them; `no_marker_sweepers` + `recursion_cannot_provide_context` do.  Late binding
itself is LEGITIMATE: resolution (which article / which person) needs the whole
corpus, impossible at per-article walk time.

The junk is narrower and is a real class.  Discriminator, exact:
  * CLEAN reader — reads an EXPLICIT marker the producer emitted (`sections.py:45`
    reads `«SEC»`/`«SH»`; `download.py:146` reads image markers).  Leave alone.
  * JUNK — RE-SCANS prose for a signal the producer SAW but never marked, then needs
    heuristic gates to survive the re-scan.

SHARPENED DISCRIMINATOR (a real case forced this, 2026-07-23): re-scanning is JUNK
only when the signal is STRUCTURALLY RECOGNIZABLE at walk time and we discarded the
position; it is LEGITIMATE when RECOGNITION ITSELF needs corpus context unavailable
at walk time.

  * **Xref decorator** (`article_json.py:_wrap_body_xrefs`, line 339) — JUNK.
    `(q.v.)` is a literal token and its target (the parenthetical, or the preceding
    word) is structural, so it IS walk-time-recognizable.  Yet it is a DOUBLE
    re-scan: `extract_xrefs` scans the body for q.v./see and FINDS the position,
    returns records; `_wrap_body_xrefs` scans AGAIN to re-find it, needing
    `_looks_bibliographic` + `_protected_ranges` to dodge prose false-matches.
    Fixable: recognize q.v./see in the walker → producer emits a pending-xref marker
    at the site → late pass reads it and resolves only the target.
  * **`_looks_bibliographic`** — pure symptom of the xref re-scan; dies with it.
    (User: "no reason to live.")  In the XREF path only.
  * **Contributor harvest** (`extract_contributors.py:_harvest_signature_contributors`,
    line 249) — NOT junk (corrected from an earlier claim).  A bare `(J. M. M.)`
    signoff has NO structural marker; the ONLY thing that identifies it as a signoff
    is matching the ROSTER (corpus context), so recognition is irreducibly late — the
    same reason xref RESOLUTION is late.  A producer cannot do it at walk time (no
    roster), and "a bare parenthetical" is not a construct worth marking, so
    re-scanning for `(...)` + roster-match IS the correct mechanism.  Its spacing /
    capital-lead / single-initial GATES are inherent false-positive prevention
    ([[feedback_contributor_zero_false_positives]]), NOT re-scan symptoms — they STAY.
    A READER (returns ids, no mutation).

So contributors and xrefs land on OPPOSITE sides of the sharpened line: contributor
recognition needs the corpus (legitimate late); xref recognition does not (the
re-scan and `_looks_bibliographic` are avoidable junk).  The clean in-tree model
(`sections.py`/`download.py` read explicit `«SEC»`/image markers) is the target for
the XREF fix; the contributor pass is already as clean as its unmarked signal allows.

Value being preserved: contributor attribution; and turning non-wikilink q.v./see
refs into `«LN»` (which feeds the xref panel — CONFIRM that dependency before
touching the writer).

NOTE: `export/body_postprocess.py`'s three functions are all READERS/helpers
(`_protected_ranges`, `_looks_bibliographic`, `_clean_surface_for_matching`) — the
module is not itself a transform; it feeds the xref decorator above.

**J8. `_decode_entities`** — `pipeline/stages/preprocess.py`.  `&nbsp;`→char:
encoding-artifact removal (cruft) or a transform?  Borderline — owner's call.

### Genuine acquittals (READERS — build a throwaway string, never transform the shipping body)

* `detect_boundaries.py:77,244` — cleaned copy for heading comparison.
* `extract_contributor_bios.py:33` — plain-text bio field (re-confirm it is not
  stored as the body).

---

## ORDER OF WORK

0. ~~**Build the enforcement test FIRST**~~ — DONE (`test_preprocess_discipline.py`).
   Each removal now shrinks `_FROZEN_CHAIN`, which is its own proof.
1. **J7 audit** early — it may surface more items and change the plan.  ← NEXT
2. **J3, J4, J5** (relocations) — no upstream bug, lowest risk; they exercise the
   verification harness before the hard ones.
3. **J6** — resolve the escape question, then delete-or-minimal-balancer.
4. **J1, J2** (sweepers) — hardest, highest payoff, fix-upstream-then-delete.
5. **J8** — owner decides.
6. **Final clean rebuild** — the corpus-wide proof (`words LOST` = 0).

One item per change, never bundled.

## Enforcement — DONE (`tests/unit/test_preprocess_discipline.py`, 472 green)

* **Classified chain, not a snapshot.** A frozen `chain == tuple` test is only a
  change-NOTIFIER — every planned removal changes the chain, so it would be
  re-baselined at each step (ceremony, not audit).  Instead every step is
  classified `_VETTED` (pure cruft removal) / `_JUNK` (to remove) / `_UNDECIDED`,
  and the standing invariant is `set(chain) == VETTED | JUNK | UNDECIDED`.  It holds
  THROUGHOUT the campaign: removing J3 deletes `_normalize_bdo` from the chain AND
  the ledger in one commit (invariant stays true); deleting it from the ledger only
  fails (can't fake a removal — verified); adding an unclassified step fails (no
  silent sweeper).  `_JUNK` is the public ledger; campaign done when it is ∅ and
  chain == VETTED — a POSITIVE cleanliness claim.  The J1 `{|` rescue lives INSIDE
  `strip_noinclude_blocks` (a VETTED step), so it is a behavioral pin, not a chain
  member — the known blind spot below.
* **Word-preservation** — a cruft-remover may delete content or insert WHITESPACE,
  but must not introduce a new non-whitespace token.  A conversion (`<bdo>`→`<span>`
  introduces "span") fails; comment→space passes.  A guard-on-the-guard asserts the
  check actually fires on a real conversion.  (Char-level subsequence was rejected:
  `strip_html_comments` inserts a space, so whitespace-insertion must be allowed.)
* **KNOWN BLIND SPOT** — neither layer catches a change to the BODY of an existing
  chain function that alters WHAT it keeps/removes (e.g. the 2026-07-23 noinclude
  wrapper-half change modified `strip_noinclude_blocks` internally; the chain was
  unchanged and the kept tokens were already in the input, so both layers pass).
  Such changes need a per-function BEHAVIORAL pin.  The noinclude case is pinned by
  `test_noinclude_halves_are_not_transcluded` (test_unpaired_styler_marks.py); add
  a pin for any cruft-remover whose "what it removes" is load-bearing.
* TODO: wire into a pre-commit / `Stop` hook so it cannot be skipped.

## Verification harness (built + tested)

* `tools/diagnostics/export_fingerprint.py` records a **content signature**
  (`content_sha`/`content_len` — rendered HTML reduced to its visible word
  sequence).  `--diff` separates `render changed` (any markup move) from `CONTENT
  changed` → `words LOST`.  Counter pinned by `tests/unit/test_content_signature.py`
  ([[feedback_verify_the_counter]]).
* **Content baseline: `data/derived/post_revert.tsv`** — captured from the clean
  2026-07-23 rebuild, content-aware (new format).  Every removal diffs against it.
  (`pre_unpaired_styler.tsv` is OLD format, render-hash only — do NOT content-diff
  against it; the column layouts are incommensurable.)
* Per-item, verify WITHOUT a full rebuild: run the affected articles through the
  pipeline in-process ([[feedback_verify_through_pipeline]]).  Success = render
  change confined to the construct's articles AND `words LOST` = 0.
* Loss-side `overlap_audit` (rebuild Phase 6f) is the standing corpus counterweight.

### Per-removal pins (capture from the clean corpus, then assert)

* **J1** — ✅ satisfied: the 83-article A/B showed `words LOST` = 0 everywhere,
  UNITED STATES included; the standing pin is the updated
  `test_noinclude_halves_are_not_transcluded`.  At the rebuild, EXPECT content
  GAINS (LIBRARIES ws 573/584 recovered) — a gain is the fix landing, not a
  regression.
* **J2** — pin ABBEY's Fig. 10 cell content; after routing the malformed-quote
  class its `words LOST` must be 0.

## Design conclusion — three scopes, and the regex discriminator (2026-07-23)

Worked out by testing "recognition is the classifier's job" against q.v.,
contributors, and footnotes — the two re-scan passes (J7) are the counterexample
to this, and it is what they violate.

Recognition NEVER needs the whole article (candidate invariant; survived q.v.,
contributor, footnote; open flank = ordinal "first-use" recognition, untested
because we don't do it).  There are exactly three scopes, each with ONE operation:

| scope | operation | reads |
| --- | --- | --- |
| local | RECOGNITION (own content + neighborhood + structural containment) | prose (regex OK — it is local) |
| whole-article | ordinal assignment (footnote numbers) / collection (TOC, panel) / article-resolution (ref→def) | the MARKER stream |
| corpus | RESOLUTION only (xref target, contributor roster) | the MARKER stream + index/roster |

Footnotes prove whole-article scope is real AND never recognition: recognizing a
`«FN»` is local; its NUMBER is ordinal assignment (a producer sees one element,
not the running count), done by a whole-article pass counting markers in order.

THE DISCRIMINATOR (greppable, enforceable): a prose regex in a whole-article or
corpus stage IS recognition that leaked out of the classifier into the wrong
scope — i.e. junk.  Whole-article and corpus passes read the MARKER stream, never
prose, so they never need a prose regex.  This flags `_wrap_body_xrefs`,
`_harvest_signature_contributors`, `_QV_PATTERN`, `_SIGNATURE_RE`,
`_looks_bibliographic` on sight, no intent argument required.

Target end state for the late (corpus) pass: read `«QV:term»` / `«SIG?:initials»`
/ `«LN»`, look up index/roster, wrap-or-drop.  ALL recognition (extent walk, gates,
`_extract_qv_target`, the `(...)` scan) moves to the PRODUCERS, where the content is
local.  Heuristic QUALITY (e.g. "Council of Trent" → "Trent") is a separate, open
axis that travels WITH the logic to the producer — it is not a reason to keep
anything late, and placement vs quality must never be conflated again.

## Build progress — contributor recognition relocation (J7 first target)

BRICK 1 — DONE (2026-07-23, 478 green).  `recognize_signoff_initials(part)` extracted
in `extract_contributors.py` — the LOCAL, structural signoff recognizer (gates +
parse, no roster).  `_harvest_signature_contributors` refactored to call it
(RECOGNITION) then `initials_map.get` (RESOLUTION) — behavior-preserving, split
labeled.  Pinned by `tests/unit/test_signoff_recognition.py`.  This is the ONE
function both the harvest (now) and the producers (next) use — "do the same here" is
the same code, so the candidate set is provably identical when it relocates.

LIVENESS CORRECTED + CONTRIBUTOR HALF DELETED (2026-07-23, repo-wide grep — the
earlier "BOTH RE-SCAN FUNCTIONS ARE DEAD" claim was HALF-wrong; its grep was scoped
to `src/` and the pipeline's phase drivers live in `tools/pipeline/`):

  * **Contributor half: DEAD, now DELETED.**  `_harvest_signature_contributors` had
    zero callers anywhere (src/, tools/, tests/); `recognize_signoff_initials`,
    `_SIGNATURE_RE`, `_SIG_MARKER_RE` served only it.  All four deleted from
    `extract_contributors.py` + `tests/unit/test_signoff_recognition.py` removed
    (brick 1 reverted).  Suite 472 green (478 − the 6 signoff tests, exactly).
    The user's account stands for THIS half: the body-signoff harvest was attempted
    and rejected as too error-prone; the live binding is roster/index consensus
    (23fbea4, 72c14a4).  `_normalize_initials` STAYS — many live callers
    (vol29_linker, author_links, resolver, build_contributor_table, 6b4).
  * **Xref half: LIVE — not deletable.**  `_wrap_resolved_xrefs_in_body` (the fn the
    doc called `_wrap_body_xrefs`) runs on EVERY article in production:
    `tools/pipeline/resolve_xrefs_post.py:74` (Phase 6b5) → `_link_xrefs_in_body`
    (article_json.py:544) → `_wrap_resolved_xrefs_in_body` (line 627).  Its helpers
    are live through the same chain: `_looks_bibliographic` / `_protected_ranges` /
    `_clean_surface_for_matching` (body_postprocess.py), and `extract_xrefs`'s
    `_QV_PATTERN` / `_extract_qv_target` / `_PAREN_SEE_*` via `_xrefs_from_body`
    (6b5 line 61) — which also feeds the xref PANEL.  Nothing on that list is dead.
  * So J7's xref half REVERTS to the original analysis: a live double re-scan
    (`extract_xrefs` finds the q.v./see sites; `_wrap_resolved_xrefs_in_body`
    re-finds them with heuristic gates) to be RELOCATED per the target end state —
    producers emit `«QV:term»` at the site, the late pass reads markers and only
    resolves.  It stays on the inventory as a relocation, sequenced AFTER J3–J5
    (it is the hardest item: coupled to the panel + the 6b5 bake order).
  * The three-scope design + the regex discriminator (below) STAY, and now have
    live instances again.  LESSON, twice paid: grep the WHOLE repo for callers —
    the pipeline's entry points are in `tools/pipeline/`, not `src/`.

--- original SIG plan, retained for reference; it targets DEAD code, do not build it ---

STALE-PREMISE CORRECTION (2026-07-23, found right after brick 1): the SIG plan
below was built on `_harvest_signature_contributors`, but that function is UNCALLED
— `recognize_signoff_initials` / `initials_map` / the harvest are referenced ONLY
inside `extract_contributors.py`, nowhere else in `src/`.  The live signoff-binding
was folded into corpus-export (commit 23fbea4 "fold contributor harvest + linking
into corpus-export"; 72c14a4 "one phase builds the roster, binds, and names").
So brick 1's `recognize_signoff_initials` is a valid reusable recognizer, but the
harvest it was lifted from is dead.  BEFORE the SIG slice, FIND THE LIVE PATH in
corpus-export / the roster phase — the recognizer must land THERE, not in the dead
harvest.  (Do NOT theorize the plan onto a function's name again — grep the caller.)

NEXT SLICE — coupled, land together (retarget onto the LIVE path first):
  1. `_process_contributor_footer` emits `«SIG:name|initials»` (it already parses both)
     instead of prose `(initials)`.
  2. body producer calls `recognize_signoff_initials` on bare `(…)` in its run → `«SIG?:initials»`.
  3. inline render decodes `«SIG…»` → the same visible float-right signoff.
  4. harvest reads `«SIG»` off the marker stream; `_SIGNATURE_RE` + whole-body scan DELETE.
Verify: EQUIVALENCE first (producer `«SIG»` candidate set == old re-scan set on real
bodies — proves the logic with NO rebuild), THEN rebuild confirms attribution counts
hold ([[feedback_contributor_zero_false_positives]]).  After this, q.v. is the twin
(body producer emits `«QV:term»` via `_extract_qv_target`; late pass resolves).

## Current state (2026-07-23)

* **J7 audit CLOSED**: contributor re-scan chain deleted (dead); xref re-scan is
  LIVE via 6b5 and reclassified as a relocation, sequenced after J3–J5.
* **J3 + J4 + J5 DONE** — all three misplaced transforms are OUT of preprocess:
  `<bdo>`/`<small>`/`<big>` are walker-lifted TAG-IMPLIED stylers; the
  param-default decode lives in `fold_cell_attrs` (attr context) + a
  `PARAM_DEFAULT` element (prose context).  `_JUNK` ledger down to
  {close_unclosed_attr_quotes} — J2 is the only chain junk left; then J1
  (inside `strip_noinclude_blocks`), J6 (`_contain`), J8 (owner's call), and
  the J7 xref relocation.
* **Verified** by the raw-page walk-equivalence harness: old chain (deleted
  passes replicated verbatim) vs new, `corrections+quote-runs → clean → walk`,
  over the union of ALL affected raw pages (179) — byte-identical everywhere
  except the 2 front-matter pages no preprocess consumer can reach.  473 green.
* Two real fixes shipped alongside: the bounder/peeler close-tag mismatch
  (stray «/SPAN» on junk-attred closers, SLOVENES) and the prose
  `{{{…|…}}}` classifier crash → faithful PARAM_DEFAULT element.
* **J6 RESOLVED — `_contain` acquitted** (browser-verified: the escape is real
  and visible; `_contain` is the minimal balancer its own fallback specified;
  see the J6 entry).  No code change.
* **J1 DONE — noinclude table-marker rescue DELETED** (see the J1 entry: the
  guarded bug died with the old architecture; the rescue itself was silently
  dropping LIBRARIES ws 573/584 from production and chopping cross-page
  tables).  83-article A/B: zero loss, 473 green.  The rebuild will RECOVER
  the two swallowed LIBRARIES pages — verify in the rebuild diff.
* NEXT: J2 (`close_unclosed_attr_quotes`) — the last chain-ledger sweeper.
* `source_cleanup.py` reverted to the plain strip; `_contain` restored to working;
  464 tests pass.  The `context_sensitive_is_producer` memory loophole is closed.
* `data/derived` holds the CLEAN rebuild (source_cleanup reverted): 37226 articles,
  0 lost/new vs baseline, 131 render-changed (127 with a session-change signature,
  4 pure `_contain` tag-balancing).  NOT shipped, not to be shipped until this
  campaign is complete.
* Nothing deployed.  britannica11.org unchanged.

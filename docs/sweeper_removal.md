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

**J2. `close_unclosed_attr_quotes`** — ✅ **DONE 2026-07-23: DELETED; the
tolerance moved to the attr READERS.**
  * **The guarded consumer is gone** (the figtable DOMParser died in the
    render collapse), but naive deletion failed the A/B: 9 pages CRASHED
    (`_SPAN_TITLE_OPEN_RE`'s quoted value `[^"]*` ran past the tag's `>` into
    the NEXT span's quote — walker matched the full text, classifier
    re-matched the bounded raw, disagreement → raise; CARMAGNOLE vol5 p368),
    title glosses dropped, proofreading furniture leaked as styled spans, and
    `_KV_RE`'s bare-token fallback tore multi-declaration values
    (`position: relative` → `position:;`).
  * **The principle, owned by the readers**: an attribute value can never cross
    its own tag's `>`, so an unterminated quote ends at the tag close — the
    exact semantics the sweeper's inserted quote gave.  Two one-char-class
    edits: `_KV_RE` value `"([^"]*)"?` (every cell/row/table/styled-wrapper
    attr slot) and `_SPAN_TITLE_OPEN_RE` value `"([^">]*)"?` (title spans).
  * **A/B over all 148 affected pages** (repair vs no-repair+tolerance):
    0 crashes, 126 byte-identical, and all 22 diffs are the repair's OWN junk
    disappearing — it had been INSERTING quote characters into visible OCR
    prose (`>` → `">` in vol 25/27/29 math/index scannos) and even minting a
    visible word (`</poem` → `</poem">` leaked the token "poem", vol29 p971).
    Equal or strictly better everywhere; zero content loss.
  * Pinned by `tests/unit/test_attr_quote_tolerance.py` (the ABBEY Fig. 10
    attr shape, the torn multi-declaration value, the CARMAGNOLE crash).

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

SUPERSEDED (2026-07-24, designed with the user) — the plan above is refined on
two points:

1. **No new tags.**  A q.v./see reference is the same ELEMENT as a link; only
   its resolution POLICY differs, and kind must survive (the 2026-07-20 lesson:
   collapsing kinds into bare «LN» caused the JOHN VENN→McADAM class).  Kind is
   an ATTRIBUTE: `«LN[qv]:…»` / `«LN[see]:…»`, the `«MATH[fs=N]` pattern.  Every
   consumer that knows «LN» keeps working after ONE grammar widening (the
   optional `[kind]` slot) — no new marker contract for render/EPUB/markdown/
   panel/audits.  «AL» stays as-is for now (it already is this idea).
2. **The producer stamps a TOTAL WINDOW; the RESOLVER picks the extent** (user's
   keystone call: extent selection IS disambiguation → it belongs in the ONE
   picker, fill-dumb-fish-smart).  The site token (`(q.v.)`, `See`, `cf.`) is
   structural and crisp; "where does the title end" is a guess ONLY without the
   title index — against the index it is a lookup ("which suffix/prefix of this
   window IS an EB title": no title `ALCHEMY AS GEBER`; `GEBER` exists).  So:
     * producer: find token, stamp `«LN[qv]:window|window-verbatim«/LN»` (dumb,
       total — the window is the plain-prose run back/forward to the clause
       boundary; it never contains element placeholders by construction, only
       inline «B»/«I» marks, which resolution already strips);
     * bake (6b5): resolver returns (extent, target) together, TIER-MAJOR over
       window cuts (an exact match on a short cut beats a loose match on a long
       one — mirrors tight-before-loose); the chosen words become the link
       display, the unchosen prefix returns to prose, an unresolved marker
       strips to its verbatim display (= original text restored, provisional
       stamps are free);
     * adjacency (`«/LN» (q.v.)`): NO window stamp — the bake does a one-token
       peek at the marker's own boundary and UPGRADES the preceding link's kind
       to qv.  Marker-stream reading, no prose re-scan, no gates.
   `_extract_qv_target` / `_TARGET_TAIL` / the stop-word armor DISSOLVE into
   the resolver's extent-pick; they do not move to the producer.
   What then deletes: `_wrap_resolved_xrefs_in_body`, `_looks_bibliographic`,
   `_protected_ranges`, `_clean_surface_for_matching`, the extractor's prose
   patterns, the wrap-last bake choreography.
   Slices, each gated on the `xref_resolution.jsonl` A/B (candidate set +
   resolution outcome vs `.xref_consolidation_baseline/`):
     0. «LN» grammar widening everywhere — ✅ **DONE 2026-07-24.**  The
        `[kind]` slot (`(?:\[[a-z_]*\])?`) is tolerated at every pre-bake «LN»
        parse site: `markers_to_text`, `body_to_markdown`, `link_resolver`'s
        display strip, `render/inline._LN_OPEN_RE`, the 6b5 2-part bake +
        `_LN_DISPLAY_RE` + the already-linked check, `_protected_ranges`, the
        extractor's five patterns, `index.html`'s JS strip.  KIND DIES AT BAKE
        (6b5 writes the plain 3-part form or strips), so post-bake bodies never
        carry it and downstream consumers (downloads, search, resolved-form
        snapshot normalizers, leak grammars — which correctly FLAG a surviving
        «LN[ as a leak) need nothing.  Byte-identical by construction: zero
        `«LN[` in the 37k-article corpus (grep-proven).  Pinned by
        `tests/unit/test_ln_kind_grammar.py` (both forms through every
        consumer); 482 green.
     1. q.v. (window stamp + resolver extent-pick) — ✅ **BUILT 2026-07-24,
        A/B'd on all 74 q.v.-bearing articles (89 sites)**; details below.
     2. see/cf family — ✅ **BUILT 2026-07-24, A/B'd on 40 sampled articles**;
        details below;
     3. delete the dead extraction/wrap layer; panel reads markers.
        (`_wrap_resolved_xrefs_in_body` is now a NO-OP for every type: qv
        records no longer exist and a resolved see's surface IS its stamped
        marker, which the already-linked check skips — deletion is mechanical.)

SLICE 2 (2026-07-24): `_stamp_see_windows` (runs after the q.v. stamp) —
cue `[Ss]ee( also)?` / `[Cc]f.` / `[Cc]ompare` (+ optional "the article on"
lead), FORWARD clause-bounded window, TWO lexical gates replacing the whole
old armory: capital-led window (the verb "see" points at lowercase clauses)
and segment-split on `,`/` and ` (each capital-led segment its own stamp).
«I» as a boundary char = the `_is_bibliographic` gate FOR FREE (cited works
are italicized → empty window → no stamp).  Kind `[see]`/`[see_also]` routes
`resolve_see(window=True)`: all contiguous SPANS (a see target sits at either
end), a PARTIAL span needs ≥2 content words (binding JAMES out of "Sir James
Stephen" is the given-name junk class), same minimal-span/coverage pick, self
stays TERMINAL.  DELETED: `_PAREN_SEE_*`, `_SEE_*` (all six), `_CF_PATTERN`,
`_COMPARE_PATTERN`, `_TARGET_TAIL`, `_is_bibliographic`,
`_clean_paren_see_target`, `_strip_markers`, `_MARKER_PLACEHOLDER`.

SLICE 2b (2026-07-24, user-approved): **tight multi-word binds without topic
agreement.**  The headroom map over the 7,701 abstained sees: 2,500 no
candidates (scripture/non-EB, correctly dead) · 4,019 not substantial
(bibliographic surnames, correctly dead) · 1,056 topic-disjoint — of which
205 were TIGHT MULTI-WORD (exact/alt/fold on ≥2 content words): full personal
names folding onto their inverted titles (JEAN FROISSART → FROISSART, JEAN;
ROBERT BURNS; WASHINGTON IRVING), abstained only because the coarse vol-29
topic map didn't intersect (targets often uncategorized).  For that class the
name match IS the guard the topic gate stood in for → `_see_pass` binds it
topic-free (self-check + ambiguity-fishing kept); the uncategorized-SOURCE
early-abort dropped too.  Measured: **+223 new binds** over the abstained
rows (uniformly full-name gold on inspection); previously-resolved 563:
**525 unchanged · 1 shifted (a pipe-corrupted target) · 37 dropped — all
junk** ("§ 5", "PLATE I. FIG. 62", "AS TO THE LATTER" bound to random
articles).  The 723 single-word exacts (GIBBON good / LIFE junk) stay
abstained — that class needs the banked fisher-cosine backstop, its own
probe.  485 green.

**STALE-BASELINE CORRECTION** ([[feedback_audit_fresh_baseline]], violated
then caught): the first see A/B diffed against
`.xref_consolidation_baseline/xref_resolution.baseline.jsonl` — the
PRE-consolidation cascade snapshot (3,931 resolved sees, the junk world the
2026-07-19 rework already dropped) — and read 52 "losses" that were the junk
staying dead.  The honest reference is the last rebuild's OWN
`data/derived/xref_resolution.jsonl` (525 see + 38 see_also resolved).  The
q.v. adjudication is unaffected (qv rows identical in both files).

Against the honest reference (40 sampled sources, 58 resolved sees):
**54 recovered · 2 real losses · 2 junk losses that are WINS** (production had
bound the anaphor "AS TO THE LATTER", and "see Aubin" — a manuscript copyist
— to AUBIN the French town) · **4 good new binds** (UTE, ESKIMO, IODINE, and
"SALICYLIC ACID RESPECTIVELY" span-cut to SALICYLIC ACID) · 1 junk new bind
(DIEGO DE → GONDOMAR, particle counted as content — refine later).  Known
residual class: `(See «LN:Geometry», «SC»Analytical«SC».)` — a cue followed
by an existing link + small-caps qualifier never opens a window (the old path
assembled GEOMETRY, ANALYTICAL); marker-stream adjacency work if the rebuild
diff shows the class matters.  13 transform snapshots rebaselined (adjudicated
first: unstamping the new output reproduced every old baseline byte-for-byte —
60 stamps, nothing else).  485 green.

SLICE 1 (2026-07-24): `_produce_body` stamps `«LN[w]:window|window«/LN»` at
`(q.v.)` sites (dumb: literal token + clause-bounded span; a site directly
after a link gets no stamp — boundary chars make the window empty).  The
extractor reads `[w]` off the marker (windows BYPASS `_is_plausible_target` —
junk windows are filtered by the index, not extraction heuristics);
`_QV_PATTERN` / `_extract_qv_target` / `_QV_LINK_PATTERN` / `_SENTENCE_STARTERS`
are DELETED.  `resolve_xref(window=True)` runs tier-major suffix cuts; the bake
splits the display at the bound cut and an unresolved window strips WHOLE (no
WS fallback — the window is our guess, not the author's page name).
The extent-pick that survived adjudication (three iterations, each falsified
by the 89-site table):
  * per candidate, the MINIMAL binding cut (subset binds at every longer cut
    — only the shortest is informative);
  * candidate choice by WINDOW COVERAGE of the bound title (MACDONNELL,
    SORLEY BOY covers 3 window words, ANTRIM, RANDAL MACDONNELL covers 1),
    tie-broken toward the cut NEAREST THE CUE (kills the PERIOD/CAUCASUS/
    POTOMAC far-end junk class);
  * a self-naming cut SKIPS, never terminal (SICILY's own name mid-window
    must not veto "patrician (q.v.)" beside it) — and this FIXED a baseline
    bug: SEMPILL's "of Beltrees (q.v.)" had been linked to ITSELF (BELTREES
    has no article; the old alias bound the source article);
  * `_grow_cut` extends the display leftward while each word belongs to the
    bound title ("BOY MACDONNELL" → "SORLEY BOY MACDONNELL"; "OF ALCIBIADES"
    never grows).
Result on the 89 sites: **85 resolved / 4 correct abstentions**; beats
baseline on specific titles (SEVEN YEARS' WAR over WAR, SEVEN DAYS' BATTLE
over BATTLE, WATERLOO CAMPAIGN over CAMPAIGN); large coverage gain (the old
extractor had found only ~3 of SWITZERLAND's 23 sites).  Residual: ~3
wrong-person homonym binds (MASON, ROUSSEAU, the DE LUC brothers) — the
pre-existing person-fisher residual class, unchanged in kind.  Baked-body
verified: prefix returns to prose, link wraps the cut with original casing,
zero residual «LN[w] post-bake.  482 green.
NOTE: `_wrap_resolved_xrefs_in_body`'s qv leg is now dead (no qv records
exist); the see leg still runs until slice 2.  Corpus-wide proof rides the
campaign rebuild's xref_resolution diff (expect: qv rows gone, ~85+ window
links appearing as type link, junk qv binds dropped).

SIMPLIFIED AGAIN (2026-07-24, user): **no `[qv]` kind and no adjacency logic.**
Measured on all 108 corpus q.v. records: qv-policy vs link-policy resolve
identically on 104; the 4 divergences are the qv LOOSE ladder binding
given-name junk (SOLOMON GESNER→SOLOMON, JOSEPH BONAPARTE→JOSEPH, CONRAD
FERDINAND MEYER→CONRAD, JOSEPH GIANVILL→JOSEPH) — the exact 2026-07-20
failure class, surviving inside the qv tier; link policy returns None on all
four and the baseline's correct binds come from machinery link policy also has.
So: the producer stamps `«LN[w]:window|window«/LN»` at `(q.v.)` sites (only
where not already linked — a link followed by `(q.v.)` is just a link);
`[see]` carries the abstain-default that killed 3,618 junk links.  Accepted
side effect: ~108 panel/xref_edges records re-type qv→link.

UNIFORM CUTTING FALSIFIED (2026-07-24, probe before build): running the cut
ladder over ALL link targets ("a tight target degenerates to itself — one code
path") changed 892 of 13,657 baseline resolutions, heavily junk: SIXTUS IV cut
to 'IV'; JESUS OF NAZARETH → 'OF NAZARETH' → NAZARETH (baseline: JESUS
CHRIST); LIFE OF CHRIST → 'OF CHRIST'; ROLLO AT WORK → WORK; person citations
cut to bare surnames past the first-given guards.  THE LINE: a wikilink's
target is an ASSERTED extent (the author committed to those words — never
cut); a stamped window's extent is UNASSERTED (cutting is the point).  That
one bit rides the marker as `[w]` — NOT a policy kind (stamped windows resolve
under the same trusted link policy; the no-[qv] simplification stands).
resolve_xref grew `window=` (cuts gated on it; default False = byte-identical
to pre-change, 482 green) and returns the bound cut for the bake's display
split (`Xref.matched_cut`).
Marker grammar so far: plain «LN» (asserted extent, link policy) ·
«LN[w]» (window extent, link policy) · «LN[see]» (window extent, abstain
policy — will cut PREFIXES, its window runs forward).
Fuzzy-tier audit (the "should baked LNs be forced to choose" question): only
125 of 28k resolved links depend on the loose (fuzzy) tier at all, and the
sample is uniformly the GOOD class (GOSPELS→GOSPEL, AELFRIC→ÆLFRIC,
plural/diacritic variants, all matching baseline) — always-pick stays.

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
  tables).  83-article A/B: zero loss.  The rebuild will RECOVER
  the two swallowed LIBRARIES pages — verify in the rebuild diff.
* **J2 DONE — `close_unclosed_attr_quotes` DELETED**; unterminated-quote
  tolerance owned by the attr readers (`_KV_RE`, `_SPAN_TITLE_OPEN_RE`).
  148-page A/B equal-or-better everywhere; 476 green.
* **THE `_JUNK` LEDGER IS EMPTY.**  The pre-walker chain is now VETTED +
  `_decode_entities` (UNDECIDED — J8, owner's call).  Remaining campaign work:
  J7 xref relocation (`«QV:term»`), J8 decision, then the FINAL CLEAN REBUILD
  (corpus-wide proof; expect GAINS: LIBRARIES pages recovered, continuous
  tables, OCR prose without injected quotes).
* `source_cleanup.py` reverted to the plain strip; `_contain` restored to working;
  464 tests pass.  The `context_sensitive_is_producer` memory loophole is closed.
* `data/derived` holds the CLEAN rebuild (source_cleanup reverted): 37226 articles,
  0 lost/new vs baseline, 131 render-changed (127 with a session-change signature,
  4 pure `_contain` tag-balancing).  NOT shipped, not to be shipped until this
  campaign is complete.
* Nothing deployed.  britannica11.org unchanged.

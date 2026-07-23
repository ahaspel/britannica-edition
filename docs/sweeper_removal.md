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

**J1. `{|`/`|}` rescue** — `pipeline/stages/source_cleanup.py`
(`_NOINCLUDE_KEEP_OPENER_RE`, `_NOINCLUDE_KEEP_CLOSER_RE`, the kept-token branch of
`_replace_noinclude`).
Preserves wikitable delimiters found inside `<noinclude>`.  Upstream bug (named in
its own comment): the balanced-table extractor pairs a `{|` on one page with a `|}`
many pages later, swallowing all intervening prose — ate Climate / Fauna /
Population from UNITED STATES, THE.  `<noinclude>` is NOT transcluded; MediaWiki
drops both halves and the table is one continuous span in mainspace, so the correct
end state drops them too.
Method: fix the extractor's cross-page pairing → delete the rescue → prove by diff.

**J2. `close_unclosed_attr_quotes`** — `pipeline/stages/source_cleanup.py`.
Repairs a tag with an odd number of `"` by inserting one before the `>`.  Upstream
bug: the missing quote makes the figtable DOMParser swallow the rest of the cell
(ABBEY Fig. 10).  363 corpus-wide — a class, not a typo list.
Method: route the class through a producer (or `data/corrections.json` if instances
are individually addressable) → delete the repair → diff.

### Misplaced transforms — construct conversion in preprocess (relocate to producers)

**J3. `_normalize_bdo`** — `pipeline/stages/preprocess.py` (`_BDO_OPEN`, `_BDO_CLOSE`).
`<bdo dir=X>` → `<span style="unicode-bidi:bidi-override;direction:X">`.

**J4. `_normalize_size_tags`** — `pipeline/stages/preprocess.py`
(`_SMALL_OPEN`, `_BIG_OPEN`, `_SIZE_TAG_CLOSE`).
`<small>`/`<big>` → `<span style="font-size:smaller|larger">`.

**J5. `_resolve_param_defaults`** — `pipeline/stages/preprocess.py` (`_PARAM_DEFAULT`).
`{{{name|default}}}` → `default`.

All three are context-free AND conversions, so preprocess was always the wrong home.
The walker already has a styled-span path; these belong on it (or a producer).
Method: move recognition to the walker/producer → assert the diff is empty or
confined to that construct's own articles.

### Render-layer

**J6. `_contain`** — `render/article.py` (`_contain`, `_WRAP_TAG_RE`; called in
`_render_body`).
A regex reimplementation of HTML tag-balancing — a fork of `render/normalize.py`
(`normalize_html`, html5lib).  Introduced THIS session to contain the unbalanced
HTML that the new `STYLE_OPEN`/`WRAP_OPEN` marks emit for unpaired source spans, so
a stray `</div>` can't escape the `body-text`/`card` wrapper.
NOT replaceable by `normalize_html`: verified it re-serializes everything
(`&middot;`→`·`), changing all 37k articles' bytes.  Scope of the actual need is
only ~30 articles (those with genuinely unpaired source spans).
OPEN QUESTION to resolve first: is the escape a real, visible problem?  It has only
been shown via html5lib `parseFragment`, not a real browser and not against the
actual `body-text` CSS.  If it is cosmetic-only, delete `_contain` with no
replacement.  If real, build a minimal byte-preserving div/span balancer (NOT a
regex fork, NOT full normalize).

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

* **J1** — pin UNITED STATES, THE's Climate / Fauna / Population section word
  content; after extractor-fix + rescue-deletion its `words LOST` must be 0.
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

NEXT SLICE — coupled, land together:
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

* `source_cleanup.py` reverted to the plain strip; `_contain` restored to working;
  464 tests pass.  The `context_sensitive_is_producer` memory loophole is closed.
* `data/derived` holds the CLEAN rebuild (source_cleanup reverted): 37226 articles,
  0 lost/new vs baseline, 131 render-changed (127 with a session-change signature,
  4 pure `_contain` tag-balancing).  NOT shipped, not to be shipped until this
  campaign is complete.
* Nothing deployed.  britannica11.org unchanged.

# Article-xref strategy — resolve via the topic resolver's fill/fish (design of record)

Scope: **article cross-references only** — in-prose references from one EB1911
article to another. All **EB→EB**: the resolver's target space is the EB corpus
(~37k articles), every `resolved_to` is a corpus filename, and wiki-namespace /
interwiki / `/`-path text links are stripped upstream. Revised 2026-07-19 after a
full-corpus audit of the freshly-rebuilt `data/derived/xref_resolution.jsonl`
(38,817 records).

## The decision

**Resolve article xrefs with the same fill/fish machinery we built for topic
links** (`topic_resolver_redesign.md`) — not a separate matcher. An article xref
is "name → EB article," exactly like a topic. The **recall half transfers
wholesale**; only the disambiguation *signal* differs.

> This supersedes the earlier framing in this doc that "the topic machinery does
> not transfer." That was an over-correction — true only of the *bucket*, which is
> one rung of the fisher. The fill cascade is generic name→article matching, and
> it is exactly what the xref misses need. The xref path currently runs its own
> weaker `find_fuzzy_match`; that fork is the bug, and un-forking it is the
> 7-forks→one consolidation arc.

## Three concerns, one recall substrate

Topics / article-xrefs / contributors are still three separate concerns (different
inputs, precision bars, disambiguation signals) — but they **share the recall
substrate**. The precise line:

- **Shared:** `fill(name) → bag` — word-set (tight) → fold / subset / first-word
  (liberal). Pure name→article matching. No "separate inversion" — inversion,
  folding, subset are the filler's internals, already built.
- **Differs — the fish's disambiguation *signal*:** topics fish against the
  reader's-guide **bucket** (a clean attribute); xrefs against the **surrounding
  prose** (+ the given name already in the reference); contributors against the
  **master index** (a different world — attribution, not name-matching).
- **Differs — the abstain policy, a BINARY (not a gradient):** one `trusted` bit
  per xref. **Trusted** `{link, q.v.}` (known-real) → **always pick** — the topic
  posture; a weak fish still picks, because the link *is* real. **Untrusted**
  `{cf, See, paren}` → the fisher **abstains below a confidence gate** (the topic
  loosening's cosine catch-gate, here used to *drop*, not widen). **Never
  always-pick the untrusted tier** — pointing the raw `see` cue at the always-pick
  posture manufactures a link from every scrap of prose (`see the table above` →
  a bogus target). It is the `aggressive` knob, already a boolean.

## What the audit found (measured, 38,817 records)

**Two tiers, not three.** `{link, q.v.}` are trustworthy cross-references; the
rest (`cf.`, `See`/`see`, paren-`(See)`) is dominated by citations and
bibliography.

| tier | count | %all | resolves | **est. precision of resolved** |
|---|--:|--:|--:|--:|
| link (explicit «LN») | 30,444 | 78% | 94% | **~95%** |
| q.v. | 108 | 0.3% | 97% | **~75%** |
| cf. | 1,361 | 3.5% | 48% | ~30% (mostly citations) |
| See / see | 6,690 | 17% | ~50% | ~35–55% (bibliographic) |
| paren `(See)` | 134 | 0.3% | 51% | ~20% (broken reads) |

**Resolution rate is not precision — the central correction.** "Resolved" only
means the target hit *some* title. cf. is a citation marker (`cf. Matt`,
`cf. Aesch. Suppl.`) — demote it out of any trusted tier. The See bulk is
bibliographic reading-lists (`See Smith, Assyrian Discoveries`). Hand-judging a
135-record sample gave the precision column above; the resolution-rate column
badly overstates the trustworthy fraction.

**Two failure modes hid inside "resolved":**
1. **Homonym wrong-article** — a bare name with no context resolves to the wrong
   same-named article: `Rousseau (q.v.)` → the *painter*; `see Routh` → the
   *mathematician*, not the patristic scholar; `see Duval` → the *highwayman*.
   This is exactly what the **prose-fed fisher** fixes.
2. **Not-a-reference false positives** — a citation/bibliographic surname collides
   with a title: `See Report` → REPORT, `cf. Acts` → ACT, `See Werther` → the
   article WERTHER. This is what a **structural bibliographic filter** kills.

## The main problem: the known-real misses

The noisy "rest" mostly self-filters (it fails to resolve, which is *correct*).
The valuable target is the tier we KNOW is real — the **1,865 declared `«LN»`
links (6% of explicit) that don't resolve.** The author bracketed a link; we
failed to match it. Characterized against the 37k-title index:

- **Forward personal names — the big pool.** `Richard Francis Burton` is filed as
  `BURTON, SIR RICHARD FRANCIS`. The topic **fill resolves these on recall alone**
  (subset: {richard, francis, burton} ⊆ {burton, sir, richard, francis}). Today's
  xref matcher misses them (its inversion is gated too tightly). **Single biggest
  win, and it comes free the moment fill is shared.**
- **Punctuation/diacritic gaps (~52, trivial).** `SHIP-BUILDING`↔SHIPBUILDING,
  `GIANT'S KETTLE`, `INCOME-TAX`, `ŌKUMA SHIGENOBU`, `RAWAL PINDI`. The article
  exists; the matcher just doesn't fold hyphens / apostrophes / macrons / spaces.
- **Wikisource text/file links — filter, don't resolve.** `BIBLE (KING JAMES)/…`,
  `COMMENTARIES ON THE GALLIC WAR/BOOK 8`, `MOLL FLANDERS`, `:FILE:…`. Never EB
  xrefs; filtering `/`-path and `:File:` targets cleans the denominator.
- **Genuine red-links — residue.** `ANTONÍN DVOŘÁK`, `FUJIWARA NO TEIKA`, `KIPPS`:
  alive-in-1911 or too minor for EB. Correctly unresolved, nothing to fix.

## The design: reuse fill, reuse fish (prose-keyed)

`fill(target) → bag` (identical) → `fish(bag, prose)` (one rung swapped).

- **Shared `fill`.** Lift the ladder out of `build_resolver`
  (`populate_classified_toc.py:356–408`) + its title indexes (`209–220`) into a
  `NameResolver`. Logic unchanged; both the topic and xref paths call it. This is
  the whole recovery engine for the forward-names and punctuation gaps.
- **Shared `fish`.** `Fisher.fish(name, cands, context, want_kind)`
  (`topic_fisher.py:84`) is already context-parameterized. The one generalization:
  the embedding query vector comes from `context` — `_path_vec(bucket)` for topics,
  `embed(prose)` for xrefs (the rung at `128–129`). geo/field (step 0) and kind
  (step 1) are bucket-only → skipped for xrefs (`want_kind=None`, no path). Most
  declared misses never reach the fisher: fill returns a unique bag.
- **Xref call site.** `article_json.py:471` (`resolve_one`). Replace `resolve_one`
  / `find_fuzzy_match` / `disambiguate_among` (`xrefs/resolver.py`, `scoring.py`)
  with the shared `fill`+`fish`. Drop the topic-only gates (`_kind_ok`,
  `_BROADEN_KINDS`).
- **The one genuinely new piece.** The extractor stores `surface`, not context.
  Capture a prose window around each reference so the fisher has something to
  embed.

## Extraction quality (refined by the audit)

The extractor owns *reading* (faithful) + *tagging* the cue; the resolver owns
*reality-judgment*. Measured priorities, highest-value first:

1. **Capture the prose context window** — prerequisite for prose-fishing (new).
2. **Bibliographic/citation filter, applied to ALL cues** (today only
   paren-`See`). Kills failure mode 2 across cf./See; a structural reject the
   extractor should own, and the biggest false-positive cut.
3. **Filter Wikisource text/file targets** (`/`-path, `:File:`) — never EB xrefs.
4. **paren-`(See)` reading is broken** — section numbers, figures, and phrases get
   extracted as targets (`ss. 52-66` → LANDLORD AND TENANT). A real read fix.
5. **q.v. is handled** (`_QV_PATTERN` + `_extract_qv_target`, backward walk);
   truncation is minor (measured 4–10%), *not* the priority an earlier draft
   implied.
6. **Preserve the cue tier** — split `cf`/all-caps out of the collapsed `see`
   label, now for the two-tier {trustworthy vs rest} split.

## Build plan (each step regression-gated)

1. **Extract `NameResolver` (fill)** from `build_resolver`; topic path calls it →
   prove byte-identical `classified_toc.json` (topic net: input→filename set-diff).
2. **Generalize `Fisher.fish` context** to `path | prose`; topic path still passes
   `path` → prove byte-identical.
3. **Extraction:** capture prose context + filter Wikisource/`:File:` targets +
   extend the bibliographic filter to all cues. Net = `xref_resolution.jsonl`
   before/after.
4. **Wire the xref path (6b4) to `fill`+`fish`** (replace `resolve_one` /
   `find_fuzzy_match`). Expect: the 1,865 declared misses drop sharply
   (forward-names + punctuation recovered); homonym wrong-arts fall (prose-fishing).
5. **Measure the win by PRECISION, not rate** — the hand-judged, human-calibrated
   per-tier sample (the topic playbook), focused on declared-link correctness +
   the correctness of the recovered misses.

## Regression net & invariants

- Gate on `xref_resolution.jsonl` before/after **and** the topic
  `classified_toc.json` set-diff — extracting fill must not move a single topic.
  No correct→wrong.
- **Measure by precision (hand-judged, calibrated), never resolution rate** — the
  whole reason the old table lied.
- Recall (fill) and precision (fish) never mix; **fill is one shared engine**, not
  a per-concern fork.
- The bucket does not exist for xrefs; the fisher's context is **prose** — same
  mechanism, different key. The bucket is the better signal; prose is the best
  available, and it only matters when the bag has homonyms.
- **One `trusted` bit drives the fisher — a binary, never a gradient.** Trusted
  `{link, q.v.}` → always-pick; untrusted `{cf, See, paren}` → abstain-gated (a
  weak fish drops). The extractor's bibliographic/Wikisource filter kills obvious
  junk up front; the abstain gate is the resolution-side backstop. Consolidation
  MUST NOT collapse this to always-pick, or the untrusted cues flood bogus links.
- The extractor reads faithfully + tags + filters *structural* non-references
  (bibliographic, Wikisource-path); the resolver judges reality.

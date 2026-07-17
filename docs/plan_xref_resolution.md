# Plan: Article-xref resolution — one kind-aware disambiguator

**Status:** design of record, 2026-07-16.  Part of the resolver-consolidation arc
([[project_resolver_consolidation]]).  Supersedes the bio-articles fold (#4),
which this session **descoped** — see below.

---

## What's settled (out of scope here)

- **The contributor problem is a different world.**  It is *attribution* — bind a
  contributor to the articles he *wrote* — resolved from signatures (footer
  initials `(J. M. M.)`), the vol-29 master Index of Contributors, and per-volume
  lists.  That machinery is `ContributorIndex` + the vol-29 linker + footer
  extraction, built and banked.  No title-matching, no fuzzy name→article, no kind
  evidence.  The contributor *bio link* (contributor → his own biography) is a
  lookup dominated by the explicit `«BIOLINK»` the source supplies (220 of them),
  zero-false-positive / conservative — also settled, and **not a resolution
  problem**.
  - The person-mode fold attempted this session was **reverted**: it imported the
    xref "pick over abstain" calibration into the zero-FP contributor domain and
    manufactured false positives (Colomb → his *brother* Philip Howard; Wallace →
    the wrong same-page Wallace).  `scoring.py` is back to un-forked.
  - Parked: the *current* live bio output carries ~14 stale false positives from
    the old aggressive matcher (Colomb → "LORD, JOHN", the KING-WILLIAM
    collapses).  A conservative pass drops them — separable, whenever wanted.

- **Topic resolution is settled** — the classified TOC resolves each bucket entry
  and disambiguates same-title collisions by the bucket's own kind via
  `pick_by_kind` / `lead_kind`.  Fixes **A1/A2** below make it (and the kind index
  it feeds) trustworthy.

---

## The remaining problem: article xrefs

Two kinds, with different evidence:

1. **Explicit source xrefs** carry a disambiguating parenthetical —
   `Zürich (city)`, `David (king of Judah)`, `Benzoin (ketone-alcohol)`,
   `Lexington (Massachusetts)`.  **Exact kind info, highest precision.**
2. **Bare xrefs** (`q.v.`, `cf.`) have no kind — a naked name.

### Sizing (2026-07-16, `xref_resolution.jsonl`, 30,444 `link` xrefs)

| set | count | note |
|---|---|---|
| explicit parenthetical hints | **~1,092** | mostly on the **target** side; the resolver reads only the display and strips the target parenthetical, so they're **discarded today** |
| — **load-bearing** (base collides under broadening) | **824** | *larger than the bare residue, and with exact kind* |
| bare **exact-title** collision residue | **~697** | genuine bare disambiguation need |
| no leading-token match (canonicalization pool) | **~5,534** | needs inversion/fold, **not** disambiguation |

The "49 hints" figure quoted mid-session was a counting bug (display-only) — see
the correction: hints live on the target half of the marker.

---

## Governing principle

**Per-*candidate* kind is universal evidence; per-*link* wanted-kind is a bias you
may apply only where it is *known*** — a structural topic bucket, or an explicit
parenthetical.  Infer a wanted-kind anywhere else and resolution gets *worse*.
Consequences:

- **Broaden the candidate set to leading-token matches (`ZÜRICH` → `ZÜRICH`,
  `ZÜRICH, LAKE OF`) ONLY when a kind is known.**  Safe with `(city)`; *harmful*
  when bare — a bare `David` broadens to 9 candidates (every `DAVID, <surname>`
  person) when it means the primary `DAVID`.
- **The kind is a hard constraint that rejects wrong-kind candidates, not a
  tiebreaker.**  The Zürich-lake bug: `pick_by_kind` abstained (no lake in the
  exact collision) and first-wins then accepted the *canton* — a kind mismatch —
  mis-tagging it `lake`.  The pollution was manufactured by a kind-blind fallback,
  not inherent to the topic.

---

## The design: one kind index → one `pick_by_kind` disambiguator

```
   topic buckets ─┐
                  ├─►  KIND INDEX  (filename → {kinds})  ─►  pick_by_kind  ─►  serves:
   lead_kind    ─┘        (person set generalized)              │              • topic resolution
                                                                │              • the 824 explicit hints
   parenthetical hint (either side) ─► wanted-kind ─────────────┘              • bare tail (salience, no kind)
```

### Work items

**A — two fixes that make the kind index trustworthy (small, foundational).**
✅ **DONE 2026-07-16** (rebuild-gated).  Regression net = robust per-bucket
filename-SET diff of `classified_toc` vs the pre-A1 baseline (target-keyed diffs
miss broadened picks that rewrite the target text).  Result: 9 buckets changed,
**all wins, 0 regressions**, resolved count unchanged (34 529); suite 419 green.
The set-diff caught three regression classes a weaker check would have shipped —
**(a)** blanket `s?` reads partitive plurals as kinds (`republic of 31 states` →
division), so A1 is restricted to the `one of the …Xs` is-a form; **(b)**
broadening a *person* query grabs the wrong same-surname person (`ADAMS, JOHN` →
`ADAMS, JOHN COUCH`); **(c)** broadening a *nature* query grabs a hyphenated
compound (`BIRD` → `BIRD-LOUSE`) and a *settlement* query a same-prefix impostor
(`NEVADA` → `NEVADA CITY`).  So A2 broadening is **allowlisted to physical
features only** (`_BROADEN_KINDS = {lake, river, mountain, island}` — the one
place the bucket wants a variant of the bare name, `ZÜRICH → ZÜRICH, LAKE OF`);
`lead_kind`'s "the Jura Mountains" plural is left unhandled (deferred, not a
regression — those were already wrong).

- **A1. `lead_kind` plural gap.**  `\bcanton\b` → `\bcantons?\b` (and towns / lakes
  / rivers / …).  The Zürich *canton* reads `None` today only because its lead is
  "one of the **cantons** of…".  Fixes it on its own merits (evidence, not luck).
- **A2. Broaden-on-abstain, kind-gated (topic resolver `resolve()`).**  When
  `pick_by_kind` abstains over the exact collision **and a kind is wanted** →
  broaden to whole-word leading-token candidates → retry `pick_by_kind`;
  `first-wins(exact)` only as the final fallback.  Reaches `ZÜRICH, LAKE OF` (never
  in the exact collision) and stops the lake entry polluting the canton.  **Never
  broaden when no kind** (the David-decoy).

**B — the kind index (generalize the person set).**  ✅ **DONE 2026-07-16.**
`tools/vol29/build_kind_index.py` → `data/derived/kind_index.json`
(`filename → [kinds]`), superseding `build_person_index` / `person_articles.json`
(the person set is now the `person`-category slice).  Kinds come from the topic
buckets (person + person-fields, division/town/city/lake/river/mountain/island,
ethnic, nature) **unioned with each article's own `lead_kind`** (which adds
person-roles: `Shelley → [person, poet]`, `Gladstone → [person, statesman]`).
On a **cross-category** disagreement **lead arbitrates** — a town mis-filed under
a Biographies bucket keeps only `[city, town]`, scrubbing the pollution
(`ABERDEEN`); where lead is silent the topic supplies the kind (atypical-lead
critic → `person`).  Coverage 25 667/36 691 (69%): person 13 751, place 10 326,
nature 1 095, ethnic 573; 200/203 bio targets carry a person kind.
**subject-domain** (article topic category) and **place-of** (containing region)
are deferred to **C** as its per-hint disambiguation inputs, read from the topic
tree at pick time rather than baked here.  Trustworthy because it rides A1/A2.

**C — collapse the disambiguation fork.**  Topics use `pick_by_kind` (sharp);
inline xrefs use `matches_disambiguator` (whole-opening word-grep, which mis-fires
because the canton says "the **capital** is Zürich").  Route inline-xref
disambiguation through the **same `pick_by_kind`**; feed the wanted-kind from the
**parenthetical on either marker side** (target *or* display).

**C-core ✅ DONE 2026-07-16** (the part unblocked before F, using each candidate's
*live* `lead_kind` at resolution time):
  - `disambiguation.hint_kind()` maps a parenthetical word into the `_LEAD_NOUNS`
    kind space (`(city)`→town, `(province)`→division, `(king of Judah)`→king,
    `(popes)`→pope, `(tribe)`→ethnic; `(South Carolina)`/`(Law)`→None).
  - `resolver._display_disambiguator` now scans **both marker sides** + the
    normalized target; `disambiguate_among` runs `pick_by_kind(hint_kind(...))`
    first, keeping `matches_disambiguator` as a **fallback** (retired once the
    kind index subsumes it, post-F).  Verified: Zürich `(city)` resolves from
    target *and* display; suite 419 green.  Reach: `hint_kind` acts on **41%**
    (436/1039) of the hints now — place-kinds + person-roles + ethnic/nature —
    the fallback covers more.

**C-full (rides F):** point the picker at the **kind index** (topic ∪ lead — adds
the atypical-lead persons live-`lead_kind` misses) and add the two axes the 603
deferred hints need — **subject-domain** (`Law`→ the candidate's topic category)
and **place-of** (`Greece`/`Massachusetts`→ containing region, the geography
tree) — both read from the post-export topic data.  Then retire
`matches_disambiguator`.

**D — salience tiebreak (the ~697 bare exact-collisions).**  ✅ **DONE
2026-07-16.**  `disambiguate_among` Rule 3 (the fallback when a collision has no
kind hint, or the hint didn't resolve) picked the dict-order first candidate —
arbitrary.  Now picks the most PROMINENT article — the **longest body** (the main
subject over a same-named stub) — order-independently and deterministically
(`max` keeps the first on a length tie, degrading to the old first-wins when
bodies match).  Bare `Zürich` → the city (body 24 791) over the canton (4 651).
Suite 419.  (In-degree / most-linked would be sharper but needs the resolved
xref graph — not available at resolution time; body length is the self-contained
proxy.)

**E — name canonicalization.**  ✅ **DONE 2026-07-16.**  `find_fuzzy_match`
strategy **10b** retries the name strategies in the diacritic-**folded** title
space, so:
  - a fold COMPOSES with inversion (`RENE DESCARTES` → `DESCARTES, RENÉ` — the
    two passes never chained before).  *Correct but small: 2 refs — the
    inversion+accent combo is rare because sources keep the accent.  My "biggest
    volume" framing was wrong.*
  - **invert-then-prefix**: a forward name → a UNIQUE `LAST, FIRST…` title keyed
    on surname + first given name, **gated on middle-name consistency** — every
    target middle (surname particles dropped) must match some matched given word
    (equal / initial / prefix / one edit), else abstain.  Resolves the fuller
    filed name (`Tycho Brahe → BRAHE, TYCHO`; `Charles Darwin → DARWIN, CHARLES
    ROBERT`; `Victor Hugo`; `von Harnack`; `de Rémusat`) but **never crosses to a
    same-first-name relative** (`John WILLIS Clark` abstains, not `CLARK, JOHN
    BATES`; the two Coleridges / Kembles / Thompsons).

Additive (10b fires only after strategies 1–10 fail).  **34** previously-
unresolved xrefs resolved (famous, high-traffic articles), **0 false positives**
(the 5 relative-collisions abstain); suite 419.  Deferred: nickname-first
(`Lew`→`Lewis`) and 2-edit spelling middles (`Eliot`/`Elliott`) abstain — safe
misses, not regressions.

**F — structural home (the bigger lift, stage last).**  All cross-corpus
resolution belongs in ONE post-export phase, because it needs the full article
index + the kind index + the topic classification.  Topics already run there and
the kind index is post-export, so **inline-xref resolution must migrate
post-export** to consume it (today it resolves at phase 3a and bakes targets at
export 4).  Follow the topic resolver's proven pattern: read the exported
articles → resolve → patch the article JSONs.  A–D already improve the
post-export topic surface immediately, so this can stage after them.

### Calibration (per surface — the `aggressive` knob is already wired)
- **Topic** — recall / aggressive; a finding tool, FPs cheap.
- **Inline xref** — precise fuzzy + **decisive pick** among genuine candidates
  (pick over abstain; never invent a match from OCR noise).  The kind constraint is
  decisive-when-unique; abstain only when genuinely ambiguous.
- **Contributor** — zero-FP (out of scope; different world).

### Regression net
Before/after resolution diff: `xref_resolution.jsonl` + `classified_toc.json`
(baseline in `data/derived/_baseline_resolver_arc/`).  Gate: **no correct →
wrong**; previously-unresolved → correct = win.  Kind-index changes verified on the
`ZÜRICH` / `ABERDEEN` / `ABBAS` probes (canton→division, lake→`ZÜRICH, LAKE OF`,
town→city).  Materializes only on a full rebuild + re-export ([[feedback_never_partial_rebuild]]).

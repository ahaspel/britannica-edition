# Topic-link resolver — redesign (design of record)

Resolves each vol-29 classified-TOC entry (a *topic*: a name in a category
bucket) to an article. Replaces the tangled single cascade in
`populate_classified_toc.py::build_resolver.resolve` (exact + by_base + alias +
kind gate + aggressive fuzzy, all bleeding into each other through fall-throughs).

## The reframe: two operations, not one cascade

Every topic is **fill the bag, then fish the bag.**

- **FILL (recall):** get the candidate article(s) *into* a bag. Cheap, broad, may
  over-include. A fat bag is good — it means the answer was caught.
- **FISH (precision):** pick the right article *from* the bag. Narrow, thorough;
  the bag is only ever 4-5 items, so we can afford real work here.

The two never mix. String/loosening heuristics do **recall only** and never
pick; the scoreboard does **precision only** and never searches. This is what
makes "an alias/loosening can never override a real match" **structural**: fish
runs only on what fill produced, and the exact path (stage 2) is tried first.

## Leverage

Every topic **is supposed to resolve** — the reader's guide only lists articles
EB actually has. So the question is never "is there a match?" but "*which* one?",
and in a collision the answer is (almost always) already in the bag.

## The stages

1. **Sections.** If the topic carries `§` or `#` it is a *section pointer* —
   resolve it as a section (`X § Y` → dedicated `{demonym} Y` article or a section
   anchor of X). Return the result **including unresolved**; a section ref never
   falls through into name-matching.

2. **Fill — exact word-set match.** Normal form = **uppercase + collapse
   whitespace, nothing else** (the inherited `normalize_xref_target` grab-bag —
   interwiki-strip, `#`→`:`, Æ-fold — buys exactly 1 topic and is xref baggage;
   drop it). Candidates = articles whose **title word-set equals** the topic's.
   - exactly 1 → **resolved** (~27k, near-zero false positives).
   - ≥2 → **collision** → fish (stage 3). The answer is in the bag.
   - 0 → **empty bag** → loosen (stage 4).

3. **Fish — the scoreboard.** The bucket is a **category**, matched by
   *membership*, not word-overlap. A cascade of rising cost, each rung validated:
   - **kind** (is-a): `lead_kind` (earliest is-a noun) + synonym map. Sharp and
     free, but *incomplete* — vocabulary gaps (`economist` unlisted) and silent on
     same-kind bags. Cross-kind only.
   - **embedding-cosine**: `cosine(embed(article lead), embed(bucket path))`,
     highest wins. Semantic membership — reads *aboutness*, so the river beats the
     department that merely mentions a river, and cosine's length-normalization
     kills the verbosity bias. **Proximity weighting**: the immediate parent
     discriminates far better than the top category, so weight the path by depth.
     `fastembed` (BAAI/bge-small-en-v1.5, ONNX, ~50 MB, no key, deterministic).
   - **LLM judge**: hand the 4-5 finalists + full path to an LLM. The arbiter for
     disagreements / thin cosine margins / kind abstentions. Build-time only.
   - **Policy:** where kind and embedding *agree*, trust it (two orthogonal
     signals). Otherwise the LLM decides. **Always picks** — the answer is in the
     bag; a dead tie falls back to salience (prominence).

4. **Loosen — empty bags.** The only pure-**recall** problem left; precision is
   already solved by stage 3. Widen the net, tightest first, each a recall-only
   loosening that never picks:
   1. **fold diacritics** at tokenization (`LÉON`=`LEON`);
   2. **match initials** (topic `J.` matches a title word starting `J`, so
      `Corot, J. B. C.` reaches `COROT, JEAN-BAPTISTE CAMILLE`);
   3. **subset** (topic words ⊂ title words — how `Galilee` reaches
      `GALILEE, SEA OF`);
   4. **fuzzy** edit-distance, for OCR garble. Last and loosest.

   The **fisher's cosine is the catch signal**, so there is no net-width to
   pre-tune: loosen a notch → fish → if the best bucket-fit is strong, we caught
   the right fish (done); if all scores are weak, widen another notch; loosenings
   exhausted with nothing fitting → honest unresolved. Recall widens until
   precision is confident. This is where the old aggressive-fuzzy lives now —
   demoted and quarantined to the ~6k empty bags, gated by the scoreboard's
   confidence, never the engine.

## Evidence (measured, this design session)

- Exact word-set unique: ~27k / 36.8k topics, ~zero false positives.
- Word-subset fill turns misses into bags that *contain* the answer (Zürich picks
  up `ZÜRICH, LAKE OF`; Galilee `GALILEE, SEA OF`) — collisions *rising* is good.
- kind alone: reliable on cross-kind (~a third of collisions), incomplete
  elsewhere (missed `Pica`→mammal, `Cunningham`→economist).
- Word-overlap scoreboard: **fails** (verbosity bias + is-a blindness) — 44.7%
  agreement with kind. Rejected.
- **LLM judge: 10/10** on the hard cases that broke *both* kind and word-overlap.
- **fastembed cosine: 10/10** on the same cases (beats kind on its blind spots);
  70.6% agreement with kind at scale (two independent signals concurring),
  81.3% clear winners on kind-couldn't bags.

## Target / acceptance bar

Because every topic is supposed to resolve, the bar is high and testable:

- **~100% resolution.** Every *name* link resolves (stages 2-4 + always-pick).
  The only accepted shortfall is a **couple of section links** (stage 1, `§`/`#`)
  that genuinely can't locate their section — the one stage allowed to miss.
- **≥98% accuracy.** Verified the same way the fisher was: the **LLM as
  ground-truth oracle** over a random sample of finished resolutions (it hit 10/10
  on the hard cases; a few-hundred-link sample gives a real accuracy number).

Resolution rate is a plain count; accuracy is the oracle sample. Both are the
bar the build must clear, not aspirations.

## Build plan

- New module for the fisher (kind → embedding → LLM cascade) + an embedding index
  over article leads (build once, cache vectors; `fastembed`, new light dep).
- Rewrite `build_resolver.resolve` as the four clean stages; delete the alias/
  by_base/fuzzy entanglement and the `_CAT_FIELD`/vocabulary scaffolding that the
  embedding subsumes (keep `lead_kind` as the cheap first rung).
- Regression net: word-set exact is the floor; fish only touches collisions;
  loosen only touches empty bags — prove no previously-resolved topic moves
  (input-keyed audit, *not* an output diff — `resolve` overwrites display/target,
  and dedup/sort are resolution-dependent, so diff the resolver *input→filename*).
- Empty-bag loosening is the last, hardest corner — string work, deferred.

## Invariants

- Recall and precision are separate operations; heuristics never pick.
- Stage 3/4 run only on a stage-2 miss/collision → nothing can override an exact
  match, by construction.
- The bucket is a category → membership, never keyword bingo.
- Audit the resolver by its **input→filename**, never by diffing `classified_toc`
  outputs (display/target/order are all resolution-dependent).

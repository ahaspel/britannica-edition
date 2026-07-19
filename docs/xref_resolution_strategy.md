# Article-xref strategy — extraction quality + cue-tiered resolution (design of record)

Scope: **article cross-references only** — in-prose references from one EB1911
article to another. How we **extract** the implicit ones faithfully, and how
**hard** we resolve each, scaled by the confidence of the cue that produced it.
Design session 2026-07-19.

## Three separate concerns — this doc is one of them

Topics, article xrefs, and contributors *look* alike (each "resolves a name to an
article") but are **three almost entirely separate concerns** — different inputs,
different precision bars, and, the deciding difference, **different disambiguating
signals**:

| concern | input | disambiguating signal | precision bar | status |
|---|---|---|---|---|
| **Topics** | reader's-guide entry in a category bucket | **the bucket** — it names a clean attribute (country, profession) the lead states | recall-happy; every entry *is* a real article | done — `topic_resolver_redesign.md` |
| **Article xrefs** | an in-prose reference (`«LN»`, `q.v.`, `See …`) | **the cue + the surrounding prose** — there is *no* bucket | mixed, **by cue** | **this doc** |
| **Contributors** | a signature / master index | **the master index** (footer initials, vol-29 roster) | zero false positives | settled, different world — `plan_xref_resolution.md` |

They share *code* where convenient (the kind index is one such utility), but they
are **not one strategy**, and the topic machinery does **not** transfer. An
article's own topics are only *adjacent* to a reference's target — never its
bucket — so the single most powerful topic signal, **bucket-context matching, is
not available here.** Article xrefs must be resolved from what they actually have:
**the cue and the prose.** Everything below is built from those two, on their own
terms — not by analogy to topics.

## Explicit vs implicit — where the work is

- **Explicit** — the raw wiki bracketed the link (`«LN:target|display«/LN»`). The
  author *declared* it a reference; extraction is reading the marker, and
  resolution is largely in hand (audit to confirm). **Not the problem.**
- **Implicit** — *we* synthesize the link from an editorial cue (`q.v.`, `cf.`,
  `See`, lowercase `see`). We are deciding it's a link. **This is the whole
  problem**, and it splits into two independent matters that must not be conflated:
  1. **Reading** (extractor) — recover the reference string faithfully: right
     phrase boundary, right direction, no conjunction-truncation. It **gates
     everything** — a mis-read reference resolves wrong no matter how good the
     resolver is.
  2. **Reality-judgment** (resolver) — is this even a link, and which article? The
     extractor is structurally unequipped (no title index, no context); the
     resolver is built for exactly this.

## Keystone: the cue is a confidence prior

The cue tells us how likely the thing is a *real* reference **before we look at a
single candidate.** That prior sets both how hard to resolve and what a *failure*
to resolve means:

| tier | cue | prior | effort | a failed resolve means |
|---|---|---|---|---|
| 1 | explicit `«LN»` | it **is** a link | look **really hard**; loosen aggressively | genuine miss → flag/keep, **never drop** |
| 2 | `q.v.`, `cf.` / `compare` | almost certainly a link | look **pretty hard** | probable miss → try harder before giving up |
| 3 | `See` / `see` | often just prose | look **lightly** | probably not a link → **drop** |

Because xrefs are **mixed-precision by cue**, "always pick" holds only for tiers
1–2 — there, abstaining is a *bug* (it *is* a link, go find it). For tier 3 the
opposite holds: *not* picking is frequently correct, and aggressiveness would
manufacture false links. The tier is really **cue × form**: an all-caps end-of-
article `See BABYLONIA AND ASSYRIA` is a deliberate cross-reference (reliable); a
lowercase mid-sentence `see the table above` is noise. `q.v.` is almost as good as
an explicit link; `cf.` a notch below; the bare lowercase `see` is the false-
positive factory.

## The prose is the other lever

With no bucket, the only article-native disambiguating signal *besides* the cue is
the **prose around the reference** — the sentence that motivates the "see." That
is the honest answer to "what can we give the resolver?": **not** the containing
article's topics (adjacent at best), but the local context of the reference
itself. The mechanism is the fisher's, re-keyed: embed the reference's prose
context and match it against candidate leads (the topic fisher matches a lead
against a *category*; here we match it against the *prose* — same cosine, a
different key). This is the resolution-side design to develop **after** the
extraction audit; flagged now only so the resolver is built around the prose, not
around a borrowed topic bucket that doesn't exist here.

## Division of labor

- **Extractor** — read the reference faithfully, **tag its cue/confidence**, be
  **liberal**. Stop pre-judging "see" quality: `_is_plausible_target` is guessing
  *blind* at whether a phrase is a real article — the reality-judgment we are
  moving to the resolver. Keep only **structural** rejects (bibliographic
  citations, cross-project `:sv:` prefixes, broken markup); those are reading
  hygiene, not reference-reality judgments.
- **Resolver** — the precision gate. Resolve under the cue's tier: title index +
  prose context + cue-gated abstain threshold. For tier 3 a *failed* resolution
  **is** the filter — lands cleanly → it was a reference; doesn't → it was prose,
  drop it.

## The extractor today (`src/britannica/xrefs/extractor.py`) — corrected record

- `«LN»` markers → `xref_type="link"`.
- **`q.v.` IS handled** (correcting a mid-session claim that it was un-extracted):
  `_QV_LINK_PATTERN` catches a pre-linked `«LN»…«/LN» (q.v.)`; `_QV_PATTERN` +
  `_extract_qv_target` catch the plain-text form, walking **backward** up to six
  words through the capitalized run (`"…as Geber (q.v.)"` → `Geber`). It is the
  file's opening pattern, commented "the dominant cross-reference pattern." Both
  emit `xref_type="qv"`.
- Everything else collapses into just two labels: `see` and `see_also`.

### Defect 1 — the taxonomy discards the confidence signal (the keystone fix)

`xref_type` has four values (`link`, `qv`, `see`, `see_also`), but **`see` alone
is fed by seven patterns of wildly different reliability**:

- all-caps `See BABYLONIA` (`_SEE_PATTERN`) — the deliberate end-of-article cross-
  reference: **high** confidence;
- `cf.` / `compare` (`_CF_PATTERN`, `_COMPARE_PATTERN`) — editorial "compare",
  **tier-2** confidence — yet tagged `see`;
- `see article X` (`_SEE_ARTICLE_PATTERN`, ~68% precision), mixed-case `See X`,
  paren `(See X)`, and lowercase mid-sentence `see x` (`_SEE_LOWER_PATTERN`, ~78%
  **junk** per the code's own comment) — a **tier-3** spread.

All seven land as `see`; `see_also` collapses the same way. The extractor
*computes* the confidence — the pattern that matched **is** the tier — then throws
it away. **The single most important extractor change is to preserve the tier**:
emit a confidence tag per xref (at minimum split `cf`/`compare` and the all-caps
forms out of `see`) so the resolver can key its effort. Implementing the tiers
*starts* by not discarding what the extractor already knows.

### Defect 2 — reading errors (faithfulness)

- **Conjunction-truncation.** `_TARGET_TAIL` stops at `and`/`or`/`of`/…, so
  mixed-case `see Babylonia and Assyria` yields only `Babylonia`; the all-caps
  path does the *opposite* and swallows `AND` into the title. Compound references
  are read wrong in both directions.
- **Boundary reach.** The `[A-Z][A-Za-z]…{2,80}` window with stop-words over- and
  under-reaches at the edges — the trailing-initial and legal-citation special-
  cases inside `_is_plausible_target` are patches over exactly this.

### Defect 3 — `_is_plausible_target` is doing the resolver's job

Its **semantic** guesses ("is this a plausible article name") are the reality-
judgment the extractor cannot make well; retire those to the resolver. **Keep**
its structural rejects (bibliographic, `:sv:`/`:de:` cross-project prefixes,
stray-semicolon markup) — those are faithful-reading hygiene.

## Audit plan (runs after the current rebuild — no corpus scans until it lands)

Per cue, on real instances:

1. **Counts per tier** — `link` / `qv` / `cf`+`compare` / all-caps-`See` /
   lowercase-`see`. Sizes where effort belongs. (Start: `plan_xref_resolution.md`
   sizing, 2026-07-16 — 30,444 `link` xrefs, ~1,092 explicit parenthetical hints,
   ~697 bare exact-collisions.)
2. **Reading accuracy per cue** — sample N, diff the extracted string against the
   source phrase: truncations, bad boundaries, `q.v.` direction errors.
3. **"see" precision** — of lowercase `see x`, what fraction point at a real
   article. Validates the tier-3 "drop on failed resolve" policy with a number.

## Invariants

- **Topics, article xrefs, and contributors are separate concerns.** Shared code
  is fine; shared *strategy* is not. The topic bucket does not exist here — resolve
  from the cue and the prose.
- **Reading** (extractor) and **reality-judgment** (resolver) are separate; the
  extractor never decides whether a "see" is a real link.
- **The cue is a confidence prior.** Effort and abstain-threshold scale with it:
  tier-1 failure = flag/keep, tier-3 failure = drop.
- **Preserve the cue/confidence at extraction.** Never collapse distinct-
  confidence cues into one label — Defect 1 is the canonical violation.
- The extractor is **liberal** on tier-3 candidates (the resolver filters) but
  **faithful** on every read (a mis-read reference is unrecoverable downstream).

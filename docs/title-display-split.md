# Design: split the fused title into canonical TITLE + DISPLAY

**Status:** proposal (scoped, not started)
**One line:** article identity, titles, URLs, search, and xref resolution all derive
from a single overloaded string. Split it into a **canonical headword (TITLE)** and a
**descriptor (DISPLAY)**, and give identity a **furniture-free number** — one structural
cut that fixes four surfaces at once.

---

## The problem

Today one string does four jobs it shouldn't:

- the **headword** a reader/xref actually names ("ALEXANDER", "WILLIAM"),
- the **disambiguator** that tells duplicates apart ("(Athenian philosopher)", "King of England"),
- the **sobriquet / common name** people search ("the Great", "the Conqueror", "of Macedon"),
- and, leaking in through the back, the **Wikisource `<section>` transclusion label**
  (`s5`, `Algebrab`, `Conon2`) that we mistakenly use as the identity slug.

Because they're fused, every consumer is compromised: URLs surface furniture, titles are
wrong, search can't find common names, and the xref resolver can't disambiguate.

## Evidence — three quantified payoffs (+ one live proof)

| Surface | Failure mode | Measured scope |
|---|---|---|
| **Identity / URLs** | `<section>` furniture *is* the primary key: `/article/01-0036-s5/abacus`, `…-algebrab/…` | **19,178 URLs** re-slug (51%); **763** same-page headword collisions (1,622 articles) |
| **Search** | Sobriquet/common name isn't in the indexed title | **668** regnal-name titles (WILLIAM I, ALEXANDER III…) + ~1–2.5k more with a sobriquet only in the opening |
| **Xref resolution** | Bare-headword match picks the wrong article; the disambiguator in the link text is unused | **6,390 (19%)** of resolved xrefs sit on an ambiguous headword; **≥141** resolve *outside* the candidate set (WOOD→WOOD GREEN, COOPER→COOPER UNION, ELIZABETH→ELIZABETH CITY, William II→Sicily) — a conservative floor |
| **Titles** (symptom) | `<section>` chunk-label leaks as the display name | **13** articles: `ALGEBRAB`, `CONON2`, `TENTB`, `S1`, `CONFEDERATE STATES OF AMERICAN`… |

**Live xref proof — ODO OF BAYEUX.** The body reads *"See the authorities cited for
William I., King of England and **William II., King of England**"* — and that second link
resolves to `28-0691-william-ii-of-sicily-WILLIAM_II_OF_SICILY.json`. A **Sicilian king**,
for a link that explicitly says *King of England*. The disambiguator is in the link;
the resolver can't use it because it matched the bare headword "William II".

**Live identity proof — ALGEBRA.** One complete 28k-word article, correctly assembled,
but titled/URL'd `ALGEBRAB` because its Wikisource page-chunk was labelled
`<section begin="Algebrab"/>`. Its real heading (`«TITLE»`) is "ALGEBRA".

## Root cause

`stable_id = {vol}-{page}-{slug}` where `slug = section_slug(section_name or title)`, and
`section_name` is the Wikisource `<section begin="…"/>` label. So **identity is derived
from transclusion furniture**, and the title field inherits the same label whenever the
heading recognizer defers to it. Uniqueness rides on how a Wikisource contributor happened
to name a section — which is why `s5`, `Algebrab`, and `Conon2` all end up as primary keys.

## The design

Separate the three concerns and make identity a number we own:

1. **TITLE — the canonical headword.** The primary term of the `«TITLE»` heading, before
   the first comma/qualifier: `ALGEBRA`, `AARSSENS`, `WILLIAM II`, `AESCHINES`. Intentionally
   **non-unique** — it's the match key, not the identity.
2. **DISPLAY — the descriptor (optional).** The rest of the heading line **plus** the
   opening sobriquet: `William II, King of England`; `Alexander III, king of Macedon,
   surnamed the Great`; `Aeschines (Athenian philosopher)`. Serves *both* human
   disambiguation *and* search.
3. **Identity — a furniture-free number.** Slug = `section_slug(TITLE)` with a **numeric
   tiebreak** only on a genuine `(vol, page)` collision: `aeschines`, `aeschines-2`. The
   tiebreak is **ours** (deterministic position), never a scraped `<section>` label. The
   `<section>` tags stay where they belong — segmentation only.

### What each consumer gets

- **URLs:** `/article/{vol}-{page}-{headword}[-N]/{headword}` — no `s5`, no `Algebrab`,
  no over-long full-name slugs.
- **Search:** index **TITLE + DISPLAY**, so "Alexander the Great", "William the Conqueror",
  "Philip of Macedon" all hit — the sobriquet is now a first-class search key.
- **Xref resolver:** build the candidate index on **canonical TITLE** → an exact,
  clean candidate set (`William II` → {England, Sicily, …}); then disambiguate against the
  **DISPLAY** descriptor using the qualifier carried in the link text ("King of England").
  Ambiguity becomes explicit and *resolvable* instead of a silent wrong pick.

## Migration

This re-keys identity, so it is a real migration, not a patch:

1. **DISPLAY-extraction pass.** Derive TITLE (primary headword) + DISPLAY (descriptor)
   from the `«TITLE»` line + article opening. Store both as export fields; leave
   `article.title` (the DB identity) untouched until step 3 so the render stays stable
   meanwhile.
2. **Re-slug + redirect map.** New identity = `{vol}-{page}-{headword}[-N]`. Emit a
   complete **old→new redirect map** (~19,178 entries) so every bookmarked/inbound URL
   302s to its new home — zero 404s is the hard requirement.
3. **Resolver rework.** Candidate index on canonical TITLE; DISPLAY-qualifier
   disambiguation; explicit "ambiguous, N candidates" state instead of a heuristic pick.
4. **Search reindex.** Index TITLE + DISPLAY; result rows show DISPLAY.

## Open items / risks

- **Persist the resolution as a derived artifact (companion, do first).** The export
  already computes *every* xref with a `status` at `resolve_one`, then discards the
  unresolved ones. Collect them all into a `xref_resolution.jsonl` (source, surface,
  target, status, chosen) — the same dump-on-export shape as `article_index.tsv`. This
  is not a re-architecture (resolution stays in-memory, single-pass), and it pays for
  itself three ways: (1) a **diffable resolution regression net** — xrefs shouldn't
  change, so a diff catches it when they silently do; (2) it **unblocks the
  unresolved-recovery measurement** below; (3) one computed-once source for site, EPUB,
  and analysis.
- **Xref payoff — mis-resolution measured, recovery still open.** Mis-resolution is now
  a number (see the table: 6,390 ambiguous, ≥141 out-of-set). The *unresolved-recovery*
  half — how many currently-unresolved xrefs a canonical index would rescue — needs the
  persisted table above (unresolved targets aren't recorded today). Falls out for free
  once resolution is persisted.
- **Primary-headword extraction — DONE** (`britannica.util.strings.primary_headword`,
  22 unit cases). Validated across all 36,688 corpus headings: 88% single-word, **0**
  leftover brackets/commas, **0** empties; persons → surname, regnals → name+numeral,
  genuine multi-word titles (`ACTS OF THE APOSTLES`) kept whole.  **Viability result:
  the re-slug is a clean sweep** — headwords extract tidily, so the migration's URLs
  come out clean (`algebra`, `aarssens`, `william-ii`). This was the open risk on
  whether the migration is even worth doing; it isn't a blocker.
- **Redirect coverage** must be exhaustive; a re-slug with a gap breaks live links (the
  exact churn we've been guarding against).
- **Tiebreak stability:** position-based `-2` is stable only while per-page segmentation
  is stable. Acceptable for a mature corpus; note it.

## Why it's worth the migration

Three of the project's hardest surfaces — identity, search, and link resolution — are all
degraded by the *same* fusion. Pulling the headword, the descriptor, and the transclusion
label apart is one structural cut that improves all three, and forecloses the whole class:
no future Wikisource labelling quirk can ever surface as a URL, a title, or a mis-resolved
xref again.

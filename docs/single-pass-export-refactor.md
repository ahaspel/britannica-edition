# Export refactor: drop `article.body`; xrefs become one isolated pass

## One line
The article body is never stored. The pipeline becomes: **walk → assemble an
in-memory corpus → run the xref module once over it → serialize to JSON.**
`article.body` and the stored `CrossReference` table both disappear, and xref
handling collapses from a scattered chain (extract → intra-resolve → inter-resolve
→ export-wrap-by-re-search) into a single isolated module that runs exactly once,
with the whole corpus in hand.

## Why
`article.body` is a flattened-tree cache that drifts from the code — days locally,
weeks on the live site. Every downstream stage reparses it. Stop storing it and the
reparses lose their reason to exist.

Xrefs are the one thing that genuinely cannot fold into the per-article structural
walk, for two reasons no cleverness removes:
- **They read prose.** "see PHYSIOLOGY" is language, not structure; the structural
  walker must not touch it (and *can't* — you can't even bound the span until
  something resolves).
- **They need the whole corpus.** A reference can point forward; whether "see X" is
  a link at all depends on whether X exists. You cannot decide one until you have all.

So we stop fighting it. Xrefs get **one separate module**, run once, after the corpus
is fully assembled — the only point at which it is *possible* to handle all of them,
and therefore the only point at which dropping a resolvable link becomes structurally
impossible. (Dropping resolvable links is non-negotiable; this timing is the guarantee.)

## The pipeline

### Stage 1 — walk + assemble (in memory)
The walker is **unchanged** and stays structural. It marks explicit
`{{EB1911 article link}}` as `«LN:target»` — pure template preservation, carrying the
target through the render; it decides no link and resolves nothing. Bare prose
("see PHYSIOLOGY") is left as prose. The export assembles each article body and holds
the corpus in memory: a `dict[id → body]`, a few hundred MB for ~44M words, transient,
**never written to the DB**. The resolution index (the titles, taken from the recognized
TITLE elements — see the title-fold — plus what the content rung keys on) is accumulated
as the corpus assembles.

**No `article.body`. No `CrossReference`.**

### Stage 2 — the xref module (one pass, in memory)
A single isolated module, run once over the assembled corpus. Three steps (the user's):
1. **Find candidates.** Reuse `xrefs/extractor.py`'s trigger detection (`(q.v.)`,
   `See`/`see`, `Cf.`, `compare`, the parenthesized `(See …)` forms) to locate every
   place that might be a link, and add them to the explicit `«LN»` markers — one unified
   candidate set. *The one improvement over today:* the span is the **longest prefix that
   resolves** against the index, not the `_TARGET_TAIL` regex guess `extract_xrefs` is
   forced into because it runs before any index exists. Resolution decides the boundary.
2. **Resolve each.** Reuse `resolve_one` (exact / fuzzy / alias / section / Bible / cache)
   against the in-memory index. The content rung — references matching no title — finally
   runs *here*, where the whole corpus is available to match against; impossible upstream.
3. **Write back.** Resolved → link, **in place** (no re-`search`, so the wrapping leak
   that silently drops resolved prose links is gone). Unresolved → leave as prose — only
   the genuine no-target residue, never a resolvable link.

### Stage 3 — serialize
Walk the in-memory dict → JSON. The shipped artifact.

## Isolation — what the module owns, what it touches
The module owns **all** xref handling; everything else is innocent of it:
- the walker marks `«LN»` (preservation) and otherwise knows nothing of xrefs;
- the export assembles bodies and knows nothing of links;
- `article_json.py` loses `_resolve_link` and `_wrap_resolved_xrefs_in_body` entirely.

Its only inputs are the in-memory corpus + the index; its only output is the same
corpus with links written in. A self-contained box, one entry, one exit — "as isolated
and painless as possible," which is the right shape *because* xrefs are irreducibly a
separate step.

## The pattern: a Decorator over the assembled corpus
This is the Decorator pattern, with one precision: the decorated object is the **corpus**, not
the article in isolation. Assembly produces the base (the bodies), innocent of links and
bylines. Each cross-corpus concern is a **decorator** — corpus in, corpus enriched out,
ignorant of its siblings: xrefs first, **contributors** (page + bios) next, then backlinks /
search index / anything that spans articles. Each touches every article *through its
whole-corpus view* — the only way it can resolve a link or aggregate a contributor — and that
corpus-scope is exactly why it can't fold into per-article assembly.

Two things the pattern buys beyond description:
- **The contract:** a decorator takes the assembled corpus, returns it enriched, and knows
  nothing of the others — one entry, one exit, the isolation made an invariant.
- **The placement test:** needs only the local article → it's assembly; needs the whole corpus
  → it's a decorator, a peer pass. The pattern decides where anything new goes, so the argument
  never recurs.

It also draws the "no post-passes" line cleanly: a decorator *produces* its own concern (links,
attributions) with the corpus as input — it is **not** a sweeper patching the body's output.
Producing a new layer is legitimate; patching an old one is the sin. Holding the corpus is what
makes the decorator half possible, and its cost amortizes across every tenant — never an
xref-specific price.

## The building blocks already exist (relocation, not invention)
- **candidate-finding:** `xrefs/extractor.py` (triggers + patterns).
- **resolution:** `resolve_one` + `build_resolution_index` (already extracted from
  `resolve_xrefs_all`).
- **collision-aware lookup / aliases / fuzzy / disambiguation cache:** `resolver.py`,
  `scoring.py`, `alias_table.py`, the cache file — reused as-is.

## What's retooled (the "bit")
- `build_resolution_index` sources from the in-memory corpus, not a DB query.
- candidate spans use longest-resolving-prefix (index in hand) instead of `_TARGET_TAIL`.
- linking is in place; `CrossReference` writes and the export re-`search` wrap are deleted.
- `resolve_xrefs_for_volume` (intra pass) is deleted — one corpus resolution, not two.

## What disappears
- `article.body` (the field) and the `CrossReference` table.
- `extract_xrefs` / `resolve_xrefs` as separate pipeline stages → folded into the module.
- the intra/inter resolution split.
- `_resolve_link` + `_wrap_resolved_xrefs_in_body` in `article_json.py`.

## Deferred to their own arcs (Stage-1 assembly, not this doc)
- **Title as element (a bonus the new architecture unlocks):** because the resolution
  index now sources from the TITLE elements, `detect_boundaries` sheds title-fetching
  entirely and returns to pure boundary-detection. The title is extracted **exactly once**,
  in the walk, and that one recognition feeds both `title_display` and the index — detector
  reads to partition, element extracts, the project's own rule honored for the title at
  last. (Pieces exist: `super_walker.py`, `elements/_title.py`.)
- **Contributors:** the same two-kinds split as xrefs. The byline is a per-article lookup
  (initials → name via the contributor table) — local, fits Stage-1 assembly. But the
  contributors page and the bios are **cross-corpus aggregations** (they need every article),
  so they become a module over the assembled corpus — a peer of the xref module, run once.
  Its own arc, but the shape is already known, and the corpus-hold already pays for it.
  It's also the only reasonable way to **recover the mid-article bare initials** —
  section-level contributor signatures embedded in prose that the table extraction misses
  today and we've been losing. They're the contributor twin of the bare-prose "see":
  prose-embedded, corpus-table-resolved, caught by the same scan-then-resolve, lost
  everywhere else.

## Verification
Fresh-rebuild a volume for a clean baseline (`tools/db/rebuild_volume.sh`), then diff the
new pipeline's JSON against it, field by field. The link set must be a **superset** of
today's: the module recovers the wrapping-leak drops and resolves the content rung in
place. It must never drop a link today's pipeline makes. Body/word_count/sections may
legitimately freshen (always walked); resolution must not regress.

## Settled decisions
- `article.body` is never stored — in-memory only, per build.
- Xrefs are one isolated module, run once, after full assembly — by their nature.
- Resolution is corpus-wide and single (no intra/inter).
- Candidate spans **resolve**, they don't guess.
- Drop **zero** resolvable links — the acceptance bar, non-negotiable.

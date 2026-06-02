# The Canonical Path

The good path: the few steps that create an article or a plate **the proper
way**. This is the spec. The cleanup campaign is its **complement** — anything
running outside these steps is scaffolding and has to go (see "What Must Go").

Stay on the path. When something is wrong, the fix is almost always *delete the
off-path pass and let the path own the shape* — not patch the pass.

---

## 1. Article creation — the good path

A **linear pipe** — each stage consumes the previous stage's output; nothing is
shared sideways:

```
make_stream()            → raw continuous stream (article pages joined)
preprocess(stream)       → clean frozen stream
detect_boundaries(clean) → article[]            (complete by construction)
  per article:  walk → classify → produce       (= process_elements)
export(article)          → JSON
```

1. **make_stream** — gather the article-only wiki pages into one continuous
   volume source from **raw** `page.wikitext`, with page markers
   (`\x01PAGE:N\x01`) carried for later page-number bookkeeping
   ([[feedback_segments_two_purposes]]). One assembly, not two — today
   `super_walk.volume_stream` and `super_detect.raw_stream` build it
   independently and identically; they collapse to this. (The per-page
   `prepare-wikitext` stage is DELETED — its corrections + quote-runs move into
   `preprocess`, step 2; raw stays raw.)
2. **Preprocess** — clean that continuous source ONCE, up front. Two jobs:
   (a) **source cleaning** — corrections (`data/corrections.json`),
   quote-run → `«B»`/`«I»`, `<noinclude>` strip **wholesale** (verified
   corpus-wide: on the continuous stream, table markers balance in 23/28
   volumes — *including* UNITED STATES, the feared counter-case; the per-page
   "preserve `{|`/`|}`" logic was a per-page-isolation band-aid. 5 volumes —
   14/16/17/19/22 — carry ≤6 residual unbalanced markers each, a bounded
   follow-up; only vol 19 has a premature-close. **NOT section tags** — those
   are detect's input: detect consumes `<section begin>` for stable-ID names,
   so they survive preprocess and drop *after* detection), fine-print `/s`–`/e`
   strip, HTML comments, word-spacing. Most of this is what the (dead)
   `source_cleanup.py` already implements. (b) **heal every page transition AT
   THE SEAM** — cross-page hyphenation
   rejoin, cross-page sentence reflow, chrome at the boundary — because the
   continuous stream is the ONLY context where both sides of a transition are
   visible at once; doing it per-page or per-article structurally leaks. After
   this, the `\x01PAGE:N\x01` marker survives as **pure bookkeeping** (page
   number + order, nothing else) and nothing about page boundaries leaks
   downstream. **The source is then frozen** — nothing mutates it until producer
   time. (This is where the whole page-break bug class — ABBREVIATION's
   cross-page table, hyphen splits, wrapped sentences — is fixed at the root.)
3. **detect_boundaries(clean_stream) → article[]** — ONE job: partition the
   clean stream into articles. **ZERO source transforms** (preprocess already
   cleaned it). Recognizing the article-opening headings *is* this stage's work
   — the current `super_walker.py` heading-finder folds in here; it is NOT the
   element walker (step 4). Output is **complete by construction**: the volume
   stream is bounded (first byte opens an article, last closes one), so every
   byte is owned by some article — no gaps, no dropped articles (ABSCISSA,
   MALVACEAE, the baseline-gap class dies here). A title heading is recognized
   *as* a boundary and its raw span rides along for the title producer
   (`produce_title`); detect points at the title, never transforms it. Per-page
   `ArticleSegment`s fall out of the carried `\x01PAGE:N\x01` markers
   ([[feedback_segments_two_purposes]]). (detect's current `_preprocess_wikitext`
   + `_strip_noinclude_preserve_tables` are defensive cleaning of dirty input —
   gone, since input is now clean.)
4. **Per article: walk → classify → produce** — the spine, `process_elements`
   (`elements/__init__.py:1187`), fed each article's content (a slice of the
   clean stream). This is the **element walker** (distinct from the heading
   walk in step 3). Producers only; **no source mutation**:
   - **a. classify_article** — walk + classify in one mutually-recursive pass.
     The walker extracts **outer elements ONLY** (it does not classify, does
     not recurse into same-family children, does not parse templates). The
     classifier strips the shape's outer delimiters, asks the walker for
     one-level extracts of the inner, recursively classifies each child, then
     assigns its own label. Returns placeholderized text + a tree of
     `ClassifiedElement` (label, raw, inner, child registry). With BODY-wrap,
     **every byte is owned by some element**.
   - **b. resolve_ref_bodies** — merge `<ref name=…>` / `<ref follow=…>` bodies
     article-wide; thread into `context`.
   - **c. produce_tree** — bottom-up over the tree. Each label's producer
     (`_PRODUCER_DISPATCH`) emits its marker after its children's markers
     exist. Producers are the ONLY place raw→final transformation happens.
   - **d. substitute_top_level_markers** — reassemble = ordered concatenation
     of element markers in walker source order. No body-substrate, no glue
     layer. **This output IS `article.body`. Nothing runs after it.**
5. **export-articles** — serialize `article.body` + metadata to JSON. The
   viewer decodes markers mechanically and invents nothing
   ([[feedback_shape_vs_rendering]]).

## 2. Plate creation — the good path (TARGET)

Plates are a different beast (different inputs, different output expectations)
but the **same spine**: prepare → detect-boundaries (plate spans + plate title)
→ `process_elements` with plate classifier labels (e.g. `SIMPLE_PLATE`,
`GROUPED_PLATE`) → plate producers (sharing the ICL / legend building blocks,
[[feedback_pipelines_share_producers]]) → assemble → export.

**Current violation:** `transform_articles/__init__.py:472` runs
`parse_plate(raw)` — the entire old `parsers/plate/` pipeline — standing in for
`process_elements`. That is why AEGEAN CIVILIZATION Plate I is flat and broken.
Migrating plates onto the spine is the largest single deletion in the campaign.

## 3. Metadata enrichment — orthogonal sidecar (stays)

These enrich the `Article` record; they do NOT create the body and must never
mutate it:
- **extract-xrefs / resolve-xrefs** — cross-references.
- **extract-images** — image-asset records.
- **extract-contributors** — reads `{{EB1911 footer initials|…}}` from raw →
  `article.contributors`. (The footer's *body rendering* — render nothing — is
  the spine's job, not this stage's.)

---

## Invariants — what "on the path" means

1. **Transform in exactly two places:** the up-front **preprocess stage**
   (step 2 — corrections + pure-noise stripping on the whole volume source,
   before boundary detection), or a **producer**. After preprocess the source
   is frozen; the walker and classifier only READ it.
   ([[feedback_transform_only_two_places]])
   **Corollary — NO per-article source transformation exists.** The transform
   stage is `process_elements` on the article's span and nothing wrapped around
   it. Every pass in today's `_transform_text_v2` (noinclude/fine-print strip,
   cross-page reflow/hyphenation, chart2 inject, paragraph reflow, comma/punct
   cleanup, blank-collapse) and the per-plate `parse_plate` violate this and go
   — up to whole-volume preprocess, into a producer, or deleted.
2. **The walker extracts outer elements only.** No classification, no
   inner-template recognition, no reaching inside a node. ([[feedback_stupid_walker]])
3. **The classifier returns only a label**; recursion is its job; producers
   extract their own content. ([[feedback_classifier_returns_only_label]])
4. **Producer output is the final body.** No pre-pass, no post-pass, no
   sweeper, no fallback, no fixup. ([[feedback_pipeline_is_the_only_clean_place]],
   [[feedback_article_owns_assembly]])
5. **The viewer is mechanical** — decodes markers, decides no source questions.
   ([[feedback_shape_vs_rendering]])
6. **No fake recursion.** Balanced `{{…}}` / `[[…]]` structure is recognized by
   a single true balanced-delimiter scanner, never a depth-enumerating regex.
   ([[feedback_recurse_it_dont_layer_it]])
7. **No catch-all sweepers.** Every unhandled shape is a producer gap to close,
   not markup to silently delete. ([[feedback_sweepers_hide_bugs]])
8. **No per-page processing.** Past `make_stream`, the page is a bookkeeping
   marker (a `\x01PAGE:N\x01` position carrying a page number), never a
   processing unit — per-page work can't see across the seam, defeating the
   continuous stream. Everything operates on the **stream** (preprocess,
   detect) or on an **article** (walk/classify/produce). The per-page
   `prepare-wikitext` stage is deleted; its corrections + quote-runs move into
   `preprocess`.

---

## What Must Go — the complement (deletion worklist)

Everything not in §1–§3. Gated by scoreboards reading zero, then deleted.

**Sequencing rule:** the moment a canonical stage *owns* its job, **delete
outright** every other place doing that work — do not relocate, do not keep "in
case" ([[feedback_delete_dead_code]]). Build the owner, wire it, then the copies
are dead by construction. (Phase 1: build+wire `preprocess`. Phase 2: delete the
5 live noinclude strips + 2 dead + 1 legacy, `transform`'s noinclude/fine-print/
reflow/hyphenation passes, `detect._preprocess_wikitext`, the duplicate
walk/detect stream assembly, and dead `_parse_page`/`_fix_swallowed_pages` — all
under the snapshot net.)

- **`_strip_templates`** (body_text.py:1508 + detect_boundaries.py:68) — the
  catch-all sweeper. Drain each family into a producer until zero, then delete.
  Scoreboard: `tools/diagnostics/strip_scan.py` (currently **554 deletions, 88
  families**; `{{Ts}}`=287 dominates).
- **16 fake-recursion regexes** → one shared balanced scanner. Scoreboard:
  `tools/diagnostics/fake_recursion_audit.py`. (depth-3 blob duplicated 5×.)
- **`parsers/plate/` + `plate_legacy.py`** — replaced by the spine (§2). Plus
  the dead `plates: []` field.
- **NOT deletion — relocation:** `_apply_markup` / `_transform_body_text` (the
  BODY producer's markup tool) are *correctly placed* — producer-only (called
  by `_produce_body` and the threaded `text_transform` in every producer). They
  live in the wrong *module* (`transform_articles/body_text.py`, forcing a
  lazy-import cycle). When the `transform_articles` wrapper dies, they **move to
  `elements/_body.py`** beside the producers they serve. Keep the tool; delete
  the wrapper around it. (Implementation quality is a separate axis from
  placement — [[feedback_clean_text_only_in_producers]].)
- **`_transform_text_v2` itself — the function, not just its passes.** A
  per-article transform locus is an *attractor*: it exists, so every special
  case gets bolted in as another pass (that is how it accreted nine around one
  `process_elements` call at line 288). DELETE the function; the
  `transform_articles` loop calls `process_elements` directly on each article's
  span. With no per-article transform box, per-article mucking has nowhere to
  land. Every pass goes to ONE of exactly **two** homes — there is no third
  "delete" or "fixup" bin:
  - **→ PREPROCESSOR** (§1 step 2 — whole-volume source cleaning before
    boundaries; nothing downstream consumes these, [[feedback_good_preprocessing]]):
    `<noinclude>` strip (269), fine-print `/s`–`/e` strip (284), cross-page
    sentence reflow (319), hyphenation rejoin (330), and chart2 "lost markup"
    injection (291–296) — which becomes "ensure the source is complete," after
    which the figure producer renders it normally. These also kill the
    duplicate noinclude strips in `detect_boundaries` / `parsers/plate/images.py`
    and resolve the dead `source_cleanup.py` (it becomes the preprocess home).
  - **→ PRODUCER** (the producer owns its output shape, so the standalone
    cleanup pass evaporates rather than being "deleted"): paragraph reflow
    (333) → BODY producer; leading-comma strip (338) → `produce_title`/BODY
    (consume the comma at the cut); orphan-punctuation (347–348) → the producer
    normalizes the content it owns (and has nothing to clean once
    `_strip_templates` is gone); blank-line collapse (355) → the marker-assembly
    step (`substitute`) owns inter-element spacing.

**Proof of done:** `strip_scan` = 0, `fake_recursion_audit` = 0, `parsers/plate`
deleted, **`_transform_text_v2` deleted** (the `transform_articles` loop calls
`process_elements` directly on each article's span) — verified against the
corpus snapshot net (`tools/diagnostics/snapshot_corpus.py`).

See also [[project_cleanup_campaign]] for the running state.

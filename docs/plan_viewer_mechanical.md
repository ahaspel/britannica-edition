# Plan: make the viewer a mechanical decoder

**Drafted 2026-06-14.**  Status: the leak/producer backlog is effectively closed
(BROKEN ≈149, ~90% broken source — see `status.md`), so the viewer is now the
remaining source of nearly all bugs.  This plan drives it to a pure decoder.

---

## Objective

The viewer renders the carried marker stream by **pure token→tag substitution**
and holds **no opinions** about structure, placement, or headings.  Every
structural decision —

- what is a heading / section / shoulder, and its display name, slug, TOC level;
- where a paragraph or a block begins;
- what class a table carries —

is made by the **producer** and carried in the marker.  The viewer renders what
it is given.  This is the [[feedback_viewer_mechanical]] / [[feedback_viewer_no_regex]]
keystone applied end-to-end.  The natural consequence is a **considerably smaller
viewer** (rough estimate: a third to a half off the current 4,095 lines).

## Governing method (non-negotiable)

Per [[feedback_producers_before_rendering]], for **each** workstream:

1. Teach the **producer** to carry the decision (emit it in the marker).
2. **Full rebuild** to freeze a static target.
3. **Then** delete the viewer logic that made the decision.
4. Diff rendered HTML of a brutal-case snapshot set — every diff is identical or
   a tagged improvement.

Never delete viewer logic against a moving producer.  The viewer shrinkage is the
*consequence* of moving the decision upstream, verified against a frozen rebuild.

**Snapshot set (the regression net):** AFRICA (prose mass), ABBEY (figures),
ALPHABET (inline glyphs), ARACHNIDA (legends), a plate, a math article, and a
glossary/heading-heavy article.  Capture rendered HTML before; diff after.

---

## The diagnosis — five classes, one disease

Every item below is the viewer **re-deriving a decision the producer should have
made and carried**.

### Class 1 — Structure re-derivation (the biggest)

`detectSections` / `detectHeading` / `scanShoulders` (≈ viewer.html 1854–2035)
re-detect sections, headings, shoulders, and build the TOC by pattern-matching the
stream with **heuristics**:

- `SC_RE` decides a small-caps run *is a heading* (Roman-prefix required, inner
  `<60` chars, not in an IMG/TABLE paragraph) — the canonical "SC detecting
  headings from prose" violation.
- `displaySectionName` inserts spaces at case transitions
  (`BrewingTrade`→`Brewing Trade`); `dehyphenateShoulder` strips wrap-hyphens —
  heuristics *patching* producer output.
- `sectionKey` / `sectionSlug` / `reserveSectionId` + cross-signal dedup — anchor
  / slug minting and dedup in the viewer.

The headings/sections/TOC business should be **entirely producer work**.  Root
cause (scoped in WS1): the authoritative `<section begin="…"/>` tag is rendered to
`""`, so the heuristic above has to *guess* sections from the inconsistently-
templated visible heading — and the same heuristic is duplicated in
`export/sections.py` (Python) and the viewer (JS).

### Class 2 — Decoder duplication (the context-leak class)

`decodeInlineMarkers`, `formatCell`, `applySizeMarkers`, `renderTitleMarkers`, and
`renderParagraph`'s local `applyMarkers` are parallel marker decoders for body /
cell / title / caption.  A marker that renders in one context but not another is
this class (memory's "seven renderers").  Several use the `«X»(.*?)«/X»`
span-match form that re-pairs wrong on nesting.

### Class 3 — Block / paragraph reconstruction

`BLOCK_MARKER_SCAN_RE` + the "mixed-paragraph split" + the non-greedy "repair"
step (≈2386–2460) + `isContinuation` (3301): the viewer scans each paragraph for
block markers, splits prose around them, and repairs nested-table mis-matches —
reconstructing placement the producer should carry.

### Class 4 — Dead / legacy paths

The `{{TABLE}}` / `{{TABLEH}}` decoder + `parseTableCell` + `tableCellHtml` +
`TABLE_CELL` grammar + `mergeTableClass` exist only for the retired align-only
marker (the producer emits `«HTMLTABLE»` now) and deployed-data compat.
`scaleDisplayMath` is already a no-op.

### Class 5 — CSS opinions

Residual imposed widths / alignments / margins (the figtable case was fixed
2026-06-14); audit for the rest so position rides from carried
`align` / `width` / `style`.

---

## Workstreams (sequenced by leverage × safety)

### WS1 — Sections / headings / TOC become producer-decided  ✅ DONE 2026-06-14

**Landed:** `transform_articles/sections.py::stamp_sections` recognizes the major-
section series in `preprocess_article` and tramp-stamps `«SEC:slug|name»` before
each heading (rides the walk like `«TITLE»`); `export/sections.py` and the viewer
`detectSections` both collect `«SEC»`+`«SH»` mechanically; the dual `SC_RE`
heuristic is deleted (viewer −8 KB, both inline scripts `node --check` clean); the
orphaned minor `{{section}}`→`«ANCHOR»` is dropped.  UNITED STATES regains its 10
L1 sections (verified); 378 tests green.  Owed: a rebuild+deploy to ship corpus-wide.

**Scoped 2026-06-14 (corpus + DB).**  A **regression fix** as much as a cleanup:
major sections were silently dropped from the TOC when the producers collapsed.

**The governing realization (user):** recursion is magic for everything
self-contained and decomposable — but **context is exactly what it cannot
provide**, and recognizing a major section *needs* context (you cannot tell a
section heading from a place-name table caption by the element alone; the
discriminator — a *series* of like headings partitioning the article — only exists
with the whole article in hand).  So major-section recognition **cannot live in the
walk**, and it is **not** boundary detection (deliberately structural, blind to
inner content).  It lives in the **post-walk extraction family**, the layer that
holds the produced tree *and* may hunt for context.  `extract_contributors` is the
model; `extract_xrefs` is its sibling.

**Three heading kinds:**

| Kind | Source (inconsistent) | Walk renders (consistent) | TOC? |
|---|---|---|---|
| **Major section** | `{{c\|{{sc\|…}}}}` / `{{csc\|…}}` (roman in/out), rarely `<section begin>` | `«CTR»…«SC»…«/SC»…«/CTR»` | **L1** |
| **Minor section** | `''Name''.—` run-in italic | `«P»«I»Name«/I».—…` | no (stays prose) |
| **Shoulder** | `{{EB1911 Shoulder Heading}}` | `«SH»…«/SH»` | L2 |

**Ground truth.**  The walk *already parses the inconsistent source correctly* —
the sections look right; the defect is only that nothing marks them as sections.
`«SH»` = 17,865 (produced, real).  `«SEC»` = **0** (vestigial).  The `SC_RE` section
heuristic — duplicated in `export/sections.py` (Python) **and** the viewer
`detectSections` (JS) — catches **4** headings in 2 articles and *mis*catches
captions.  `<section begin>` is **not** the signal: it's the Wikisource *article-
boundary* transclusion marker (20,676 articles, one each); only **3** use it for
≥2 named subsections (UNITED STATES / Britain / Drama).  The real set: **1,238**
standalone `«CTR»«SC»` major headings vs **261** caption look-alikes (213 Fig/
Plate/Table-word, 40 table-adjacent, 8 img).  And **217** raw `…#Name` section
links exist but only ~7 resolve — because the majors they target aren't anchored.

**The architecture (post-walk, dependency-ordered):**

```
transform/walk  →  extract_sections (NEW)  →  extract_xrefs  →  extract_contributors  →  export
```

- **Walk** (recursive, self-contained): produces faithful `«CTR»«SC»` and the
  `«SH»` minor anchors.  Recognizes **no** sections.
- **`extract_sections`** (NEW; `extract_contributors` model): per article,
  `walk_article(...)` → `_harvest_sections(body)` — recognize the **major** sections
  by the **series of `«CTR»«SC»` headings** in the assembled tree (the context only
  this layer has), gated against captions by the element's *own* content
  (`Fig/Plate/Table` lead, contains-`{{IMG:}}`).  Bind the **major anchors `«SEC»`**
  (+ a section index, like `ContributorInitials`).  `«SH»` is already the minor
  anchor.  **No anchors except these two** — drop the 760 minor `{{section}}` →
  `«ANCHOR»`.
- **Ordering is the keystone:** `extract_sections` runs **before** `extract_xrefs`
  so the section anchors exist when `[[…#Name]]` links resolve (recovering the ~210
  dropped section links).  Today's `detect_sections` runs at **export — after
  xrefs** — so even correct recognition there could never bind; the recognition
  must move earlier.
- **Viewer** (mechanical): iterate the anchors (`«SEC»` L1 + `«SH»` L2) for the TOC;
  render.  No detection.

**Deletes.** The `SC_RE`/`SH_RE` heuristic, `displaySectionName`,
`dehyphenate_shoulder`, `sectionKey`/`sectionSlug`/`reserveSectionId`, the
caption/`_EXCLUDED_RE`/`<60`-gate machinery — in **both** `export/sections.py` and
the viewer `detectSections`.

**Verify after:** UNITED STATES TOC regains Physical Geography…History; ACADEMIES/
ALPS/AFRICA get their L1 TOCs; ABERRATION "Fig. 2." is not a section; the ~210
`…#Name` section links resolve; no false headings.

**Accepted residual:** a place-name table caption with no self-contained tell and
not part of a heading series may still mis-bind as a section — taken over building
cross-element machinery to prevent it.

### WS2 — One decoder

Make `decodeInlineMarkers` the single position-invariant decoder (independent
open/close token substitution — the `«P»` / `«CTR»` rule, no `(.*?)` span-match).
`formatCell` / `renderTitleMarkers` / `applySizeMarkers` / `applyMarkers` collapse
into it; the only legitimate variation is escape-or-not on entry.  **Deletes** the
duplicate decoders and the span-match regexes.

**Verify.** Every marker renders identically across body / cell / caption / title
/ legend — the context-leak class disappears by construction.

### WS3 — Placement carried, not reconstructed

Producer carries paragraph boundaries (`«P»` exists) and emits block markers
already delimited as their own blocks, so the viewer renders the stream in order
without scanning.  **Deletes** `BLOCK_MARKER_SCAN_RE`, the mixed-paragraph split,
the non-greedy repair, `isContinuation`.  Trickiest; depends on WS1–2 and clean
producer block structure — do last.

### WS4 — Delete dead legacy

After a clean rebuild confirms **zero `{{TABLE}}`** in output, delete the
`{{TABLE}}` / `{{TABLEH}}` decoder, `parseTableCell`, `tableCellHtml`,
`TABLE_CELL` grammar, and `scaleDisplayMath`.  Have the producer carry the chem
table's class so `mergeTableClass` dies entirely.

### WS5 — CSS audit

Reduce remaining CSS to mechanical defaults + carried styles.

---

## Definition of done (the meter)

- No heuristics in the viewer: no `<60`-char gate, no Roman-prefix guess, no
  case-transition spacing, no dehyphenation, no "is this a heading" decision.
- Regexes touching the marker stream are **only** token→tag substitutions + pure
  text utils (slug / url / latex) — the no-regex keystone.
- One inline-marker decoder; no per-context copies.
- The viewer never decides *where* content goes.
- viewer.html line count down by roughly a third to a half.

# Britannica Edition — Status

**Last updated:** 2026-05-17.  Single source of truth for project state.  Snapshot
audit reports live in `docs/reports/`; long-form per-topic notes live in the
agent's memory directory and are not duplicated here.

---

## Current focus (2026-05-17) — Phase A recovery shipped

The 2026-05-16 V2 deploy shipped marker-contaminated titles (`«B»X«/B»` in
the `title` field) plus a separately-broken xref resolver and contributor
linker — both downstream consequences of the same root cause.  Today's
Phase A recovery reverts the title contract and ships clean.

**Root cause:** an in-session edit to `_clean_extracted_title` kept the
`«B»/«I»/«SC»` formatting markers in the returned title so the viewer's
H1 could render typography.  Eight surfaces read `title` as plain text
(volume index, search, xref resolver, contributor linker, Meilisearch,
Reader's Guide, topics page, URL-slug builder); only the H1 was patched.
Every other surface either rendered raw `«B»` characters or failed
string-equality matching.  Net result: ~98% of titles displayed garbage
in the volume index, ~89% of cross-references unresolved (28,613 lost),
~70 contributors orphaned.

**Phase A fixes shipped today:**
- `detect_boundaries.py::_clean_extracted_title` — strips `«B»/«I»/«SC»`
  markers, returns plain title.  Single chokepoint.
- `detect_boundaries.py` multi-line bold extension — when first content
  line ends with `«/B»` and the next starts with `«B»`, the extractor
  joins them.  Fixes ROBESPIERRE, MAXIMILIEN FRANÇOIS MARIE ISIDORE DE
  (title's bold span spans two physical lines in source).
- `clean_pages.py::_convert_quote_runs` — applies quote-run conversion
  inside `<ref>...</ref>` blocks before masking, so italics in citations
  (`''Ency. Bib.''`) get marked correctly.  `stray_wiki_italic` 2,159 → 15.
- `tools/rebuild_all.sh` — quality report moved to Phase 6f (pre-deploy)
  for visibility.  Gate-style blocking deferred to a follow-up.
- 6 corrupted quality-report baselines deleted from
  `data/derived/quality_reports/` (post-stacked-DB-rebuild artifacts).
- `data/contributor_aliases.json` — three pairs added so `_clean_name`
  collapses them on next rebuild: Lawrence F. Abbott / Laurence Abbott
  (the one visible-on-page dup), H. Hamilton Fyfe / Hamilton Fyfe,
  Ralph Stockman Tarr / Ralph Stockman.  Only Abbott is currently
  visible (the others have one empty side).

**Tests recovered:** the 2026-05-16 boundary rewrite broke 24 unit tests
(fixtures fed raw `'''X'''` to `detect_boundaries`, which now consumes
cleaned `«B»X«/B»`).  Plus 9 regression/integration tests in the same
fixture-shape family.  All 33 updated to call the real
`_convert_quote_runs` before passing to the boundary parser.  Test
suite is back to being a real signal: 286 passing, 8 remaining red —
each one a documented production bug (image-legend extraction +
chemistry layout), not a stale fixture.

---

## Last full rebuild

**2026-05-17 — Phase A recovery deployed to britannica11.org.**
- 36,671 articles (+8 vs 2026-05-14 baseline)
- 31,815 xrefs resolved (vs 31,954 baseline — close to parity)
- 5,219 xrefs unresolved (vs 5,131 baseline)
- 0 titles contain `«B»/«I»/«SC»` in the JSON `title` field
- stray_wiki_italic: 15 (was 2,159 yesterday, 2 on 2026-05-14)
- stray_close_braces: 9 (unchanged from baseline)
- 1,501 contributors created, ~48 unlinked after Phase 3b → ~7 after Phase 3b2

---

## Queued (next session)

- **Phase B**: restore H1 typography via a `title_html` field rendered at
  export time in Python, emitted alongside plain `title` in the article
  JSON.  Single chokepoint (Python), every JS surface drops `title_html`
  into innerHTML.  No marker contamination, no per-surface helpers.
- **Captioned-figure producer bug — Phase 1** — defer until after the
  next clean rebuild.  Producer-bug pool = STRANDED + BLOCK_LAYOUT +
  float-wrapped refs = **2,226 corpus-wide**.  Adjacency audit
  (`tools/_scratch/audit_caption_patterns.py`) classified the pool by
  position of the nearest caption-shape text (`Fig./Plate/{{sc|Fig}}`):

  | Bucket | Refs | % | Notes |
  |---|---:|---:|---|
  | **GLUED_BR**    | 580 | 26% | `<br>`-glued caption directly after the ref |
  | **PARA_AFTER**  | 158 |  7% | Caption in next paragraph (existing EXTCAP path broken on template-wrapper closers) |
  | **PARA_BEFORE** | 160 |  7% | Caption on line(s) BEFORE the file ref |
  | ELSEWHERE       | 605 | 27% | Caption within 400 chars but not adjacent — mostly figure + wikitable-with-caption-header-row pattern |
  | NONE            | 723 | 33% | No caption-shape detected — mostly maps, chem-formula-as-content, article-start figures |

  **Phase 1 scope:** the first three buckets, 898 refs (40% of pool).
  Extend the IMAGE element's EXTCAP intake to:
    1. Accept `<br>`-glued captions directly after the file ref
       (GLUED_BR).
    2. Fix the existing PARA_AFTER intake so a caption wrapped in a
       template with trailing `}}` (outer-wrapper closer) doesn't
       trip the match regex.
    3. Accept captions on the line(s) immediately before the file ref
       (PARA_BEFORE — new direction).
  Wrapper templates to consume (small fixed set): `{{sc|Fig.}}`,
  `{{Fs|…|…}}`, `{{Fine block|…}}`, `{{EB1911 Fine Print|…}}`,
  `{{center|…}}` / `{{c|…}}`, bare prose `Fig. N.—…`.

  **Phase 2 (separate work):** ELSEWHERE bucket = 605 refs of
  figure-then-wikitable-caption-row patterns.  Either teach the
  wikitable extractor to bind its `|+` row as caption for an adjacent
  preceding figure, or teach IMAGE to look ahead into the next
  wikitable.  Own audit first.

  **Phase 3 (defer indefinitely):** NONE residual = 723 refs.  Mostly
  legitimately captionless.  Article-title-as-caption for maps is a
  separate design question, not a producer fix.

  Per `[[feedback_diagnostic_first_recipe]]`: pre-fix HTML snapshot
  of ~50 known-captioned-figure articles (ACCUMULATOR, BREWING,
  ORDNANCE, STEAM ENGINE, FLUTE, OBOE, CATACOMB, BRACHIOPODA, BOOK
  BINDING, …) BEFORE any code change.  Post-fix diff should show
  changes only on refs the audit classified into one of the three
  Phase 1 buckets; anything else changing is a regression.
- **Fast-mode rebuild_volume actually fast** — defer until after the
  next clean rebuild.  Current "fast" mode (vol 1) takes 174s vs
  production full mode at 180-240s — savings is only ~30s, so fast
  mode doesn't deserve its name.  Two structural fixes land it in a
  meaningfully different speed class:
  1. **UPDATE articles in-place** instead of DELETE+INSERT.  Same
     article rows, new body field.  Saves ~26s of DB wipe overhead.
     Cleanest match for the fast-mode use case (iterating on
     transform/export code without disturbing detected articles).
  2. **Parallelize transform_articles and export_articles_to_json**
     across CPU cores.  Both are per-article-independent.  Saves
     ~80-100s combined (transform 75s → ~10s, export 52s → ~6s on 8
     cores).  Same parallelization helps full mode (classify, xref,
     image, contributor stages all per-article-independent too).
  Combined effect: fast mode ~30-40s, full mode ~60-90s.  The
  "30-90s per volume" claim in `rebuild_volume.py`'s docstring then
  becomes honest.  (Skipping boundary detection on a heuristic was
  considered and rejected — too magical.)
- **rebuild_all.sh viewer-deploy enumeration** — defer.  The deploy
  phase has ~25 individual `aws s3 cp tools/viewer/FOO.html s3://…/FOO.html`
  lines; each new viewer file requires editing the list, and the list
  will silently drift from the actual `tools/viewer/` directory.
  Already caused a near-miss this session — `typeahead.js` would have
  404'd in prod if I hadn't noticed before the deploy phase ran.  Same
  catch-all-by-enumeration anti-pattern; structural fix is a single
  `aws s3 sync tools/viewer/ s3://britannica11.org/` with appropriate
  `--exclude` patterns (mirrors the `data/articles` sync a few lines
  above).  Per `[[feedback_dont_grow_catchalls]]`.
- **Shared viewer page shell** — defer.  Every viewer HTML page
  (`home.html`, `index.html`, `viewer.html`, `contributors.html`,
  `topics.html`, `ancillary.html`, and friends) duplicates its
  `<head>`, the `:root` CSS variable palette, the nav bar, and the
  script-loader IIFE that pulls in `article-urls.js` /
  `search-api.js` / `typeahead.js`.  Every color tweak or nav link
  addition touches N files; drift surfaces as inconsistent styling
  and the kind of "this works on index but not home" bugs the
  typeahead extraction surfaced.  Structural fix: a shared shell —
  either a tiny build-time partial included by every viewer page,
  or a runtime `viewer-shell.js` that injects `<head>` content +
  nav + script tags at load time.  Same anti-pattern as the
  typeahead duplication we just collapsed; same recipe applies.
  Per `[[feedback_dont_grow_catchalls]]`, treat each "add this
  small thing to all N files" diff as a smell.
- **`_transform_text_v2` decomposition** — defer until after the next
  clean rebuild.  Same catch-all anti-pattern as the old `clean_body` /
  `clean_pages`, just at a lower level: ~430 lines of template-name-
  specific preprocessing piled before `process_elements`, plus the
  `_strip_templates` allowlist regex (`IMG:|IMG-INLINE:|TABLE|VERSE:`)
  that grows every time we add a marker.  Recipe: name each pre-pass
  for the structural thing it does (`promote_inline_glyphs` is the
  shape), push template-specific knowledge into the element that owns
  it, drive `_strip_templates`'s catch-all to zero.  See
  `[[feedback_no_catchall_cleanup]]` and
  `[[feedback_dont_grow_catchalls]]`.
- **Contributor-dedup gate — LANDED 2026-05-17.** Shipped as a gate, not
  a fixer (per `[[feedback_db_writes_evaporate]]`).  `dedup_contributors.py`
  gains a `--report` mode (threshold default 0.85, JSON output);
  `aliases.json` gains a `distinct` list for acknowledged-different
  people; `tools/diagnostics/check_dedup_candidates.py` is a new
  pre-deploy gate that filters the report against `aliases` + `distinct`
  and exits 1 on any unreviewed candidate.  Wired as Phase 6g in
  `rebuild_all.sh`.  Current state: 11 raw candidates → 3 covered by
  aliases (collapse on next rebuild) + 8 in distinct → 0 unreviewed.
- **Pre-deploy quality gate** with hard thresholds + a title-shape check
  (`«` in any title → abort) + a (vol, page)-level pair diff against
  baseline.  Currently the quality report runs pre-deploy but doesn't
  block; harden it into a gate.
- **Architectural cleanup**:
  - **Inline-image rendering — LANDED 2026-05-17.**  Source convention
    `[[File:X|14px]]` mid-prose was rendering as a 600px-cap block
    figure, breaking ~337 corpus refs (Hebrew/Phoenician alphabet
    glyphs in vol 1 p774, the article on the letter A's 5 ornamental
    initials, similar inline glyphs scattered across letter articles
    and tag/ornament references).  New
    `elements/_inline_glyphs.py::promote_inline_glyphs` runs as a
    pre-pass to element extraction in `_transform_text_v2` and rewrites
    only the INLINE_GLYPH bucket — refs with no caption, no layout
    keyword, outside any wikitable, and in prose-line context — to a
    new `{{IMG-INLINE:filename|size}}` marker.  The other ~10,000 file
    refs (CAPTIONED 569, BLOCK_LAYOUT 2,631, TABLE_FIGURE 5,431,
    STRANDED 1,128, CHEM_BRACKET 210) continue through their existing
    paths unchanged.  Viewer renders the new marker as a true inline
    `<img>` with `vertical-align:middle` and the source-specified size
    (`Npx`, `xHpx`, `WxHpx`, or 1.2em default).  Routing buckets were
    established by exhaustive corpus audit in
    `tools/_scratch/audit_image_routing.py`.  Catch-all template
    stripper in `body_text.py::_strip_templates` allowlist updated to
    pass `IMG-INLINE:` alongside the existing `IMG:`, `TABLE`,
    `VERSE:`.
  - **8 pre-existing test failures resolved — LANDED 2026-05-17.**  All
    were test-harness bugs, not production bugs.  7 of 8
    (`test_image_layout_unwrap.py::test_*`) called `_transform_text_v2`
    directly on raw wikitext, but production runs `_convert_quote_runs`
    upstream in `prepare_wikitext` first.  Without that pre-pass,
    `'''italic'''` markers stay raw and the legend extractor's
    `_MULTICOL_FULL_ENTRY_ITALIC_RE` regex (which keys on `«I»…«/I»`)
    silently fails — producing the wrong test fixture output even
    though the underlying production articles
    (SPONGES/HYDROMEDUSAE/Abbey) render correctly.  Fix: 12-line
    wrapper in the test file that mirrors the production call shape
    (`_convert_quote_runs` → `_transform_text_v2`).  Zero production
    code changes.  The 8th (`test_fulminic_acid_competing_formulae`)
    was a stale assertion: the test expected `"Langle"` filename
    string preserved, but the chemistry processor has been correctly
    rendering it as the `❮` Unicode glyph for some time — assertion
    updated to match.  Tests: 294 passing, **0 red**.  Diagnosis
    process followed `[[feedback_verify_the_counter]]`: an earlier
    "fix" that mutated `_clean_legend_text` to strip `''` and HTML
    `<i>` tags appeared to fix 6 tests, but verification against
    production showed the affected articles already rendered
    correctly — the change was a test-side mirage with regression
    risk to the working mass.  Reverted, then dug deeper to find the
    real cause (the test harness, not production).
  - **`clean_pages` → `prepare_wikitext` rename — LANDED 2026-05-17.**
    The module/function name `clean_pages` was a holdover from when
    the stage did 13 different cleanup ops; after today's tightening
    it does exactly two things — `apply_corrections` + quote-run
    conversion — and "cleans" nothing in any general sense.  Renamed
    file `src/britannica/pipeline/stages/clean_pages.py` →
    `prepare_wikitext.py`, function `clean_pages(volume)` →
    `prepare_wikitext(volume)`, CLI command `britannica clean-pages`
    → `britannica prepare-wikitext`.  Updated all imports (CLI,
    transform_articles comments, body_text comments, corrections
    module docstring, img_float docstring, reprocess_article), all
    11 test files that imported `_convert_quote_runs`, renamed
    integration-test file `test_page_cleanup_pipeline.py` →
    `test_prepare_wikitext.py`, and updated the two active shell
    scripts (`tools/rebuild_all.sh`, `tools/db/rebuild_volume.sh`).
    Tests: 286 passing, same 8 pre-existing reds.  Disposable
    `tools/_scratch/*.sh` left untouched.  Earlier LANDED entries
    in this file still reference `clean_pages` to describe the
    pre-rename state accurately.
  - **SCORE → content-addressable element — LANDED 2026-05-17.**
    `<score>` handling lived as a pre-extraction pass in
    `clean_pages.py` (then briefly in `elements/_score.py`) because
    `SCORE_IMAGES` was keyed by `(volume, page, occurrence_index)` —
    treating SCORE as a positional element.  But the upstream Commons
    URL is a content-hash of the LilyPond source, not position-based;
    the keying was an implementation choice, not an architectural
    necessity.  Rekeyed all 11 entries by whitespace-normalized
    LilyPond content; `_leaf._process_score` now does a single dict
    lookup like `_process_math` and is reached as a normal post-extract
    element handler.  Deleted: `elements/_score.py`,
    `_replace_score_tags` entirely (it was the pre-extraction pass),
    `SCORE_TAG` regex from `image_assets.py`, the pre-extract
    registration in `_ELEMENT_HANDLERS`, the call site in
    `transform_articles/__init__.py:497`.  Smoke-tested: all 8 score
    tags across vol 3 p221 + vol 6 p416 resolve to their original
    URLs.  Tests: 286 passing, same 8 pre-existing reds.
  - **Editorial Preface → source-regenerated static HTML, full
    ancillary decoupling — LANDED 2026-05-17.**  New build script
    `tools/viewer/build_preface.py` reads vol 1 ws pages 10-23
    `raw_text` (not `cleaned_preview` — see below), applies
    `corrections.json`, converts wikitext to static HTML, writes
    `tools/viewer/preface.html`.  Joins all four ancillary builders
    in Phase 6d of `rebuild_all.sh` (`build_about_page.py`,
    `build_ancillary_pages.py`, `build_preface.py`).  Mirrors the
    article pipeline's marker semantics so output matches what the
    JS renderer would have produced if its input were correct.

    **Bugs fixed vs the old `export_front_matter.py` → JS path:**
    * **Wrong content range.**  The old export read pp.6-23 corpus-
      wide and glued the Prefatory Note (pp.6-9) onto the Editorial
      Introduction (pp.10-23).  Production has been showing both
      stuck together for the entire site's history.  New build reads
      pp.10-23 only; Prefatory Note stays in
      `ancillary-prefatory-note.html`.
    * **Missing opening sentence.**  The print's first paragraph
      begins "In the Prefatory Note the history of the production
      of the successive editions of the Encyclopædia Britannica has
      been briefly told; and elsewhere in these volumes…" but the
      Wikisource transcription drops this clause and starts at
      "Elsewhere…".  Confirmed against live Wikisource — same gap
      there.  Patched via `corrections.json` `"1:10"` (adds the
      missing clause, rebases the drop-cap from "E" to "I").
    * **Lost footnotes.**  The old path read `cleaned_preview`
      which captured only some `<ref>…</ref>` tags.  Building from
      `raw_text` keeps both footnotes intact.  Wired the same
      `id="fnref-N"` / `scrollIntoView` back-navigation the article
      viewer uses so footnote-list clicks return to the in-body
      anchor.
    * **Bold-italic shoulders.**  The old `cleaned_preview` stripped
      `'''` bold markers from SH content (italic-only via CSS); the
      raw-text build was emitting `<b>` inside `<span class=
      "shoulder-heading">`.  Now strips B markers to match.
    * **Lost spaces, mid-word soft hyphens, em-space entities,
      double periods, SH-broken paragraph flow** — each fixed; mirror
      the JS / fetch-pipeline transformations precisely (HTML space
      entities → space; `<br>` → space; `- ` removal joins
      soft-hyphenated words; SH content in margin via paragraph-
      merge so prose flows continuously around it).
    * **Wikilinks rendered.**  `[[w:X|Y]]` → Wikipedia anchor,
      `[[Author:X|Y]]` → `/contributors.html?q=Y`.  Production's
      `cleaned_preview` stripped these to plain text; restored as
      proper clickable links.

    **Decoupling work:**
    Deleted `tools/pipeline/export_front_matter.py`,
    `clean_for_front_matter`, the `clean_pages` compatibility
    orchestrator, the `cleaned_text` column from `SourcePage`, the
    Phase 5 export step from `rebuild_all.sh`, the dead
    `dedication.body` export, `cleaned_text=None` initialisers in
    the CLI / importer / test conftest, and the obsolete
    `test_page_cleanup_pipeline` assertions (replaced with a
    quote-run-conversion check on `wikitext`).  `clean_pages.py` is
    now ~180 lines doing one job: typo corrections + quote-run
    conversion on `page.wikitext`.  Tests: 286 passing, same 8
    pre-existing reds.  Production stays broken until the new
    `preface.html` is uploaded on the next deploy.  Follow-up: drop
    orphan `cleaned_text` column from local DB with
    `ALTER TABLE source_pages DROP COLUMN cleaned_text;` when
    convenient.
  - **`clean_pages` split — LANDED 2026-05-17.**  Replaced the 539-line
    catch-all with two narrow public entries.  `clean_for_articles`
    (~10 lines) does only typo corrections + quote-run conversion on
    `page.wikitext`.  `clean_for_front_matter` (~14 lines) does the
    six prose-cleanup ops (unicode, print artifacts, headers,
    hyphenation, reflow, whitespace) on `page.cleaned_text` consumed
    by `export_front_matter.py`.  `clean_pages` is now a compatibility
    orchestrator calling both.  Deleted ~280 lines of article-shaped
    catch-alls from the front-matter path (`_clean_plate_layout`,
    `_convert_img_float`, `_clean_leaked_table_markup`,
    `_fix_unclosed_footnotes`, `_fix_unclosed_tables`, plus
    stray-control-char / residual-`''` substitutions).  Audit verified
    these produced IDENTICAL output on the 19 pages
    `export_front_matter.py` actually consumes (Vol 1 pp.5-23 —
    dedication + editorial preface) — they were dead weight running
    against article-pipeline data the front-matter export never reads.
    Tests: 286 passing (same 8 pre-existing reds).  Idempotency check
    on Vol 1: 1028/1029 pages byte-identical when rerun (the 1 diff
    is a pre-existing quirk in `_convert_quote_runs`).
  - Decompose `detect_boundaries.py` (~900 lines): letter-article handler,
    bold extractor, glue check, fallback path → each its own module
    with focused tests.
- **Inline images rendered as block** — corpus-wide bug.  Source has
  `[[File:foo.svg|14px]]` mid-prose (letter articles use these for
  variant glyphs of A/B/C in Phoenician, Greek, Latin scripts; ARENIG
  GROUP and similar use them for taxonomic ornament).  Pipeline strips
  the size hint (`_image.py:34` skips `\d+px` parts) and wraps the
  resulting `{{IMG:fn}}` with `\n\n`, turning inline images into
  standalone block-level images at default size.  Fix is multi-file:
  preserve size in `_process_image` (and the ~10 other IMG-emit sites
  in `_layout.py`/`_tables.py`/etc.); extend marker schema to
  `{{IMG[size=14px]:fn|caption}}` mirroring `«MATH[fs=N]:`; stop the
  `\n\n` framing for inline images; teach the viewer to render the
  size-hinted form inline.

- **Letter-article simplification — LANDED 2026-05-17**.  Replaced
  ~70 lines of brace-walker + body-keyword check with ~25 lines of
  regex + brace-aware helper.  Validated 26/26 on corpus (one per
  letter A–Z), zero false positives.  See
  `tools/_scratch/verify_letter_articles_simplified.py`.

- **Missing-image audit honest + djvu refs normalized — LANDED 2026-05-17**.
  `find_missing_images.py` reported 14 misses but 10 were `EB1911 -
  Volume N.djvu/NNN` page-leaf refs whose canonical local form
  (`djvu_volNN_pagePPPP.jpg`) was already on disk — the audit just
  didn't apply the djvu normalization that `transform_articles` does
  to article bodies.  Two fixes: audit imports `_normalize_djvu_page_refs`
  before checking on-disk (14 → 4); `extract_images.py::_parse_image_ref`
  and `_parse_img_float` normalize before storing so `images[*].filename`
  matches what's on disk and what body markers already say.  Remaining
  4 were genuine Commons files never fetched on the last
  `download_images.py` run; all 4 downloaded locally (will reach S3 on
  next deploy).  Audit now reports 0.

---

## Known issues (open)

- **Bare-label legend bundling** — SPINAL CORD (vol 25 Fig 3) / MALLOW (vol 17
  5-part botanical legend).  Single-bare-label paragraphs render as body prose;
  needs a figure-pass that collects consecutive single-entry paragraphs.
  Styling, not content loss.
- **Two-column legend variants — RESOLVED for canonical cases 2026-05-15.**
  The MULTICOL_LEGEND layout subclass now handles multi-row continuation
  entries via column-major reconstruction (ARACHNIDA Figs 7, 12, 14, 47,
  54, 65 all clean).  Trailing single-cell colspan annotations break the
  legend at the right boundary; pre-existing LEGEND blocks are preserved
  through the figure walker so trailing credits still fold into the IMG
  caption.  Remaining sub-patterns within the same systemic class:
    * **`rowspan=N` continuation cells** (ARACHNIDA Fig 31) — col-1 cell
      spans 2 rows of col-0; the rowspan row has only one source cell so
      legend parsing terminates early.  Need rowspan-aware row expansion
      before column-major build.
    * **Prime-marked labels** (`7′`, `I′ to V′` — ARACHNIDA Fig 47) —
      `_MULTICOL_FULL_ENTRY_RE` doesn't accept prime characters in the
      label, so labelled-with-prime cells get folded into the prior entry.
      Extend label regex to include `′″‴` etc.
    * **Hanging-indent entries in wide-column cells** (ARACHNIDA Fig 26)
      — legend laid out as one `{{Hi|1em|…}}`-wrapped entry per template,
      multiple per cell, no `||` separator.  Different shape from the
      standard 2-col legend; needs its own detector that walks `{{Hi}}`
      templates as legend entries.
    * **Side-by-side image cells losing caption + legend** (ARACHNIDA Figs
      57–58, BAG-PIPE vol 3 p221) — two figures laid out in a 2-column
      wikitable, each cell containing `[[File:…]]` (or `<score>`) +
      caption + `<br>`-stacked legend; pipeline lifts the IMG markers
      but drops the cell text and leaks the TABLE marker.  Sackpfeife /
      Bock / Schäferpfeife / Hümmelchen image labels lost, and the
      chalumeau-scores table renders as raw `{{TABLE:…}TABLE}` text.
      Distinct extraction-time issue.
- **Fig 7 editorial note in trailing PRE** — a wikitable that follows the
  figure containing an editorial annotation `[According to the system…]`
  classifies as PRE; the figure walker doesn't recurse into PRE for an
  enclosed credit line.  Both an extraction-time classification miss
  (the trailing wikitable's actual structure is annotation + credit)
  and a walker miss.
- **BRITISH EMPIRE India-acquisitions table** — multi-line cell continuation
  + `|+` caption attribute leak; separate single-article residual.
- **`{{c|…}}` Roman-numeral subsections** (24 articles) — flatten to inline
  prose; no clean single-block distinguisher, only Roman-numeral progression
  across blocks.
- **Tall-brace taxonomic grouping** — print-typographic device using a tall
  `\left\{ \begin{matrix} \\ \end{matrix} \right .` (no math content, pure
  ornament) to group preceding-or-following items as members of a single
  category.  Currently renders as a stray vertical brace splitting the
  surrounding prose.  Examples: ARACHNIDA (Eurypteromorpha sub-orders;
  scorpion families with Carboniferous bracket), ARENIG GROUP, ATMOSPHERIC
  ELECTRICITY — ~8 instances corpus-wide.  Real fix: detect the
  empty-matrix brace pattern, parse the grouped items, emit as an OUTLINE
  block.  The outline renderer is general-purpose and we underexploit it;
  this is one of several patterns that ought to route there.
- **IMG-caption credit-glue missing space** — when a figure's descriptive
  caption and its `(From …)` credit live in the same source cell separated
  only by structural markup that gets stripped (`{{center|{{Fs|N%|…}}}}`,
  `<br>`, etc.), the IMG caption emerges with `).(From X)` — no space at
  the join.  Sample: ARACHNIDA Figs 13, 63, 74.  Narrow extraction-time
  fix: normalise `.(` → `. (` when assembling the caption (in
  `clean_caption` or the caption-build path of the layout subclasses).
- **Italic-marker inversion (residual)** — pre-existing class.  Post-Phase-A
  `stray_wiki_italic` counter is at 15 (vs baseline 2 on 2026-05-14, and a
  catastrophic 2,159 on the broken 2026-05-16 V2 deploy).  Ref-internal
  italics fixed today; the remaining 15 are the unfixed pre-existing edge
  cases in the 5-quote bold-italic handler.
- **8 unit-test failures** = 8 documented production bugs:
  - 7× `test_image_layout_unwrap.py` — the legend-extraction sub-patterns
    listed above (rowspan, prime marks, hanging-indent `{{Hi}}`,
    side-by-side image cells, sponges/hydromedusae figures).
  - 1× `test_elements.py::test_fulminic_acid_competing_formulae` —
    chemistry-layout doesn't emit `«CHEM:` marker for the
    competing-formulae 2-D table shape.
- **Contributor duplicates (1 visible, 2 invisible)** — Abbott pair
  visible on contributors page; Fyfe + Stockman pairs have one orphan side
  filtered out of the contributors page.  All three queued for merge via
  `data/contributor_aliases.json` on next rebuild.
- **Lower priority:** ~7 unlinked contributors after Phase 3b2 (down from
  ~88 in yesterday's broken deploy); ~3,633 unproofread Wikisource pages;
  Meilisearch port 7700 open to all (should be CloudFront-only).

See `docs/reports/` for historical audit snapshots.

---

## Overview

A scholarly digital edition of the 1911 *Encyclopædia Britannica* — the first
hyperlinked, searchable, fully annotated edition with proper rendering of Greek,
Hebrew, hieroglyphics, mathematical notation, chemical formulas, footnotes,
images, verse quotations, and contributor attribution.  Live at
**britannica11.org**.

---

## Architecture

### Boundary detection

Article boundaries are determined by `<section>` tags in the Wikisource
wikitext — not heuristic heading detection.  Plate pages are split off first
in a stateless PASS 1 (`_split_out_plates`), then the article state machine
runs over the plate-free pages in PASS 2.

### Element pipeline

Extract-process-reassemble per segment (`pipeline/stages/elements/` +
`transform_articles/_transform_text_v2`):

1. Wiki tables (balanced matching) → HTML elements (ref, html_table, poem,
   math, score) → wiki markup (image_float, image).
2. Each element processed recursively.
3. Body text transforms (~11 explicit functions: hieroglyphs, links, content
   templates, small caps, shoulder headings, layout templates, sub/sup,
   bold/italic, strip templates, strip HTML, decode entities).
4. Reassembly with `\x01PAGE:N\x01` markers.

### Marker formats (internal)

| Marker | Meaning |
|---|---|
| `«B» / «I» / «SC»` | Bold / italic / small caps |
| `«LN:filename\|target\|display«/LN»` | Resolved link |
| `«LN:target\|display«/LN»` | Unresolved link (falls back to search) |
| `«MATH:…«/MATH»` | LaTeX, plain |
| `«MATH[fs=N]:…«/MATH»` | LaTeX, render at N% font-size |
| `«MATH[popout]:…«/MATH»` | LaTeX, render click-to-pop-out link |
| `«FN:…«/FN»` | Footnote |
| `«HTMLTABLE:…«/HTMLTABLE»` | Complex table preserved as HTML |
| `«CHEM:…«/CHEM»` | Chemistry valence-bracket grid |
| `«PRE:…«/PRE»` | Preformatted block |
| `«SH»…«/SH»` | Shoulder heading |
| `{{TABLE:…}TABLE}` | Wiki-table block |
| `{{VERSE:…}VERSE}` | Verse block |
| `{{LEGEND:…}LEGEND}` | Figure-legend block |
| `{{IMG:filename\|caption}}` | Image with caption |

### Cross-reference resolution

Multi-strategy resolver: exact title, alias table, plural/singular, name
inversion, trailing article/period, qualified prefix.  Resolved targets are
rewritten as direct links at export time so the viewer routes to
`/article/{page}/{slug}` instead of search.

### Stack

Python 3.12, SQLAlchemy, Typer, Postgres, Meilisearch, KaTeX, Playwright (for
math measurement).  pytest (265 tests).

---

## Pipeline phases (`tools/rebuild_all.sh`)

1. Truncate DB, clear exports.
1b. Build contributor table.
1c. Apply vol 29 contributor linker.
2. Per-volume: import → clean → detect boundaries → transform → classify →
   extract xrefs → resolve xrefs (intra-vol) → extract images → extract
   contributors → export.
3a. Resolve xrefs across all volumes.
3b. Link contributors from front matter.
3b2. Link vol 29 article attributions.
3c. Rebuild printed-page mapping.
4. Re-export (with cross-vol xrefs resolved).
**4b. Measure math widths (refresh scale-hint cache).**
**4c. Annotate math markers from refreshed cache.**
5. Export front matter.
6b. Parse classified TOC; 6b2. apply cached disambiguations; 6c. detect fm
   first-content pages; 6d. rebuild generated site pages; 6e. build Reader's
   Guide.
7. Deploy (S3 sync articles + images + scans + JSON + viewer; CloudFront
   invalidate; index search on EC2).
8. Quality report.
9. Deploy preflight (check_deploy_refs.py).

---

## Scripts

- `tools/rebuild_all.sh` — full corpus rebuild + deploy (`--no-deploy` for
  local-only).  ~2 hours.
- `tools/pipeline/rebuild_volume.py <vol> <TITLE>` — rebuild a volume
  targeted at one article.  Fast (in-process) by default; `--full`
  wipes source + re-imports + runs all stages; `--deploy` uploads
  the article JSON to S3.
- `tools/render_article.py <TITLE>` — re-render one article from existing DB
  state (~3 s).  Fastest iteration loop.
- `tools/diagnostics/quality_report.py` — body-wide metrics (run before every
  deploy).
- `tools/diagnostics/measure_math_widths.py` — refresh math-width cache.
- `tools/pipeline/annotate_math_markers.py` — re-annotate exported MATH
  markers from refreshed cache.
- `tools/deploy_html.sh` — upload viewer HTML + invalidate CloudFront.
- `tools/pipeline/start_services.sh` — start/stop local Postgres, Meilisearch,
  web server.

---

## Data model

`Article` (title, volume, page range, body, article_type, section_name) ·
`ArticleSegment` (text ↔ source page) · `CrossReference` · `ArticleImage` ·
`Contributor` · `ArticleContributor`.  Stable IDs: `{vol:02d}-{page:04d}-{slug}`.

---

## Viewer

- `home.html` — title-page landing.
- `index.html` — volume tabs, title / full-text / contributor search,
  alphabetic navigation.
- `viewer.html` — articles with volume:page citations, shoulder headings,
  images, footnotes, tables (inline + complex), TOC, in-article search,
  KaTeX math (with fs= scaling + popout modal for wide expressions),
  bold/italic/small-caps/hieroglyph rendering, direct cross-reference
  links.
- `search.html` — Meilisearch full-text, exact-substring filter, dedup,
  match-count sort, per-occurrence links to `viewer.html?…&match=N`.
- `contributors.html`, `preface.html`, `topics.html`, `ancillary*.html`,
  `readers-guide*.html`.

---

## Production

- **britannica11.org** — single S3 bucket + CloudFront (dist
  `E24BJKH0IB4I6`).  CloudFront function `article-rewrite` maps
  `/article/{page}/{slug}` → `viewer.html`; `strip-search-prefix` proxies
  `/search-api/*` to Meilisearch on EC2.
- **Meilisearch** — Docker on EC2 `t3.small`
  (`ec2-44-222-119-72.compute-1.amazonaws.com`), port 7700.
- **Raw wikitext** backed up to `s3://britannica11.org/raw/` (28 zips, 139 MB).
- **IA page scans** — 29 volumes (~30 GB), `data/raw/ia_scans/`.

---

## Topics page (Vol 29 classified TOC)

Category-bounded OCR (`tools/ocr_vol29_classified.py`) +  two-phase walker
(`tools/parse_classified_toc.py`).  23,050 articles across 24 categories.
Per-cat refinement: edit `data/derived/cat_ocr/<slug>.txt` or rerun
`ocr_vol29_classified.py --only='<Cat>'`.  Ambiguity disambiguation via
Haiku batch (`tools/vol29/disambiguate_toc.py`), cached.

---

## File / directory conventions

- `tools/_scratch/` — disposable.  Promote keepers to `tools/diagnostics/`
  with a real name and docstring.
- `data/corrections.json` — source-text typos by `vol:page`; never edit raw
  wikisource page JSONs directly.
- `docs/reports/` — dated snapshot audit reports.
- `docs/status.md` — this file.  Source of truth for current state.

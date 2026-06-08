# Two transform places: the title / page / byline fold

## Principle

Text is transformed in exactly two *categories* of stage, nowhere else:

1. **Preprocessing** — minimal, raw-source. Two scopes:
   - `preprocess` (corpus stream, before slicing)
   - `preprocess_article` (per article, after slicing) — **NEW**
2. **Producers** — `process_elements` (the walk): recognize structure, produce the tree.

Everything that is not a content transform is either **recognition** (the walk
recognizes a marker the source already carries) or **decoration** (a corpus-wide
post-walk pass that enriches the assembled body). Neither is a third transform place.

A "transformation" means *changing the text* — adding a bracket counts. So the
title bracket is a transform and must live in a transform stage; PAGE and the
byline footer are named templates and must be **recognized**, not transformed.

## Target pipeline

```
preprocess (corpus)
  → detect_boundaries (slice into articles + per-page segments)
  → preprocess_article (per article: assemble text, stamp «TITLE», NOTHING else)
  → process_elements (walk → tree; recognize PAGE + CONTRIBUTOR_FOOTER)
  → assemble (in-memory corpus)
  → decorate [ xref module, contributor module ]
  → serialize (export reads the tree)
```

Gone: `_transform_text_v2`, `produce_article`.

## The four rehomings

### 1. TITLE → stamp in `preprocess_article`
`preprocess_article` is the one stage with BOTH `beginning`+`once` (it runs
per-article — the article *is* the unit, there's no "first" to hunt) AND
legitimacy (it's preprocessing). The chop has the aids but isn't a transform
stage; corpus-`preprocess` is a transform stage but has no article boundary; a
producer has neither. It brackets the recognized title span as `«TITLE»…«/TITLE»`,
raw inner left intact for the walk. Kills the `title_raw` field, `title_display`,
the second walk, and the `title_display` gate (`produce_article` 189–191). The
span heuristic (`_title_span`, connective-gap logic) moves here.

### 2. PAGE → recognize in the walk
The raw already carries `{{EB1911 Page Heading|left|hw|hw|right}}`; the numeric
arg is the **printed** page number (flips left/right with verso/recto). Stop
stripping it in `preprocess`; stop stamping `\x01PAGE:N\x01` in the join. A
producer recognizes the template → a PAGE element. Bonus: the printed number is
in the template directly — the leaf→printed conversion via `printed_pages.json`
may drop out.

### 3. BYLINE / CONTRIBUTOR → ONE contributor decorator, handling it COMPLETELY
The footer's chronic leaking is a symptom of **partial handling** — split across a
pre-walk `strip_attributions` and (attempts at) a walker element. Both are partial;
both leak. **Do NOT make it a walker element** — a walker recognition is just another
partial layer, and partial = leaks (confirmed the hard way: recognizing only some
footer shapes while narrowing the strip left the footer leaking in every sampled
article).

The fix is to handle it COMPLETELY in ONE place: the **contributor decorator**
(corpus-wide, post-assemble). It comprehensively removes EVERY footer shape from the
body — `{{EB1911 footer …}}`, bare `{{EB1911 XX}}` sign-off, `{{right}}`/`{{float
right}}` signature, `{{Fs}}`-wrapped — AND owns the byline (read initials, resolve to
a name against the contributor list, build it). Consolidates the three scattered
pieces — `extract_contributors` (read) + `strip_attributions` (strip) + export byline
build — into one module. The decorator is the sole owner; nothing footer-related lives
in the walk or a pre-walk strip.

### 4. XREFS → centralize the decorator
Today the xref decoration is lifted halves inside the export (`_xrefs_from_body` /
`_link_xrefs_in_body` in `article_json`). Pull it into its own module so
`decorate` is a real phase with two symmetric modules (xrefs, contributors).

## The deaths (consequence, not action)

`_transform_text_v2` and `produce_article` are not deleted — they are **vacated**.
Once the four rehomings land, every job they hold has moved:
- `produce_article`: segment concat → `preprocess_article`; the walk →
  `process_elements`; PAGE stamp → recognition; title work → `preprocess_article`
  + the tree.
- `_transform_text_v2`: `strip_attributions` → contributor decorator; the second
  walk → gone; the body walk IS `process_elements`.

Nothing calls them. They fall off for lack of work.

## Discipline guard

`preprocess_article` is exactly the kind of stage that rots into the next
`_transform_text_v2`. Hard entry bar: **a thing earns a slot only if it is a
positional fact that provably cannot be recognized.** The title qualifies (no
template, only position). PAGE and the byline do NOT (named templates →
recognized). Keep it a one-occupant stage; a second occupant is a loud audit
flag, not a silent splatter.

## Order

Independent. The four rehomings can land in any order; the two functions vacate
once all four are home. Structural change → snapshot before, full rebuild as the
static target (the first clean rebuild doubles as the fresh baseline).

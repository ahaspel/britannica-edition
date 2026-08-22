# TEI-XML export — design

**Status:** design, awaiting sign-off.  Nothing built.  Written 2026-08-22 during
the rebuild; grounded in `src/britannica/export/markdown.py`,
`src/britannica/markers.py` and `src/britannica/render/article.py`, not in a
guess about what the marker vocabulary contains.

---

## 1. Why, and for whom

Readers have asked for it.  TEI (Text Encoding Initiative, P5 Guidelines) is the
interchange format for scholarly text encoding: it is what libraries, digital-
humanities projects and corpus tools actually ingest.  A JSON bundle does not go
into that infrastructure; TEI does.  The audience is small and institutional, and
it is the audience most likely to cite the edition rather than merely read it.

There is a second reason, internal to this project and probably the better one.
The bundle's current text export is `body_to_markdown`, whose own policy line
reads:

> presentation (SHED to content)  «SC» «CTR» «DIV[…]» «SPAN[…]» «FL» «FR»
> «MIRROR» and the size family «SM»/«LG»/«XS»/«XXS»/«XXL»/«FS»/«LH»

That is a flattener, by design and by necessity — Markdown has nowhere to put
small caps or centring.  So the download bundle currently violates principle 3
([[feedback_three_principles]]): we carry those distinctions all the way through
the walk and then drop them at the last step, for every consumer who takes the
text export.  **TEI is the first output format capable of carrying what we
already carry.**  It is not a new burden on the pipeline; it is the pipeline's
existing work finally reaching a reader.

## 2. Scope decisions (proposed)

* **TEI P5**, validated against a project ODD customisation.
* **`<div type="entry">` with `<head>`, NOT the dictionaries module.**  TEI's
  `<entry>`/`<form>`/`<sense>` is built for lexical entries — a headword, a part
  of speech, senses.  EB1911 articles are prose essays that happen to be
  alphabetised.  Encoding them as dictionary entries would assert a structure the
  source does not have, which is the imposed-taxonomy failure
  ([[imposed-taxonomy-is-negative-value]]).
* **One `<TEI>` document per article**, plus a `<teiCorpus>` manifest.  Per-volume
  documents were considered and rejected: articles are the unit that has a stable
  id, a URL and a contributor, and volume boundaries fall at article boundaries
  anyway ([[project_no_cross_volume_articles]]).
* **Ships in the existing download bundle** as a sibling of `articles.jsonl`, not
  as a separate product.

## 3. Where it sits

Three renderers, one tree:

```
walk_article  →  marker stream  ─┬─→  render/article.py    →  HTML   (the site)
                                 ├─→  export/markdown.py   →  MD     (the bundle)
                                 └─→  export/tei.py        →  TEI    (new)
```

**Off the marker stream, never off the HTML.**  A TEI writer that parsed our own
HTML would be a second answer to "what does this construct mean"
([[feedback_shadow_path_at_the_root]]), and would inherit every presentational
decision the site makes for screen reasons.

## 4. The totality contract

`export/markdown.py` states the lesson this design must inherit, having learned it
the expensive way — 8,140 raw markers shipped across 560 articles, including a
regex written for a form that had never existed:

> Totality is now grounded in the OUTPUT, not in a manifest: anything without a
> rule survives visibly and `tools/diagnostics/output_leaks.py` counts it.  The
> old claim of being "TOTAL by construction" over
> `RENDERED_GUILLEMET_MARKER_NAMES` was true and worthless — that constant
> omitted the very names this file had no rule for.

So: **do not ground TEI totality in the registry.**  Ground it in the output, and
take the second net XML gives us for free:

1. **Leak net** — an unhandled `«X»` survives into the XML as visible text;
   `output_leaks.py` gains TEI as a scanned output.
2. **Schema validation** — every article must validate against the ODD-generated
   RELAX NG.  This is a genuinely *independent* check: it catches structural
   errors (a `<cell>` outside a `<row>`, an unclosed `<hi>`, a duplicate
   `@xml:id`) that a leak scan cannot see, and it cannot be argued with.

Validation over all ~37,226 documents is the natural phase-7 gate, and it is the
kind of mechanical ratchet that has closed every class that had one.

## 5. The mapping

The marker vocabulary is 55 names.  Families below follow `markdown.py`'s own
policy list so the two can be diffed; **the "MD" column shows what Markdown does
today**, which is where the gain is visible.

### Structure

| marker | MD | TEI |
|---|---|---|
| `«P»` | `\n\n` | `<p>` |
| `«TITLE:…«/TITLE»` | dropped (title field) | `<head>` in the entry `<div>` |
| `«SEC:slug\|name»` | `## name` | `<div type="section" xml:id="slug"><head>name</head>` |
| `«SH:slug»…«/SH»` | `### …` | `<div type="subsection" xml:id="slug"><head>` |
| `«ANCHOR:slug\|name»` | dropped | `<anchor xml:id="slug"/>` — a target, not a heading |
| `«BR»` | space | `<lb/>` |
| `«DHR»`, `«DHRI»`, `«BAR»` | shed | `<milestone unit="rule" rend="…"/>` |
| page position (out of band) | — | `<pb n="311" facs="{scan url}"/>` |

`«SEC»`/`«SH»` nest as real `<div>`s rather than flat headings — TEI wants the
hierarchy, and we have it (level 1 / level 2, `export/sections.py`).

### Typography — everything Markdown sheds

| marker | MD | TEI |
|---|---|---|
| `«I»` / `«B»` | `*…*` / `**…**` | `<hi rend="italic">` / `<hi rend="bold">` |
| `«SC»` | **shed** | `<hi rend="small-caps">` |
| `«CTR»` | **shed** | `<hi rend="center">` (or `@rendition`, §8) |
| `«U»`, `«STK»` | `~~…~~` (STK) | `<hi rend="underline">` / `<hi rend="strikethrough">` |
| `«SS»` / `«SR»` | **`<sub>`/`<sup>` — WRONG, see below** | `<hi rendition="#sans">` / `<hi rendition="#serif">` |
| `«FL»` / `«FR»` / `«MIRROR»` | **shed** | `<hi rend="float-left\|float-right\|mirror">` |
| size family `«XXS» «XS» «SM» «LG» «XXL» «FS» «LH»` | **shed** | `<hi rendition="#size-…">` |
| `«DIV[style:…]»` / `«SPAN[…]»` | **shed** | `<seg rend="…">` carrying the style |
| `«BRACE2»` | shed | `<hi rend="brace">` |

Eight families of typographic distinction that the bundle currently loses.

### The mapping's first find: `«SS»`/`«SR»` are DEAD, and the dead rule is wrong

**Corrected 2026-08-22 after measuring.**  This section first claimed a shipped
bug.  It is not one: `«SS»` and `«SR»` occur **0 times in 37,226 article bodies**,
and `class="sans-serif"` / `class="explicit-serif"` **0 times in 37,226 rendered
HTML**.  No producer emits them.  The source construct is alive — `{{sans-serif}}`
on 20 pages, `{{serif}}`/`{{Serif}}` on 78, concentrated in ALPHABET where letters
are discussed AS letters — but it is carried by the style-span path instead
(`«SPAN[style:font-family:sans-serif]»`, 117 in ALPHABET alone) and renders
correctly.  Nothing was ever subscripted for a reader.

What remains is a **vestigial marker pair alive in four places**, one of which
holds a wrong rule: `export/markdown.py:139` maps `"SS": ("<sub>","</sub>")` and
`"SR": ("<sup>","</sup>")`.  They are not sub- and superscript.  The viewer's own
CSS says what they are:

> `.sans-serif` — Sans-serif metalinguistic letter — source uses
> `{{sans-serif|…}}` to mark single letters being discussed AS LETTERS
> (alphabetic typography convention).  Distinguishes the letter "A" qua letter
> from the running word "A".
>
> `.explicit-serif` — `{{Serif|I}}` is the mirror of `{{sans-serif|…}}`.

Had anything emitted them, the bundle would have rendered every metalinguistic
letter as a subscript.  Nothing does.  Genuine sub/superscript never enters the
marker stream either: it is carried as literal `<sub>`/`<sup>` HTML (which is why
those tags sit in `render/leaks.KNOWN_TAG_NAMES`).  So the rule is wrong twice
over — wrong about what `«SS»` means, and redundant with a mechanism that already
handles the thing it thought it was doing — and it is unreachable besides.

**Remedy: delete the pair, in all four places** — the `markers.py` registry entry,
the two `render/inline.py` decoder lines, the `markdown.py` mapping, and the two
`viewer.html` CSS rules.  Not "fix the mapping": there is nothing to map.

**The lesson is the one already written down.**  [[feedback_dead_is_wrong]] says
dead code whispers wrong answers and should be distrusted and deleted.  This is
that, demonstrated: the dead rule was read as authoritative, believed, and
reported as a shipped defect affecting the alphabet articles — by me, in this
document, until the corpus was asked.  Dead code does not merely fail to run; it
supplies confident wrong answers to whoever reads it next
([[feedback_look_dont_theorize]]).

The "TEI as external auditor" claim survives, in a weaker and more honest form:
writing the mapping did surface something real — a dead marker pair and a wrong
rule — but not a defect any reader ever met.

### Content

| marker | TEI |
|---|---|
| `«FN[name]:body«/FN»` | `<note place="foot" n="name">` |
| `«MATH:…«/MATH»`, `«EQN:…»`, `«MATHPH»` | `<formula notation="TeX">` (`@rend="display"` for EQN) |
| `{{IMG:file\|meta\|caption}}` | `<figure><graphic url=""/><head>caption</head></figure>` |
| `{{VERSE:…}}` | `<lg><l>` per line |
| `«OL[type:…]»` / `«UL»` / `«LI»` | `<list rend="numbered\|bulleted"><item>` |
| `«TABLE[…]»`,`«TR»`,`«TD»`,`«TH»`,`«CAPTION»` | `<table><head>`, `<row>`, `<cell>` (`@role="label"` for TH, `@cols`/`@rows` for spans) |
| `«LN:target\|display«/LN»` | `<ref target="#{stable_id}">` |
| `«XL:url\|display«/XL»` | `<ref target="{url}">` |
| `«AL:…»` | resolved to `«LN»` before export — no TEI rule needed, but see §9 |

### Metadata (`<teiHeader>`)

Built from the article JSON's own fields (`volume`, `page_start/end`,
`stable_id`, `ws_page_start/end`, `word_count`, `contributors`, `source_quality`):

```xml
<teiHeader>
  <fileDesc>
    <titleStmt><title>METEOROLOGY</title>
      <author ref="#c-a">Cleveland Abbe</author></titleStmt>
    <publicationStmt>… CC-BY-SA, britannica11.org/article/18-0285-420571 …</publicationStmt>
    <sourceDesc><biblStruct>
      … Encyclopædia Britannica, 11th ed., vol. 18, pp. 285–…, Cambridge UP 1911 …
      <relatedItem type="transcription" target="{wikisource page range}"/>
    </biblStruct></sourceDesc>
  </fileDesc>
  <encodingDesc>… projectDesc, editorialDecl, the ODD …</encodingDesc>
  <profileDesc><particDesc><listPerson>… the 1,508 contributors …</listPerson></particDesc></profileDesc>
</teiHeader>
```

**The contributor slug is already an `@xml:id`.**  `contributor_slug` (landed
2026-08-22) produces `c-a`, `j-f_k`, `l-d-star` — unique across the roster, gated
at emit, `[a-z0-9_-]+`, which is exactly what `@xml:id` requires (an XML Name:
must not start with a digit; ours start with a letter).  `<person xml:id="c-a">`
in the corpus header, `<author ref="#c-a">` in each article.  This is the standard
TEI way to do authorship and we can do it today without inventing anything.

## 6. The apparatus — what TEI lets us finally say

TEI has a vocabulary for editorial intervention, and we have interventions we
currently make silently:

* **`data/corrections.json`** → `<choice><sic>{source}</sic><corr>{ours}</corr></choice>`.
  Every correction becomes visible, attributable and reversible by the consumer.
  Right now a reader of the bundle cannot tell where we intervened.
* **Unproofread pages** (`source_quality.lowest_level <= 1`, the ones where
  mathematics arrives as OCR garbage, [[project_unproofed_math_impact]]) →
  `<div cert="low">` or `@resp`, and the damaged runs as `<unclear>`.  The site
  already shows a quality notice; TEI can carry it into the data.
* **Unresolved cross-references** → `<ref>` without `@target`, rather than the
  current silent degradation to display text.

This is the honest-apparatus arc arriving with a standard vocabulary instead of
one we would have to invent.

## 6a. Provenance is THREE-valued, and our model has two slots

Established 2026-08-22, from the raw source (vol 1 p311):

```
(<span title=Pyrphóros>{{polytonic|Πυρφóρος}}</span>)
```

That `title=` is hand-written into the wikitext by a Wikisource transcriber.  It
cannot be EB1911's — a printed page has no hover.  So it is neither the source's
nor ours: it is **the transcriber's**, and we currently carry it silently.  Our
model has two categories — the source, and our own `corrections.json` — and this
is a third.

**The discriminating question is not "who wrote it" but "does it add text that was
not printed?"**  Sorted by that test, the transcription's interpolations fall
cleanly in two:

| interpolation | pages | adds printed-absent text? |
|---|---|---|
| `[[Author:Pius X\|Pius&nbsp;X]]` | 3,227 | **No** — "Pius X" is printed; the link is navigation |
| `{{EB1911 article link\|Curia Romana}}` | 8,217 | **No** — "(See Curia Romana.)" is printed |
| `{{polytonic\|Πυρφóρος}}` | 205 | **No** — a font hint around printed Greek |
| `<span title="Pyrphóros">` | **3,519** | **YES** — a transliteration that is not on the page |

Only the last interpolates content, and it is 12% of pages.

**On the site this is not a bug.**  It renders as a tooltip — visibly not part of
the text, a reading aid, and it has been shipping happily.  The obligation is
specific to a data format, where a consumer takes the text to BE the text and has
no tooltip to disbelieve.

**Resolution (proposed): attribute, don't launder and don't drop.**

* Add a `<respStmt>` crediting the **Wikisource transcribers** for the
  transcription.  We owe this regardless — the entire text is their work, and TEI
  expects the transcriber named in `<titleStmt>`.  This turns an awkward question
  into a credit we should have been giving.
* The gloss becomes attributed and separable:
  `<note type="transliteration" resp="#wikisource">Pyrphóros</note>` beside the
  Greek — a consumer can filter it out, or use it, knowing whose it is.
* Dropping it would violate carry-by-default ([[feedback_when_in_doubt_carry]]);
  carrying it unattributed would put a 21st-century editor's gloss in EB1911's
  voice, in the one format whose audience would most trust it.

**Follow-on audit (not yet run):** the four rows above were found by looking for
what we already knew about.  The real question is what ELSE the transcription
interpolates that we carry without noticing.  `source_pages` survives the phase-1
truncate, so this is cheap to ask.

## 7. Slices

1. **One article, hand-checked, validating** — METEOROLOGY (byline, sections,
   footnotes) or ARACHNIDA (figures, tables).  Settle the ODD.
2. **The producer set** — `export/tei.py`, family by family, diffed against the
   HTML renderer for content equivalence.
3. **Corpus run + validation gate** — all 37,226 validate; wire into phase 7.
4. **Bundle + `<teiCorpus>` manifest**; document it on the download page.
5. *(later)* the apparatus of §6.

## 8. Decisions

* **DECIDED (user, 2026-08-22): `@rendition`, not `@rend`.**  `@rend="small-caps"`
  is free text repeated on every element; `@rendition="#sc"` points at a
  `<rendition>` declared once in `<tagsDecl>`.  Same one-owner discipline the rest
  of the codebase runs on, and it makes the set of distinctions we carry
  **enumerable in the header** instead of scattered across 37k files — which also
  means the set can be audited, and a new one cannot appear silently.  The
  declared set is §8a.
* **`«XL»` IS NOT A SIZE.**  Noted because this document got it wrong first time:
  the size family is `XXS XS SM LG XXL FS LH` (seven), and `«XL:url|display»` is
  the EXTERNAL LINK marker.  `markdown.py`'s docstring has this right.
* **DECIDED (user, 2026-08-22): NO invented semantic markup.**  TEI offers
  `<persName>`, `<placeName>`, `<date>`, `<orgName>` and the rest, and every
  DH project is tempted.  **We do not have that information.**  EB1911 does not
  mark its persons and places, so producing them means inferring them, and an
  inferred entity is an assertion in our own voice about a source that made no
  such claim — the imposed-taxonomy failure, in the one output format whose
  audience would most trust it ([[imposed-taxonomy-is-negative-value]],
  [[toc-characterize-before-ruling]]).  **Encode only what the source marks.**
  A consumer who wants entities can run their own NER over our text and own the
  result; that is their claim to make, not ours to bake in.
* **Size markers.**  `«FS»` carries a percentage; do we encode the number
  (`rend="font-size:83%"`) or the class?  *Recommendation: the number* — carry
  what the source said ([[feedback_forks_are_dropped_attributes]]).
* **One file per article vs one per volume** — see §2; 37,226 small files
  compress fine and match the URL space, but institutional consumers sometimes
  prefer volumes.  Could ship both from the same writer.
* **`@facs` targets** — point at our scan URLs, or at Wikisource/IA page scans?
  Ours are stable and we control them.

## 8a. The declared rendition set

`@rendition` requires every presentational distinction to be declared once in
`<tagsDecl>`.  That set is enumerable because the renderer already emits a closed
vocabulary of classes — read off `render/inline.py`, not guessed:

**Presentational → a `<rendition>` each** (17):
`small-caps` · `centered` · `float-left` · `float-right` · `underline` ·
`sans-serif` · `explicit-serif` · `mirror-h` · `size-xxs` · `size-xs` ·
`size-sm` · `size-lg` · `size-xxl` · `dhr-block` · `dhr-inline` · `inline-bar` ·
`cell-verse`

Plus the parametrised ones, which carry a value rather than a class and so take a
literal `@style` (TEI permits CSS in `@style`): `«DIV[style:…]»`, `«SPAN[style:…]»`,
`«FS»` (a percentage), `«LH»` (a line-height).

**NOT renditions — resolve to structure or drop** (5):
`fn-popup-num` (a site UI affordance, not in the text), `math-system-*` (an
equation-system grouping → `<formula>` structure), `hieroglyph` /
`hieroglyph-fallback` (a glyph-availability fallback, site-only).

**One open question: `xlit`.**  The renderer emits
`<span class="xlit" title="álpha">ἄλφα</span>` — a transliteration carried in
`@title`.  Before encoding it, establish whether that transliteration is IN THE
SOURCE or generated by us.  If it is ours, it is an addition, and under the
no-invented-markup decision it either goes out or goes in explicitly attributed
(`<foreign>` plus `@resp`) — never silently, and never as if EB1911 said it.

## 9. Risks

* **A fourth output to keep in sync.**  Mitigated by construction: same tree, same
  leak net, plus validation.  But it is real, and it is the "N sites must remember
  X" shape ([[feedback_dissolve_dont_fix]]) — the producer set must be the only
  place that knows a marker's meaning.
* **Verbosity.**  ~40M words of TEI is large; it compresses well and ships in the
  existing tarball.
* **ODD authoring** is real, bounded work and needs doing once, properly.
* **Scope creep into semantics.**  TEI invites `<persName>`, `<placeName>`,
  `<date>` markup everywhere.  We should not — we do not have that information,
  and inventing it is the imposed taxonomy again.  Encode only what the source
  marks.

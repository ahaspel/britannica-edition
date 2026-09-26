# Complete MDX edition — 2026-09-14

**Release packaging:** the standard MDX is the main download; enhanced Windows
search is an optional complete alternative. Both have matching samples. Use
`mdx/releases/` for distribution; see [`mdx_packaging.md`](mdx_packaging.md).

**Current installed package:** native canonical-title search across all 37,225
articles, built with `--all --native-search`. Setup and behavior are documented
in [`mdx_search.md`](mdx_search.md). It adds a local title index and compressed
article store for GoldenDict's supported Programs interface. The current MDX
is 117,316,215 bytes, MDD 450,022,368 bytes, ZIP 704,853,503 bytes; 39,360 internal
redirect keys and 40,633 HTML records. The latest build took 352.8 seconds.
The counts and sizes below describe the preceding conventional MDX package,
which remains available by omitting `--native-search`.

The same exporter now supports the complete corpus:

```
uv sync --extra mdx
uv run --extra mdx python -m britannica.mdx.build --all --output mdx/complete
```

It reads existing canonical exports, uses the shared offline renderer, cached
SVG mathematics and existing image encoder, then compiles with pinned
`mdict-utils==1.3.14`. No source rebuild is needed. Output is ignored by Git.

## Coverage and packaging

| Contents | Count |
|---|---:|
| Canonical articles/plates | 37,225 |
| Redirect keys, including stable identifiers and lookup aliases | 44,915 |
| Choice pages | 1,273 |
| Contributor pages | 1,508 |
| Topic pages | 519 |
| Volume lists | 28 |
| Introduction and prefaces | 3 |
| Reader's Guide pages (hub, six parts, 65 chapters) | 72 |
| MDD resources, including CSS | 10,745 |
| Checked internal links | 317,217 |

The latest MDX is 117,468,764 bytes; MDD 450,022,368 bytes; distribution ZIP
570,677,261 bytes (about 571 MB / 544 MiB). Full builds have taken four to eleven
minutes on this workstation, depending on corpus disk-read time. Observed compilation memory was approximately
3.3 GiB; this was a spot measurement, not a measured peak.

Every nonempty article/plate has one stable canonical entry. Corpus identities
must match the index. The sole empty record, `25-0483-dc502a`, is explicitly
excluded, matching the existing download exporter. New unexplained omissions
fail the build.

Headwords use canonical titles and distinct resolved reference names. Link
display text is not harvested as an alias. Redundant accent and punctuation
variants are consolidated, preferring the book's spelling. Source-attested
name-order variants are retained for natural full-name lookup;
ambiguous spellings retain all evidenced destinations in a choice page.
`alias_report.json` records harvested candidates; `redundant-aliases.json`
records which spellings were consolidated and their retained lookup keys.
The complete build removes 15,089 redundant spellings while preserving word order.

Enable **Ignore diacritics** in GoldenDict-ng Preferences for accent-free lookup.
Search personal names by surname or a source-attested full name. Removing
word-order aliases broke `Jonathan Swift`, which must resolve to `SWIFT, JONATHAN`
without splitting into the name JONATHAN and bird SWIFT. These aliases are restored.
DESCARTES retains `DESCARTES, RENÉ` and `RENÉ DESCARTES`, instead of five spellings.

Article topic links are always visible immediately below the byline. Unsigned
articles show them below the volume/page citation. Multiple topic memberships
appear together, retaining their full paths and destinations.

The contents entry (`Britannica 11`) leads to volumes, the full contributor
roster, the topic hierarchy with its notes and printed unresolved entries,
introduction/prefaces, and the Reader's Guide. These reuse the existing taxonomy,
roster and EPUB ancillary extractors. Guide links and illustrations are local.

Keep `Britannica11.mdx` and `Britannica11.mdd` together in a GoldenDict-ng
dictionary folder and rescan. `Britannica11.zip` includes both, installation
instructions, license, manifest, source-link issue inventory and checksums.
Generated `entries.json` contains only the difficult sample articles for reader
QA, and is not part of the distribution.

## Existing source-link issues

Full validation found 18 missing section destinations in the canonical exports.
OILS refers to an unanchored “Oil Testing” passage; SUDAN uses an abbreviated
section name. Other cases include apparent article references encoded as local
fragments, such as “France” within French department articles. These are not
MDX container failures. The issue inventory preserves each original destination
and label; it does not assert which source/parser correction is appropriate.

The exact audited links are displayed as text with `[source link unavailable]`.
They are also disclosed in the contents entry and manifest and listed in the
shipped `source-link-issues.json`. No text is removed, replacement article
guessed, or artificial section anchor inserted. An explicit allowlist in
`mdx/link_exceptions.py` limits this treatment to the audited destinations;
new missing links still fail. If a source anchor is repaired, its exception
automatically stops applying. Other source transcription/reference errors flow
through unchanged, as on the website.

## Integrity checks

The build validates every generated internal link and fragment, alias chains,
HTML IDs, and local resources; scripts and event handlers are rejected. It
reads back every compiled MDX record and MDD byte sequence and requires exact
equality, streaming verification to avoid an additional whole-corpus copy.

Thirteen focused tests cover lookup collisions, natural-name lookup, alias evidence, section identity,
missing links/resources, exception retirement, and Unicode/binary round trips.
The sample also rebuilds successfully through the extended exporter. No shared
renderer code changed.

Manifest hashes identify the corpus payloads, index, taxonomy, contributor roster,
ancillary source pages, images and Python export code. Complete corpus hashes
use sorted-key JSON payload serialization; sample hashes use the original file
bytes. Compiler version and UTC build time are recorded. Separate reader QA
reports fingerprint the actual tested MDX/MDD pair.

## Reader checks

GoldenDict-ng 26.8.0 / Qt 6.10.3 passed 36 automated checks on the full
edition before the topic-layout change, including readable content keys and compacted aliases. Coverage
includes all difficult sample articles, aliases, Unicode,
MERCURY choices with another dictionary enabled, footnotes/returns, back
navigation, section jumps, MDD resources, SVG math, dark content colors,
deep topics, all navigation hubs, and Reader's Guide hub → part → chapter links.
Screenshots are in `mdx/complete/reader-qa/`; `report.json` records package hashes.
Native network sources were disabled and WebEngine HTTP(S) requests blocked;
the checks generated no remote requests.

Native UI checks confirm one `DESCARTES, RENÉ` suggestion for DESCARTES,
successful ABABDA → ABĀBDA lookup with Ignore diacritics enabled, and readable
article titles in the full-text results for `thucydides`. The reader finished
full-text indexing. ZIP CRC verification passes for every packaged file.

Subsequent correction restores source-attested name-order aliases: native
`Jonathan Swift` + Enter now opens `SWIFT, JONATHAN` directly. This supersedes
the earlier single-Descartes-suggestion policy. The rebuilt package passes
exact read-back and all 13 focused tests; full-text indexing restarts on reload.

FRANCE, UNITED STATES and JAPAN were tested as the three largest entries by
the corpus index's body-length field. Each rendered with its images in roughly
one second during the first full-reader run. These are local measurements,
including QA polling overhead, not hardware-independent promises.

The reader initially truncated deeply nested topic keys and failed their
lookups. Topic keys now use compact hashes of the canonical taxonomy IDs;
full topic paths remain displayed. Three overlong reference-derived alias
spellings are excluded and reported because this reader limits headwords to
100 characters. No canonical article is excluded by that policy. The same
reader checks explicitly exercise the formerly failing deep topic paths.

Native theme switching, other MDX readers and replacing a published older
edition remain untested. Reloading rebuilt full files in this portable reader
does rebuild its lookup index; a separate full-text index is reader-managed.

## Search behavior and agreed scope

The user tested native full-text search with `thucydides`. The dialog reported
197 matches and displayed internal IDs in alphabetical order. The current build
puts readable titles on content records. Stable IDs were kept as redirect keys
for a time so that links held a fixed address; that was withdrawn on 2026-09-25,
because an MDX redirect is indexed exactly like a page and those ~40,000 keys
were ~40,000 machine ids in the reader's own headword list. Links now carry the
display key, and `check_headwords` refuses any key beginning `EB1911:`.
Unambiguous article titles are reused; homonyms take the book's own opening
words, then printed volume/page, and an ordinal only as a last resort.
Navigation records receive readable labels too. `display_keys` in the manifest
preserves the complete mapping. See `mdx_packaging.md` for the headword rules.

The initial request was the **site's exact hierarchy
and result presentation**, with THUCYDIDES first for `thucydides`. The canonical
ranking is `tools/viewer/search-api.js:rankHits`: exact title → first title word
→ any title word → title prefix → title substring → body-only; within a tier,
body occurrence count descending, then alphabetically. The site's full-results
view shows title and printed location for title matches; body-only results add
match counts and up to six highlighted occurrence excerpts.

The installed reader's own source was inspected at tag `v26.8.0`:
[`fulltextsearch.cc`](https://github.com/xiaoyifang/goldendict-ng/blob/v26.8.0/src/fulltextsearch.cc)
sorts with `FtsHeadword::operator<` using locale-aware alphabetical comparison,
and `HeadwordsListModel::data` supplies only the headword as the display value.
[`ftshelpers.cc`](https://github.com/xiaoyifang/goldendict-ng/blob/v26.8.0/src/ftshelpers.cc)
retrieves up to 100 Xapian matches before that display sorting. MDX data cannot
override this native dialog's comparator or display model.

The user subsequently accepted native title lookup plus readable, usable native
full-text results as sufficient. **No separate search page or modified GoldenDict
is required.** Keep the native ordering. Alias cleanup now avoids redundant
suggestions while preserving real alternative names and distinct articles,
using the canonical spelling and reader accent folding.

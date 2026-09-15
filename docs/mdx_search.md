# Britannica search for the dictionary edition

## Full edition integration — 2026-09-14

For the installation package and shared Windows/macOS/Linux installer design,
see [`mdx_installation.md`](mdx_installation.md). The Python setup command below
is the earlier advanced installation path; the new Windows package bundles its
runtime and provides a graphical installer.

The full 37,225-article edition now builds with native canonical-title search:

```
python -m britannica.mdx.build --all --native-search --output mdx/complete
```

The MDX retains canonical display titles and stable internal links. Alternate
names live in `search/titles.json`; the supported Prefix match program returns
one title per article. The HTML program handles Enter and browser URI queries:
an exact alternative name opens the existing article HTML; ambiguous names
show linked canonical choices. Partial queries can also show a choice list.
GoldenDict still controls the final ordering of native suggestions and full-text
results. This does not reproduce the site's complete ranking or snippets.

Article HTML is stored, compressed and indexed by stable identity, in a local
SQLite database. Only the selected body is decompressed per lookup. Styles,
images, math, footnotes and cross-references use the existing exported content.
Cross-article section links use GoldenDict's `gdanchor` parameter. Website
search code and indexes remain unchanged; the package contains a copy of the
existing folding/title-rank functions.

Ship `mdx/complete/Britannica11.zip`, including its `search` directory. This
integration currently targets **portable GoldenDict-ng on Windows**, tested
with version 26.8.0. It requires Node.js 22.13+ at runtime and Python 3 for setup.
Close GoldenDict, extract the package, then run from the extracted directory:

```
python search/install.py --reader "PATH TO PORTABLE GOLDENDICT" --node "PATH TO node.exe"
```

The installer copies the MDX, MDD and search files into the reader's `content`
directory, configures the two local Programs sources, enables Ignore diacritics,
and backs up the existing configuration. Other settings are retained. Rerunning
setup replaces these same sources without duplicating them. Program commands
use absolute paths: rerun setup if the reader or Node installation moves.
The program receives query text on stdin, never as shell command text.

Validation: 16 focused tests pass; full compiled read-back is exact and all
317,217 internal links validate. The installed edition passes 39 reader checks
with zero remote requests, including math and images served through alternative
names. Native UI checks confirm both Swift name orders, both Descartes queries,
Thucydides and the three distinct Mercury articles. Native full-text indexing is
complete; `thucydides` returns 198 readable results in GoldenDict's own order.
The registered `goldendict://Jonathan%20Swift?target=main` browser handoff opens
the author directly. Feedly's context-menu interception still needs the user's
separate confirmation; this change does not alter the Chrome extension.

Reader evidence: `mdx/complete/reader-qa/report.json` and screenshots in that
directory; compiled package hashes: `mdx/complete/SHA256SUMS`.

The prototype notes below describe the earlier investigation, not the current
package's storage or installation mechanism.

## Native prototype result — 2026-09-13

The supported Programs interface works in unmodified GoldenDict-ng 26.8.0:

| Query | Native suggestion result |
|---|---|
| Jonathan Swift | SWIFT, JONATHAN once |
| Swift, Jonathan | SWIFT, JONATHAN once |
| Descartes | DESCARTES, RENÉ once |
| Rene Descartes | DESCARTES, RENÉ once |
| mercury | Three distinct articles, qualified by volume/page |
| thucydides | THUCYDIDES once |

Selecting the Swift result opens the actual article. Prefix match alone does
not handle Enter without a selection: GoldenDict still submits the literal
query. A second supported **HTML** program resolves exact aliases and returns
the existing article HTML; this was verified with Jonathan Swift + Enter.
The existing scoped stylesheet is embedded for that path, and resource and
entry links need explicit reader URLs because MDX's rewriting does not run on
external-program HTML. The Swift article's formatting was visually checked.

`tools/mdx-title-search.cjs` is the prototype helper. It reads a 37,225-article
title/alias index derived from the verified package manifest and alias audit,
deduplicates by article identity, and returns canonical labels. It reuses the
site's folding and title-tier functions. Candidate matching additionally accepts
all query terms as title/name word prefixes. Six cold-process lookups measured
119–150 ms locally, including loading the complete title index.

GoldenDict **reorders** program completions using its own title score and length
tiebreaker. The Mercury screenshot demonstrates an order different from helper
stdout. Therefore this achieves canonical results but does not establish exact
site-ranking parity. The program protocol supplies newline-separated titles,
not explicit ranks or separate destination IDs. Homonyms require distinct labels.

The isolated test used eight real articles, canonical MDX keys plus stable-ID
redirects, the full title index, and the existing MDD. Artifacts and launchers:
`mdx/search-prototype/`, `mdx/build_search_prototype.py`,
`mdx/launch_search_prototype.py`. Screenshots: `mdx/complete/reader-qa/prototype-*.png`.
Cross-links outside those eight articles, complete resource rendering through
the HTML program, browser URI handoff, packaging, and full-edition integration
are not yet verified. The helper's HTML mode currently loads a small JSON fixture
and uses a prototype dictionary resource ID; production needs indexed article
storage and an installation-specific resource binding. Do not ship this fixture
as the full dictionary or claim the full edition has been migrated.

The acceptance target is the site's article search, not a tidier MDX headword
list. `Jonathan Swift` and `Swift, Jonathan` must produce one result labelled
`SWIFT, JONATHAN`, pointing to the same stable article. Accents, punctuation and
alternative names are matching data, never duplicate displayed results.

## Existing implementation to reuse

- `tools/viewer/typeahead.js` calls `searchClient.rankedSearch(q, {limit: 50})`
  and displays the first 16 article records with their canonical titles.
- `tools/viewer/search-api.js` owns accent folding, title ranking and occurrence
  counting. Both site displays use this one ranking implementation.
- The site's candidates come from Meilisearch, with all query terms required,
  then a folded title/body substring gate. This is not a simple title-only
  substring scan. In particular, do not claim copying `titleRank` alone
  reproduces full-name or full-text behavior.
- `tools/pipeline/index_search_ec2.py` indexes canonical article IDs, titles,
  plain body text, contributors and locations. Reuse `load_corpus` and
  `markers_to_text` if an offline index is needed.
- The existing MDX stable article keys provide exact destinations. Search
  results should open those identities through GoldenDict's URI handler.

## Required behavior

1. Match queries against titles and lookup names; collect article identities.
2. Deduplicate by article identity before sorting or limiting results.
3. Display the canonical title, with the site's existing supporting text.
4. Reuse the site's ranking; explicitly specify and test any new handling of
   natural-order full names instead of silently introducing a second ranking.
5. Keep genuinely different articles distinct, including homonyms. An alias
   with several destinations must retain every evidenced destination.
6. Use the same search path for typing and Chrome's selected-text command.

Regression examples: Jonathan Swift / Swift, Jonathan; Rene Descartes /
Descartes, René; thucydides; mercury (distinct articles); Zürich / Zurich.
Compare actual site candidate sets and order before declaring parity.

## Native reader boundary

**Correction: inspect the supported external-program interface before considering
a reader patch.** GoldenDict's Programs dictionary type **Prefix match** accepts
a program's output as native search-box completions. This is a promising route
to matching aliases internally and returning only canonical titles, while an
MDX without display aliases supplies the articles. Verify candidate filtering,
GoldenDict's subsequent ranking, homonym labels, and Enter-without-selection
behavior in a small native prototype before rebuilding the complete dictionary.
This needs a local helper/index, but no separate search box or reader fork.
Documentation: https://xiaoyifang.github.io/goldendict-ng/manage_sources/#programs

GoldenDict-ng v26.8.0 `MainWindow::updateSuggestionList` calls the dictionary
prefix matcher. `updateMatchResults` passes its returned headword strings
directly to the dropdown model. The UI does not receive a separate canonical
display label and article identity at this point. Adding/removing MDX aliases
therefore cannot implement the required separation on its own.

Source: https://github.com/xiaoyifang/goldendict-ng/blob/v26.8.0/src/ui/mainwindow.cc

The user explicitly rejects a separate search interface. Investigate native
alias-to-canonical result handling first. In the installed MDX reader, `addWord`
indexes every headword; `@@@LINK=` is followed during article retrieval, while
prefix search inherits the generic B-tree matcher. No canonical identity is
supplied with its `WordMatch` (word and weight only). Thus redirects already
share articles, but native suggestions do not coalesce them by destination.

A fallback native code change would be to resolve MDX redirect identities for suggestions
and deduplicate canonical destinations before truncation while retaining the
matched alias's relevance. Ambiguous aliases must remain choices. This needs
implementation and performance investigation; it is not an existing MDX flag
or a verified ready-to-use setting. Do not conflate this bounded display issue
with a requirement to replace the whole application or search engine.

# Britannica search for the dictionary edition

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

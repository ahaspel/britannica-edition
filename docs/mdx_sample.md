# MDX sample — 2026-09-13

Phase 1 of [the plan](mdx_edition_plan.md) is complete. The sample works in
GoldenDict-ng 26.8.0, Windows x64, Qt 6.10.3. The portable release archive's SHA-256
was checked against the GitHub release asset digest before launching it.

## Artifact and results

Local output: `mdx/sample/Britannica11-sample.zip` (1,739,843 bytes at this build).
The MDX is 676,913 bytes and MDD is 1,051,522 bytes. Sizes describe this sample,
not an estimate for the complete edition. Generated dictionaries, the portable
reader, previews, screenshots and reports are ignored by Git.

| Contents | Count |
|---|---:|
| Canonical articles/plates | 13 |
| Alias keys (including help lookup) | 16 |
| Disambiguation pages | 1 |
| Contributor pages | 11 |
| Topic pages | 11 |
| Help page | 1 |
| Total MDX keys | 53 |
| MDD resources (46 images plus CSS) | 47 |
| Checked internal links | 261 |

The fixed selection is in `src/britannica/mdx/sample.json`. It includes the three
MERCURY articles, AGRICULTURE, ALGEBRA, DYNAMICS, ALPHABET, ARTHUR, ABACUS,
CONTINUED FRACTIONS, an AEGEAN CIVILIZATION plate, ABĀBDA and AARON’S ROD.
Contributor/topic pages list only sample articles. A source-attested
`Continued Fraction` alias exercises redirection; title normalization supplies
accent and punctuation variants without depending on reader preferences.

Validation passed:

- Exact round-trip equality of all entry strings and all resource bytes through
  the compiled MDX/MDD, using the compiler package's reader.
- All generated local targets, section fragments, alias chains and resources
  resolve. Five focused unit tests cover ambiguous/folded keys, missing targets,
  alias cycles, missing resources, Unicode/binary compilation and Windows cleanup.
- 23 checks in GoldenDict's actual embedded browser, including all 13 articles,
  all image occurrences loaded from `bres:` MDD resources, matching inline SVG
  counts, CSS, three-way choices, alias and Unicode lookup, contributor/topic
  navigation, cross-entry section navigation, and footnote/return links.
- A second local dictionary also defines MERCURY. Ordinary lookup displays both
  dictionaries; clicking a Britannica choice opens only the intended Britannica
  article via its stable key.
- Native online sources were disabled in the isolated portable config, and
  WebEngine HTTP(S) requests blocked during the final run. No HTTP(S) page
  requests occurred. This is application-level offline verification, not a claim
  that the workstation's network adapter was disabled.
- Screenshots were inspected for the wide AGRICULTURE table, SVG algebra,
  illustrated plate and MERCURY choice page. Dark background/text colors were
  emulated inside the reader; its native theme preference UI was not tested.

Evidence: `mdx/sample/manifest.json`, `SHA256SUMS`, and
`mdx/sample/reader-qa/report.json`. Screenshots are alongside the latter. The
manifest fingerprints selected input articles, corpus index, taxonomy, image
sources and Python export code. The reader report records tested package hashes.

## Build and try it

From the repository root, with the optional dependency installed:

```
uv sync --extra mdx
uv run --extra mdx python -m britannica.mdx.build --sample --output mdx/sample
```

The existing `.venv` was used directly in this session. The command uses a fixed
selection from the current index, copies its payloads into private staging, and
loads them through `load_corpus`. It does not scan/parse Wikisource or rebuild the
corpus. All 428 distinct requested math assets were already cached. Compilation
and packaging took about four seconds in the warmed session; this is not a
full-corpus performance benchmark.

Place the MDX and MDD together in a GoldenDict-ng dictionary folder and rescan.
Look up `Britannica 11 sample` to browse the contents, `MERCURY` for choices,
`Continued Fraction` for redirection, `ABABDA` for accent normalization, and
`ALGEBRA` for equations. External article links visibly say they are online and
outside the sample.

The isolated reader used here is under
`mdx/reader/GoldenDict-ng-26.8.0-Qt6.10.3/`. A `portable` folder beside
`goldendict.exe` keeps its settings separate; its `content` folder holds the
sample and a tiny QA control dictionary. This is a test installation, not part
of the dictionary ZIP.

## Repeat the reader checks

Use a separate portable reader, disable its MediaWiki, website and DICT-server
sources, and copy the current sample MDX/MDD into `content`. Add this UTF-8
`content/qa-control.dsl` fixture (it is not a shipped Britannica entry):

```
#NAME "MDX QA control"
#INDEX_LANGUAGE "English"
#CONTENTS_LANGUAGE "English"
MERCURY
    QA control dictionary: unrelated mercury definition.
```

Launch that reader with `QTWEBENGINE_REMOTE_DEBUGGING=127.0.0.1:9223`, then look
up ALGEBRA. For unattended testing, this session also used
`QT_QPA_PLATFORM=offscreen`; omit it for normal interactive use. Neither variable
needs to be set globally. The debugging endpoint should stay local to the test
session and be closed when finished.

```
node tools/diagnostics/check_mdx_reader.mjs
```

The script accepts output directory and portable reader directory as its first
two arguments; `MDX_READER_CDP` overrides the local endpoint. It requires Node
with built-in `fetch` and `WebSocket` (Node 24 was used). It verifies that native
online sources are disabled and that the reader's dictionary files match the
output files. Its screenshot/report directory is `reader-qa` under the output.

Qt WebEngine does not support the browser-context operations Playwright's CDP
connection requests, so this harness uses the page's CDP endpoint directly.
Offscreen lazy images are explicitly requested by the harness so every image
resource is checked, rather than just those in the first viewport.

## What remains

The user subsequently confirmed the sample's mathematics, images, glyphs and
full-text search (including `mercury`) in the interactive reader. Front matter
and the Reader's Guide remain outside this pilot. Complete-edition work now
uses the same exporter with `--all`; see [the complete edition](mdx_complete.md)
for its coverage and validation. Native theme switching and other dictionary
applications have not been validated.

No source transcription, shared renderer, website, EPUB, or sales listing was
changed by this export work. The product can advance to the complete-corpus
phase without revisiting the binary format or inventing a new rendering path.

# Britannica 11 MDX / GoldenDict edition

Proposed 2026-09-13. **Phase 1 completed the same day:** the 13-article sample
compiles and passes GoldenDict-ng 26.8.0 reader checks. See
[`mdx_sample.md`](mdx_sample.md) for the artifact, evidence, reproduction steps
and remaining scope. The complete-corpus exporter is now implemented with
`--all`; see [`mdx_complete.md`](mdx_complete.md) for results and limitations.

## Objective and scope

Produce an illustrated, offline reference edition from the existing Britannica
corpus, delivered as MDX/MDD files. GoldenDict-ng is the first supported reader.
The files should use conventional MDict features so other readers can be tested
later without creating another edition pipeline.

This is a modest export extension. Reuse the canonical renderer, resolved
cross-references, contributor and topic data, and EPUB asset machinery. No new
OCR, source ingestion, transcription cleanup, or website reconstruction is
required. Source improvements subsequently flow into this artifact through the
same pipeline as the website and EPUB.

The initial product includes all nonempty article/plate records, illustrations,
tables, mathematical notation, footnotes, internal cross-references, contributor
biographies and article lists, and topic navigation. Preserve source citations
and edition attribution. Include a simple start/help entry. Adapt the existing
front matter and Reader's Guide as linked entries where their current generators
can be reused; inventory these explicitly rather than silently losing them.

Do not make support for every MDX reader, a custom application, a second format,
an online GoldenDict connector, DRM, or a market survey prerequisites for the
first release. Demand is unproven, but the remaining engineering work is small
enough to justify a useful first edition. Creating this plan does not publish a
product or settle its price.

## Deliverables

| Artifact | Purpose |
|---|---|
| `Britannica11.mdx` | Article HTML, lookup aliases, disambiguation and navigation entries |
| `Britannica11.mdd` | Local images, stylesheet and any required fonts/resources |
| `README.md` and attribution/license material | Installation, supported reader versions, edition identity, limitations |
| Release manifest and SHA-256 checksums | Input identity, counts, dependency versions and output verification |
| Distribution ZIP | One downloadable product containing the above |
| Clearly labeled sample ZIP | Installation/compatibility trial using the same exporter |

Start with unencrypted MDX version 2.0, UTF-8 article text, and an existing
compiler such as `mdict-utils`. Pin the tested compiler version. Let the compiler
handle binary sorting, block layout, compression and MDD path encoding. Confirm
its resource and memory behavior at full scale before treating it as settled.
Do not implement the binary format ourselves.

## Existing components and the export seam

| Component | Reuse |
|---|---|
| `export/corpus.py:load_corpus` | Strict corpus loading; corrupt records must fail the build |
| `export/article_json.py:stable_id_from_filename` | Stable identity independent of rebuild-assigned database IDs |
| `render/article.py:render_article` | Canonical content rendering and existing offline policies |
| `epub/pack.py:_LinkTokens` | Existing link-policy interface: `url_for` and `contrib_url` |
| `epub/images.py` and `image_assets.py` | Image identity, existing display-resolution encoding and caches |
| `epub/math_assets.py` | Pre-rendered math and asset caches |
| `epub/epub.css` | Starting point for content typography |
| `export/download.py`, EPUB front matter and Reader's Guide code | Existing contributors, topics, provenance and ancillary navigation |

Paths above are relative to `src/britannica/`. Inspect the actual helper contracts
before extracting anything. The EPUB builder currently calls the canonical
renderer with `target="epub"` and an `epub_bundled` link-policy object; it is not
simply a ZIP wrapper around stored site HTML.

Implement a dictionary link policy against that existing interface. Initially
reuse the offline render behavior, then introduce only the target-specific
differences the sample demonstrates. Avoid a broad renderer refactor or a copy
of the EPUB builder. EPUB chunk packing, spine generation, and its custom search
index do not belong in this exporter. GoldenDict owns lookup and full-text search.

Proposed home: `src/britannica/mdx/`, with a build entry point and small modules
only where indexing, resources and validation warrant separation. Proposed CLI:

```
python -m britannica.mdx.build --sample --output mdx/sample
python -m britannica.mdx.build --all --output mdx/complete
```

Both `--sample` and `--all` are implemented. Generated output
under `mdx/` is ignored. Builds read a complete, identified derived corpus and
write a separate staging directory. A sample is a selection from that corpus,
not a partial source rebuild or deploy.

## Lookup and link design

Keep article identity separate from lookup spelling:

- Each article has one canonical content record keyed by a unique, stable
  identifier. Display its real title in the entry, not the internal identifier.
- Headwords and approved variants point to canonical records. Verify native
  MDX alias behavior in the sample; avoid multiplying long article bodies.
- Duplicate titles and aliases leading to several articles produce a labeled
  choice entry. Use existing title/context metadata to distinguish the choices.
  Never overwrite one article with another in a headword-keyed Python dictionary.
- Reuse canonical title/name normalization helpers. Reader case/diacritic
  folding can create additional collisions; exercise these in the sample.
- Use existing resolved references and curated aliases as evidence, not an
  instruction to index every occurrence of link display text. Phrases such as
  "see above" are not useful headwords. Do not generate speculative aliases.
- `xrefs/alias_table.py:build_alias_map` chooses the most frequent target for an
  ambiguous alias. Do not blindly reuse that reduced map as the lookup index.
  Preserve candidate targets from available resolved evidence and report gaps.
- Contributor, topic and help entries need distinct namespaces so that a topic
  or contributor name cannot replace a Britannica article.

Translate resolved article links to the reader's conventional MDX entry-link
syntax. Prove Unicode escaping, punctuation, alias targets and section fragments
in GoldenDict-ng before finalizing serialization. Reuse the canonical section
slug/anchor rules; do not derive a second scheme. Test lookup while another
dictionary is enabled, so internal Britannica links cannot silently resolve to
an unrelated dictionary's entry.

Keep genuinely external references as labeled external links. Carry unresolved
source references explicitly; do not pretend they are resolved local links.
Scan access may remain online and must be labeled accordingly. If a sample
omits a target, mark that destination as outside the sample and provide an
explicit website link rather than a broken internal link.

## Rendering and assets

Scope CSS under an edition wrapper and respect reader font sizing and light/dark
themes. Preserve semantic structure and carried source styling, including
footnotes, captions, tables and non-Latin text. Keep essential reading and
navigation independent of JavaScript.

Use existing pre-rendered SVG math first for GoldenDict-ng; use the established
PNG machinery only if an actual reader defect requires it. Bundle dependencies
locally. Do not inherit EPUB/Kindle-specific table splitting or other workarounds
without a demonstrated need in this reader.

Reuse display-resolution images for the initial product and retain transparency.
Inventory all referenced assets, including CSS URLs, special glyphs, maps and
ancillary illustrations. Reconcile absent assets against the current corpus:
historical EPUB missing-image counts are leads, not today's truth. New packaging
losses fail validation; pre-existing source omissions require an explicit report
and visible treatment. Do not substitute blank placeholders silently.

Start with one complete MDX and companion MDD. Measure size, build memory, cold
indexing and long-entry responsiveness. Neither the EPUB's size nor Kindle's
limits establish an MDX limit. Splitting files or articles is a response to a
measured problem, not an initial requirement.

## Implementation sequence

### 1. Difficult sample and compiler proof

Choose a small fixed set from current exports, covering duplicate headwords,
aliases, Unicode, one long article, a wide table, equations, a plate, footnotes,
cross-article section links, contributor and topic navigation. Add linked targets
as needed to exercise complete local paths without recursively including the
whole corpus.

Implement the minimal end-to-end path: strict load, canonical render, link policy,
resources, compilation, read-back. Open it in a recorded GoldenDict-ng version on
Windows. Verify the sample with networking disabled, including images and math.
This phase settles the genuine format uncertainties before full-corpus work.

### 2. Complete export and integrity checks

Expand the same exporter to the whole edition and ancillary entries. Record the
input artifact hashes, source edition information and code/dependency versions;
a Git revision alone is insufficient when local changes exist.

Required checks:

- Every eligible article is represented exactly once as canonical content.
  Reconcile identities, not just totals. The current baseline is 37,226 records
  and 37,225 nonempty records, with empty plate `25-0483-dc502a.json` excluded by
  the download exporter. Record that disposition explicitly and fail on any
  newly unexplained omission.
- Count canonical articles, aliases, choice pages and ancillary entries
  separately; MDX key count is not article count.
- Every generated internal link and fragment resolves, with no alias loops.
- Every required local resource is present under its referenced MDD path.
- Read back the compiled package and compare content/resources with staging.
  Preserve rendered text, structure and destinations across container conversion;
  text equality alone cannot detect dropped images or formatting.
- Test collision behavior, section links and alias lookup against actual reader
  behavior as well as static checks.

Use focused automated tests for these failure modes. If shared renderer helpers
change, run existing relevant rendering/EPUB regressions and compare the affected
outputs. Do not rebuild or deploy the entire source pipeline solely to package
already-current derived articles.

### 3. Reader verification and release preparation

Test the full edition in GoldenDict-ng: clean installation, initial indexing,
ordinary and ambiguous lookup, full-text search, back navigation, long entries,
math, wide tables, images, and light/dark mode. Record timings and disk footprint
as measurements, not promises. Publish only the tested reader/version claims.

An independent MDX reader is a useful additional test if readily available; it
is not a release dependency. Keep sample and complete release on the same build
path. Prepare the ZIP, instructions, attribution, checksums, and a short lookup
demonstration. Keep the full dictionary's basename stable across releases and
test replacing an older edition and rebuilding its reader indexes.

The first release is complete when the full corpus passes the integrity checks,
works offline in the supported reader, and can be installed from the documented
package. A price, storefront listing, or deployment is separate release work.

## Effort and maintenance

Working estimate: a few focused days for a useful GoldenDict-ng release, subject
to the sample confirming link/resource behavior. Reassess after the sample; do
not quietly expand into a general dictionary framework. Subsequent corrections
should require rerunning this exporter against the updated corpus, reusing asset
caches and the same checks.

Offer the dictionary separately and potentially bundled with the EPUB. Retain
the project's existing attribution/license material; commercial distribution is
compatible with its current CC BY-SA terms, including recipients' redistribution
rights. No new licensing or copy-protection scheme is proposed.

## External references

Checked during the planning discussion, 2026-09-13:

- [GoldenDict-ng supported formats](https://xiaoyifang.github.io/goldendict-ng/dictformats/)
- [GoldenDict-ng full-text indexing](https://xiaoyifang.github.io/goldendict-ng/ui_fulltextsearch/)
- [mdict-utils compiler and reader](https://github.com/liuyug/mdict-utils)
- [writemdict format notes and limitations](https://github.com/zhansliu/writemdict)
- [MDX/MDD version 2 format description](https://github.com/zhansliu/writemdict/blob/master/fileformat.md)
- [GoldenDict MDX implementation, including alias handling](https://github.com/goldendict/goldendict/blob/master/mdx.cc)
- [CC BY-SA 4.0 terms](https://creativecommons.org/licenses/by-sa/4.0/deed.en)

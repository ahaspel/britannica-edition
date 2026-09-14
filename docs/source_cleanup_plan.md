# Source transcription cleanup plan

Proposed 2026-09-12. Planning only; no source edits, rebuild, deployment, or
Wikisource edits have been performed for this plan.

The objective is a more accurate transcription of the printed Britannica, flowing
through the existing pipeline into every edition artifact. The scan is the textual
authority. Wikisource is the collaborative transcription and upstream source;
our correction ledger is the reproducible local overlay.

## What the project already gives us

- `docs/status.md` records a mature, lossless pipeline and 37,225 live articles.
  This campaign builds on that work; rendering cleanup is not its starting point.
- `data/corrections.json` and `src/britannica/corrections.py` already provide
  literal source corrections. `source_pages.load_pages` supplies corrected source
  to readers; `preprocess` also applies corrections to the joined volume stream.
- Scans and `tools/diagnostics/extract_scan.py` exist. Reuse `leaf_for_ws`; never
  invent another page-to-scan offset. Preserve both the Wikisource page number
  and printed page citation, including plate exceptions.
- Existing leads include `missing_period_scan.py`, `triage_render_leaks.py`,
  `propose_brace_corrections.py`, and the source-side findings of
  `mangled_markers.py`. Search `what_answers.py` before adding diagnostics.
- The August 14 status entry records 677 suspect encoding sequences in 58
  articles, concentrated in twenty articles and especially volume 25. These are
  historical leads to recheck, not a newly measured backlog. Its examples show
  why replacing every `Â°` with a degree sign would introduce errors.
- The September status entry reports substantial upstream change since the April
  fetch, including migration to `{{SIC}}`. Those sample estimates do not establish
  today's full-corpus counts or imply that every changed page is improved.

## Editorial rule

Every finding receives one of five dispositions:

| Finding | Action |
|---|---|
| Transcription disagrees with a legible scan | Exact source correction, with scan evidence |
| Printed error or printed inconsistency | Preserve printed text; correction belongs in explicit apparatus |
| Valid historical spelling, unusual terminology, or typography | Preserve; record rejected suggestion to avoid repeated review |
| Sound source rendered incorrectly | Fix the responsible parser/renderer; keep out of the transcription queue |
| Scan does not establish the reading | Leave unresolved; obtain better evidence |

Dates, arithmetic, names, and scientific claims are not corrected merely because
another source or a model says they are wrong. A different digit must be visible
in the scan. Apparatus such as `{{SIC}}` must survive unchanged unless itself
mis-transcribed. Preserve the `{{SIC}}` / invisible `{{sic}}` distinction established
in September.

Audit the existing ledger before treating it as training data or an upstream patch
set. For example, `17:10` and `17:40` explicitly assign an editorial asterisk to
disambiguate contributor initials; `1:775` rearranges caption markup for the
pipeline. Retain existing behavior during this audit, but classify such entries
separately from scan-proven transcription corrections.

## 1. Establish a reproducible baseline

Freeze the current raw-source snapshot and the artifacts actually served by
production. Record the code revision, ledger hash, source manifest, and artifact
hashes. Preserve full before-artifacts, not just hashes: the status history records
why hashes alone were insufficient to adjudicate differences.

Add a staged upstream refresh to the existing batched fetcher. Today it skips
existing files and requests only revision content; it is not an update tracker.
New snapshots should retain page title, revision ID and timestamp, fetch time,
content hash, and explicit missing/error state. Do not label an unreadable API
response as a blank printed page. Old snapshots with no revision ID remain
identified by their actual content hash; do not invent revision provenance.

Compare current local raw text, fresh upstream text, and the local correction
overlay. Account separately for substantive text changes, markup changes, and
proofread-status changes. Retire an active patch only when its exact correction
is demonstrably incorporated upstream, retaining its history. Conflicts go to
review. Do not overwrite the current raw snapshot in place.

Review and build a source refresh as its own batch before measuring the new
cleanup campaign. This credits upstream work accurately and avoids reviewing
errors already fixed there. A limited pilot can proceed against the pinned old
snapshot while the refresh is being assessed, with revision checks before merge.

## 2. Make the correction seam suitable for a larger ledger

The current keys look page-specific, but `apply_corrections(text, volume)` applies
every matching entry throughout the volume with unrestricted `str.replace`.
The corpus is now selectable, but this function does not take a corpus either.
It also cannot report stale or multiply matching patches. Its claim that repeated
application is a no-op needs verification: literal replacement alone does not
guarantee that property.

Extend this existing mechanism, with one owner, to enforce:

- Corpus and exact source page, plus an explicitly declared adjacent-page span
  only when needed for a correction at a seam.
- Literal before/after text, enough context to identify the occurrence, and
  expected match count (normally one).
- Source hash/revision against which the change was adjudicated, scan reference
  and crop coordinates, reason, reviewer, and decision date.
- Explicit outcomes: applied, already incorporated, stale/conflicting, or
  ambiguous. No silent no-op accepted as a successful correction.
- Deterministic application and verified idempotence; detect overlapping or
  interacting patches before they reach a build.

Apply page patches while page identity is still available, before stream joining
and boundary detection. Inspect all callers of the existing correction function
so raw-source readers and the build consume the same corrected text exactly once.
Do not add another correction pass in rendering or exported Markdown.

Migrate existing entries with a full behavior comparison before adding new ones:
some may have relied on volume-wide application. Separate newly discovered
editorial questions from the mechanical migration. The migration gate is unchanged
published content and graphs; the new-corrections gate is explained change.

Keep proposed/rejected/unresolved findings outside the active ledger. Each accepted
correction has a durable ID linking the patch to its evidence and eventual upstream
revision. A small JSONL queue and a generated review report are enough initially.

## 3. Locate trouble spots before spending on OCR

Revised after the user's cost constraint: corpus-wide OCR is not the proposed
discovery method. The first deliverable is a ranked map of suspect passages made
from text already on disk. Scan inspection is a selective verification expense.
No full-source refresh or ledger migration is required to start this read-only
triage against the pinned current corpus.

Build a corpus vocabulary and occurrence index from the existing Markdown/body,
with article context and provenance. Use the encyclopedia as its own historical
lexicon: a rare form close to a frequent form is a lead, especially when both
occur in the same article. Rarity alone is not an error signal in an encyclopedia.
Names, quotations, transliterations, formulae, and bibliographies need separate
handling; a modern dictionary would swamp the queue with legitimate vocabulary.

Run inexpensive detectors locally, in descending initial priority:

1. Known corruption: encoding debris, replacement characters, stray markup, and
   the previously documented source-error clusters.
2. Rare forms explainable by OCR confusions such as `rn/m`, `cl/d`, `I/l/1`,
   `O/0`, or broken/merged words. Require a plausible attested alternative,
   context, or another signal; do not flag every uncommon word.
3. Within-article inconsistencies: one anomalous spelling among repeated mentions
   of a name or term, inconsistent units, or a stray letter in a numeric field.
   Existing title and contributor data provide additional candidate comparisons.
4. Punctuation and continuity anomalies: the existing missing-period detector,
   repeated phrases, abrupt sentence breaks, suspicious word joins, and malformed
   footnote references. Exclude markup syntax using the existing representations.
5. Concentrations of the above within pages and neighboring pages. Upstream
   proofreading status is supporting evidence, never proof of either cleanliness
   or error. Missing status stays unknown rather than inheriting the exporter's
   default of level 3.

Return the exact suspicious passage and the reason, not just an opaque page score.
Initially rank agreement between distinct detectors, strong individual signals,
and anomaly density per prose word. Cap repeated signals from the same defect;
twenty broken bytes in one token are not twenty independent observations. Keep
specialist/non-prose pages separate so mathematical notation does not dominate a
prose anomaly ranking. Deduplicate occurrences without losing their locations.

After reviewing a small batch, rank by measured confirmed errors per page inspected
and reviewer minute. Expand around a confirmed cluster until yield falls; retain
some exploration outside the highest-ranked pages. Adjacent-page corruption is a
hypothesis to test, not a reason to mark a whole volume bad.

Optional later stages, only if the inexpensive ranking leaves useful gaps:

- Inspect whether existing scan archives already contain OCR text or word
  coordinates. Reuse them if available; do not pay to recreate them. Their errors
  may be shared with Wikisource, so agreement does not establish correctness.
- Send only shortlisted prose passages to a text model to rank transcription
  suspicions. Require quoted source spans and reasons; no rewriting. Benchmark
  incremental confirmed discoveries against its cost before expanding its use.
- Use targeted OCR/vision on an implicated crop when necessary. Cache results by
  scan hash, crop, and reader version. Prefer direct visual inspection when the
  proposed letter or punctuation is readily visible. Read a whole page only when
  a cluster or suspected omission justifies it.

The initial report should list article, page, snippet, signal(s), neighboring
cluster, and review outcome. Include detector-level totals and yield. A simple
ranked report is sufficient; building a review application is not a prerequisite.

### Supporting methods and their limits

**Targeted searches, across the whole corpus.** Recheck the known encoding and
markup findings; scan for character confusions, improbable letter/digit mixtures,
word joins and splits, duplicated words, missing punctuation, and inconsistent
spellings within an article. Existing titles, contributor rosters, and repeated
references supply useful consistency signals. They are candidate generators,
never grounds for an automatic replacement.

Use existing exported Markdown/body for linguistic searches, retaining the path
back to the exact source page and literal wikitext. Do not write another
wikitext-to-text stripper. Check the source when attributing a displayed defect.

**Selective independent reading of scans.** When justified, OCR or vision-read the page without first
showing the model the Wikisource transcription. Align that independent reading
with the existing transcription; send disagreements to review. Reading the scan
independently reduces anchoring on the very mistake we are trying to find.

Work by page and column, with a whole-page view to establish reading order and
preserve material spanning columns. Use overlapping context at crop and page
boundaries. Account for headings, footnotes, captions, tables, formulae, and
non-Latin text explicitly; unprocessed regions are coverage gaps. The volume 29
whole/half reading work already demonstrates why a universal crop is inadequate.

Alignment must surface missing or duplicated lines and regions, not just spelling
differences. A second OCR agreeing with Wikisource is not proof: both can make the
same error. When scans differ between the Wikisource and IA copies, establish the
edition and page correspondence before interpreting the difference as a typo.

**Direct proofreading of a random sample.** Review complete sampled pages against
the scans without being confined to flagged disagreements. This measures errors
the detectors miss, including plausible substitutions such as a wrong ordinary
word or year. Spellchecking alone cannot measure transcription fidelity.

## 4. Test whether the ranking finds trouble economically

Suggested initial allocation: 50 pages, with no paid OCR required by default.

- 30 high-ranked pages, spread across detectors rather than all from one cluster.
- 10 neighboring pages around confirmed trouble spots to test clustering.
- 10 randomly selected pages outside the shortlist, chosen before review, as a
  small check on what the ranking overlooks.

Keep the random sample's measurements separate from the enriched samples.
Freeze the initial ranking before review and evaluate tuning on a subsequent
batch. Independently proofread the random sample, including pages on which no
detector reports an error. Ten pages provide a rough check, not a defensible
corpus-wide error estimate; expand this sample only when that estimate is needed.
Use second review for ambiguous/high-impact readings and an audit sample of
accepted and rejected decisions. Model agreement does not replace scan review.

For each proposal, the review packet contains the scan crop plus full-page link,
current source context, proposed literal change, article link, provenance, and
detector reason. Accept, reject, or defer; never force an uncertain reading.

Report:

- Confirmed transcription errors per reviewed page and per 10,000 reviewed words.
- Candidate precision and recall against independently proofread pages, by defect
  class. State sample sizes and uncertainty; do not extrapolate the enriched set.
- Omitted/repeated text and erroneous numbers separately from spelling errors.
- Reviewer minutes and processing cost per page and per accepted correction.
- Confirmed errors per inspected page by ranking band and detector; comparison
  with random-page yield. Count unique corrections, not duplicate detector hits.
- Additional discoveries attributable to any paid text/vision stage, and its
  marginal cost. Stop stages that add little beyond the local detectors.
- Coverage, unreadable regions, unresolved cases, and introduced errors discovered
  by second review.

Use these measurements to choose OCR/vision tooling and project cost; no vendor or
corpus-wide runtime is assumed here. Start with the existing scan/OCR utilities.
If a method generates excessive false alarms, narrow it before scaling.

## 5. Scale in adjudicated batches

First clear the confirmed high-yield clusters. Then continue down the measured
ranking, expanding around productive clusters. Do not automatically graduate to
whole-corpus OCR. Reassess when yield falls below the review effort justified by
the project. Continue small random full-page audits, including already validated
upstream pages. Track
"candidates checked" separately from "page fully proofread".

Automate fetching, crops, candidate generation, alignment, patch validation, and
reports. Initially require scan-backed review for every accepted textual change.
Retain historical vocabulary and rejected candidates by occurrence; a rejected
reading in one context is not a global whitelist.

For each release batch, settle the correction class and inspect all patches before
the full rebuild. Current `CLAUDE.md` specifies full rebuild/full deploy, about
58 minutes; do not base this plan on old partial-rebuild instructions in status.

Compare the full build with the actual production baseline using existing artifact
loaders and gates. Compare identities through the canonical stable-ID machinery,
not database autoincrement IDs (including IDs nested in xrefs). Check:

- Every intended source patch applied at its declared location.
- Every changed article and text span explained by the batch.
- No unexplained loss of text, articles, captions, footnotes, or structure.
- Contributor and topic membership, cross-reference destinations, and public URLs
  unchanged except where an adjudicated correction explicitly requires a change.
- Existing rendering, marker, contributor, and deploy gates pass; changed passages
  are verified in rendered output, including apparatus and specialist typography.

Rebuild the affected distribution artifacts through their existing workflows so
the website, search, download corpus, TEI, and EPUB do not claim the same release
while carrying different source revisions. Version published deposits normally;
do not overwrite a historic edition. Keep a batch manifest and prior release for
rollback. A clean leak report is not a claim that the text is error-free.

## 6. Return verified corrections upstream

Prepare page-level Wikisource diffs from scan-proven transcription repairs only.
Preserve its markup conventions, check the current revision immediately before
editing, and record the resulting revision after acceptance. Do not send local
contributor disambiguation or pipeline accommodations as transcription fixes.

Begin with a small manually reviewed batch. Public edits are a later, explicitly
authorized action. Automated editing additionally requires Wikisource community
approval under its [bot policy](https://en.wikisource.org/wiki/Wikisource:Bots).
Its [proofreading guide](https://en.wikisource.org/wiki/Help:Beginner%27s_guide_to_proofreading)
likewise preserves original spelling and uses apparatus for printed errors;
[proofreading](https://en.wikisource.org/wiki/Help:Proofread) takes place against
scans in the Page namespace.

The local edition can ship verified corrections while upstream review proceeds.
On subsequent refreshes, recognize incorporated fixes and retire their active
overlays without deleting their evidence. This keeps our improvements useful to
Wikisource and prevents a growing, unexamined fork.

## First deliverable and decision gate

The first implementation milestone is the inexpensive corpus-wide anomaly report
and its 50-page ranking evaluation. This can run before changing the ledger or
refreshing upstream. Deliver ranked passages, detector yield, cluster findings,
and rejected/unresolved cases. Harden the ledger before applying accepted patches;
then deliver the scan-backed batch and full artifact diff. Choose further review
and any OCR spending from measured yield, not corpus size.

Success is fewer scan-proven transcription errors with no unexplained collateral
changes, and reproducible evidence for every intervention. No finite detector run
establishes that the whole book is clean.

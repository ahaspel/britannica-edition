# Patches: our words and formulas on Wikisource's pages

Our scan readings beat Wikisource's transcription on words and formulas, and
lose to it on everything a person built on the page: tables, links, footnotes,
images, headings. So Wikisource's page stays the base and only our corrections
are laid on it, as `data/patches.json`. The pages enter the pipeline with the
patches applied (`wikikit.source_pages`), before `corrections.json` and the rest.
A patch whose text no longer stands where it was made fails the load. It never
lands somewhere else.

## The chain

| step | tool | reads | writes |
|---|---|---|---|
| disputes | `disputes.py` | readings, fetched pages | `judge/disputes.json` |
| judge (model) | `judge.py` | disputes, scans | `judge/judge.json` |
| rulings | `rulings.py` | disputes, answers | `judge/rulings.json` |
| words | `build_words.py --loose` | readings, disputes, rulings | `words.json` |
| formulas | `build_formulas.py` | readings, rulings, `vocab.json` | `formulas.json` |
| merge | `merge.py` | words, formulas | `merged.json` |
| filter | `filter_patches.py` | merged | `kept.json` |
| validate | `validate_patches.py` | kept | `validate.json`, `tex.json` |
| KaTeX | `katex_check.py` | tex | `katex_errors.json` |
| faults | `drop_faulted.py` | validate, kept | `data/readings/drop.json` |
| install | `install.py` | kept, drop | `data/patches.json` |

The working files are in `data/staging/patches/`. `build.sh` runs the chain
from `words` on. The first three steps call the model and their results are kept.

- **Words.** A site the judge ruled ours is placed where its Wikisource words
  stand among the agreed words the judge saw on either side.
- **Formulas.** Placed by the PROSE both pages share: real words (`vocab.json`)
  aligned, which OCR salad almost never makes. Each formula of ours lies between
  two aligned words, and Wikisource's text between them becomes ours.
- **Refusals.** A patch is refused if Wikisource's span holds structure, a real
  word would be lost, or a site there was not given to us.

## The checks

1. **Filter.** Each patch, alone, removes a disagreement with our reading and
   creates none. A formula patch that changes only the notation is kept: ours
   stands. No real word may become a non-word.
2. **Validator.** On every patched page, no real word is removed. It also
   collects every formula for KaTeX.
3. **KaTeX.** Every formula renders in the site's KaTeX.
4. **Install.** `wikikit.scan.patches.check` passes: the structure a person
   built is unchanged, and a formula's own display gives way to ours. No
   `corrections.json` entry falls inside a patch.

## The readings

`data/readings/vol_NN/` holds the readings as judged. Each later correction is
recorded in its `provenance.corrected`. There are 399 pages: 317 judged
(`judge/judged.txt`) and 82 read but not judged. The 82 cross columns or have
holes in the scan.

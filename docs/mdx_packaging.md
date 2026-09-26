# Dictionary download packaging

The customer-facing release directory is **`mdx/releases/`**. Other directories
under `mdx/` are build inputs or earlier engineering packages.

| File | Role |
|---|---|
| `Britannica11-MDX.zip` | Main download: conventional MDX/MDD, no installer or runtime. |
| `Britannica11-Enhanced-Windows.zip` | Optional complete alternative with canonical-title search and private runtime. |
| `README.md` | Download comparison, installation and switching instructions. |
| `release.json`, `SHA256SUMS` | Archive identities, sizes and checksums. |

GoldenDict is not bundled. The standard archive contains only the MDX, MDD,
instructions, attribution, manifest, known source-link inventory and checksums.
It uses ordinary aliases; see **Headwords** below for what those put in front of
a reader.

The enhanced edition is a complete alternative with its own MDX, not a helper
to add to the standard dictionary. Customers choose one edition. Its installer
replaces the pair in the selected portable reader's content directory; copies
elsewhere must be removed from the reader's sources to avoid duplicates. Returning
to the standard edition requires disabling the two Programs sources.

Both editions use the same source corpus. The release assembler rejects differing
corpus/index/topic identities, checks every ZIP member against its checksum, rejects
extra or duplicate members, and checks the edition flags and article counts.
Setup still refuses to overwrite a full dictionary with a sample, which now only
protects a QA build rather than a published download.

## Headwords

Every key in an MDX file is a headword, and a `@@@LINK=` redirect is indexed
exactly like a page. There is no hidden lookup key, and no per-dictionary or
per-file override for the reader's *Ignore diacritics* and *Ignore punctuation*
settings — GoldenDict-ng reads those from global Preferences only. So the
headword list IS the interface, and everything in it is a line a reader scrolls.

Three rules, settled 2026-09-25 after a reviewer reported that typing `ABABDA`
returned "No results for ABABDA, did you mean Abābda?".

1. **A stable identifier is never a key.** `EB1911:article:01-0036-dd33a0` and
   its siblings were redirect keys so that hyperlinks kept a fixed address. They
   were also ~40,000 machine ids in the reader's list. Links now carry the
   DISPLAY key instead, and `check_headwords` refuses any key beginning
   `EB1911:`.

2. **An alias that is a PREFIX of its own article's key goes.** `VOLTAIRE`
   beside `VOLTAIRE, FRANÇOIS MARIE AROUET DE` is a second line for one article,
   and there is nothing a reader can type to reach the alias that does not also
   reach the key. 383 corpus-wide, at a cost of no lookup whatever.

   The converse is **not** symmetric and is deliberately kept: `DANTE ALIGHIERI`
   is a prefix sibling of `DANTE`, and dropping the longer spelling would mean
   typing the poet's full name finds nothing — the reviewer's own failure,
   self-inflicted. 467 corpus-wide, left alone.

3. **The accent-free spelling is a key in its own right.** Alias compaction
   groups spellings by a fold that ignores case, punctuation, word order and
   accents, and kept one per group. Case, punctuation and word order a reader
   can reproduce from the keyboard; accents they cannot, and *Ignore diacritics*
   is off by default — a hand-copied `.mdx` never meets the installer that turns
   it on. `compact_aliases` therefore also emits `fold_accents(keep)`: 908
   corpus-wide, including the reported `ABABDA`.

Rules 2 and 3 pull in opposite directions on purpose, and one ruling decides
both: **a redundant line is a lesser defect than a lookup that fails.**

### The display key

A content entry is keyed by its title wherever the title is unambiguous —
34,386 of 37,225 articles. Where it is not, the book's own disambiguation
follows the title:

```
MERCURY — in astronomy, the smallest major planet and the
MERCURY — (Mercurius), in Roman mythology, the god of merchandise
MERCURY — (symbol Hg, atomic weight＝200), in chemistry, a metallic
```

That is what an index entry has always looked like, and it is source-derived, so
it moves only when the text moves. `TITLE (vol. N, p. M)` is the fallback and an
ordinal `(2)` the last resort — an ordinal is the one form that can shift when
an unrelated article is added, silently repointing every link addressed to it.
The gloss is the first eight words of `<div class="body-text">`, the renderer's
own name for the article's prose; reading from `</h1>` instead swept up the
byline and page furniture. A plate carries no words, so it is named by the image
it holds.

## Reproduction

```
python -m britannica.mdx.build --all --output mdx/complete
python -m britannica.mdx.build --all --native-search --output mdx/complete-enhanced
npm ci --prefix tools/mdx-installer --ignore-scripts
python -m britannica.mdx.release
```

`mdx/complete` is the STANDARD edition and `mdx/complete-enhanced` the native-search
one — "complete" means the whole corpus, as against `--sample`. These steps and
`release.py`'s defaults described an earlier scheme (`mdx/standard` plus an
`mdx/complete` that held the enhanced build) for some time after the builds had
moved, so a default-args release would have shipped the standard edition labelled
"Enhanced". Each directory's `manifest.json` records `native_search`; that is the
check when the names look ambiguous. `mdx/standard` is gone (2026-09-21).

13-article samples are no longer published (2026-09-15): a downloads page should
not open with a four-way choice. `build.py --sample` still builds one for QA.

Existing validated builds can be reused. Packaging does not rebuild the website,
change source data, publish downloads, or touch the user's Git history.
The assembler refreshes standard-edition instructions while preserving the
compiled MDX/MDD bytes, so editorial packaging changes do not require another
article build.

The standard format is independent of OS, but reader verification is currently
GoldenDict-ng 26.8.0 on Windows. The optional enhanced download targets portable
GoldenDict on Windows x64. Other readers and operating systems remain unverified.
The shared installer has Mac/Linux profile support, but their runtime packages
and native-reader checks are not part of this release.

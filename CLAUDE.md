# Working in this repo

Short, and only rules whose violation has actually cost time here.

## Before writing any analysis script

**Search first — the reinvention is worse than the original, by default.**
The original has met the corpus's exceptions; a fresh one has met none.

```
uv run python tools/diagnostics/what_answers.py <words describing the question>
```

60 diagnostics, each docstring naming the question it answers, plus the public
helpers in `src/britannica`. Two seconds. Reinventions here have produced: an
alias audit reporting pairs "broken" that the real gate accepts, leaf-offset
arithmetic raising a production alarm with no instance behind it, and a wikitext
stripper that ate 73% of a page and made a 97%-accurate OCR read as 42%.

Specifically:

- **Load the corpus with `britannica.export.corpus.load_corpus`**, never by
  globbing `data/derived/articles/*.json`. It treats a payload missing
  `id`/`body` as a FAILURE rather than a silent skip.
- **Never write wikitext→text.** Exported articles already carry `body` and
  `markdown`, stripped properly. Touch raw wikitext only when the question is
  genuinely about the SOURCE.
- **Import, don't re-derive**: `leaf_for_ws`, `_clean_name`,
  `_split_name_creds`, `canonical_name` are public because they are THE answer
  to their question. Re-deriving a page→leaf offset is explicitly forbidden —
  it produced wrong, confusing numbers and the corpus-wide check was settled
  twice already.
- When a reconstruction disagrees with the real instrument, **the
  reconstruction is wrong** until proven otherwise.

## Rebuilds

A full rebuild is ~58 minutes. There is no partial rebuild and no partial
deploy.

- **Settle what goes in BEFORE launching.** "Accumulate all changes" means go
  looking for the rest of the class first, not batching whatever you happen to
  hold. Read-only audits are free; a rebuild is an hour.
- **Never kill a running rebuild.** `kill` on `rebuild_all.sh` takes the shell;
  the phase's Python child keeps running with the log handle and will write
  into the database the relaunch is about to truncate. If one must be abandoned,
  wait for the log's mtime to go quiet first.
- **Pre-flight the gates that can stop it at minute 52:**
  `uv run python tools/diagnostics/check_dedup_candidates.py` —
  `contributor_aliases.json` keys adjudications by exact name STRING, so any
  change to name shape silently invalidates one.
- Launch with `nohup … > rebuild_NAME.log 2>&1 &`; never `tee`.

## Shell

- **Bash only, never PowerShell.**
- **Never put Python in a heredoc.** Backslashes get mangled — `\b` became a
  literal backspace byte twice, silently producing wrong answers. Write the
  script to a file and run it.

## Source fidelity

- A source typo goes in `data/corrections.json`; a parser-spec mismatch is a
  code fix. Never conflate them.
- The roster's contributor names come from the BOOK — the per-volume front
  matter and the vol 29 index. A footer's name is the transcriber's, not the
  page's: an article is signed with initials alone.
- Before offering a correction upstream to Wikisource, READ THE SCAN. Ours fixes
  what our pipeline needs; only some of those are Wikisource's errors.

## Conventions

- The user runs `git commit`. Draft the message in the console; never commit
  unless told so in that turn.
- `docs/status.md` is the human-readable state of the project. Read it first.

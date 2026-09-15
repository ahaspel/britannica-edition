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
It uses ordinary aliases; duplicate alias suggestions depend on the reader.

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

## Reproduction

```
python -m britannica.mdx.build --all --output mdx/standard
python -m britannica.mdx.build --all --native-search --output mdx/complete
npm ci --prefix tools/mdx-installer --ignore-scripts
python -m britannica.mdx.release
```

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

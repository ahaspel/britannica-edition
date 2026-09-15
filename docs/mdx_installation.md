# Dictionary installation

The default customer download is now the standard MDX/MDD pair, requiring no
installer. This document describes the optional enhanced-search setup. Current
download names, samples and reproduction: [`mdx_packaging.md`](mdx_packaging.md).

## Shared design

The article files, resources, title index, SQLite article store, search helper,
and installation engine are shared across Windows, macOS and Linux. GoldenDict
is installed separately. Each self-contained download needs the Node runtime
for its OS and processor; recipients do not need a system Node or Python install.

`tools/mdx-installer/install.cjs` owns verification, configuration, copying,
backup and rollback. It uses a pinned XML parser with a lockfile; it preserves
unrelated settings instead of replacing the user's configuration. The Windows
folder-picker executable is only a launcher for this engine.

GoldenDict 26.8.0's configuration locations and dictionary-ID algorithm are
defined in its [configuration source](https://github.com/xiaoyifang/goldendict-ng/blob/v26.8.0/src/config.cc)
and [dictionary source](https://github.com/xiaoyifang/goldendict-ng/blob/v26.8.0/src/dict/dictionary.cc).
The engine supports:

- Portable readers: `portable/config`, dictionaries in `content`, relative-path resource IDs.
- Windows profiles: `%APPDATA%/GoldenDict/config`.
- macOS profiles: `~/.goldendict/config`.
- Linux profiles: existing `~/.goldendict/config`, otherwise the XDG `goldendict/config` location.

For ordinary profiles, the edition is installed under the profile's
`dictionaries/Britannica11` directory and added to the reader's search paths.
Resource IDs use absolute paths. An explicit `--config` handles installations
whose configuration is elsewhere. Mac application bundles are not modified.

The shared engine supports these layouts; **macOS and Linux have not yet been
tested in their readers or supplied as self-contained downloads**. They need
matching runtime bundles, OS-specific launch testing, and actual reader checks.
`Install.command` is the small Unix launcher template. Sandboxed reader packages
also need verification that they can execute the helper and access its files.

## Windows package

Build from the verified native-search edition, without recompiling its articles:

```
npm ci --prefix tools/mdx-installer --ignore-scripts
python -m britannica.mdx.windows --edition mdx/complete
```

The builder uses the selected local Node executable and its accompanying license,
records their identity, bundles the locked XML dependency, and compiles the small
Windows GUI with the installed .NET Framework compiler. Its inputs remain outside
the site's build and search paths.

Output: `mdx/Britannica11-Windows.zip`. Extract the entire ZIP, quit GoldenDict,
double-click `Install Britannica 11.exe`, select a writable portable GoldenDict
folder, and click Install. The extracted setup directory can be removed afterward.
The bundled runtime is copied into `content/search/runtime`; the reader's search
does not depend on the original setup directory or the machine's PATH.

Setup verifies all shipped checksums before copying. It stages replacement files,
saves a configuration backup, and restores the old installation if committing
the update fails. It refuses to proceed while GoldenDict is running. Reinstalling
does not duplicate the search sources. Moving the reader requires rerunning setup
to update its absolute helper paths. Browser configuration remains a separate,
optional step; setup does not replace an existing URI handler.

Shared engine regression checks:

```
node --test tools/mdx-installer/install.test.cjs
```

These cover configuration preservation, repeated installation, resource bindings,
platform profile selection, spaces/Unicode, corrupt input and update rollback.

Windows verification: a fresh install and an update passed with Python and Node
removed from PATH, in a reader folder containing spaces, an ampersand and an
accented character. The installed runtime resolves Jonathan Swift, and the
fresh reader displays his complete article with byline and topic links. The
distribution ZIP is approximately 738 MB. Evidence is recorded under `mdx/` in
`windows-install-qa.json`, `windows-installer.png`, and the isolated installation
reader's log. This is Windows evidence, not a substitute for Mac/Linux testing.

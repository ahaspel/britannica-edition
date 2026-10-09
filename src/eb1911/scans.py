"""The Britannica's page scans, by the SITE's leaf numbering — the one
numbering there is: `scan_map` (ws -> leaf), `printed_pages` (leaf ->
printed) and the site's own scan files (data/derived/scans/volVV_leafLLLL.jpg)
all count by it, so a transcription read from leaf L is read from the very
image the article's page links show.

Most volumes' leaves are the Internet Archive's JP2 leaves, held in
data/raw/ia_scans/ as one zip a volume (tools/fetch/fetch_ia_scans.sh), at
the zip's own numbering; the site shows them downsampled
(tools/diagnostics/extract_scan.py) and the transcriber (`wikikit.scan`)
reads them at full resolution, 2340 px across.  Two volumes are not that:

- Vol 20 is Wikisource's `EB1911 - Volume 20.djvu` (site leaf L = djvu page
  L-1), after the Bengal and Osmania copies were both replaced for quality;
  its leaves exist only as the site's own files, kept at 2400 px across.
- Vol 6's archive copy lacks printed pp. 791-792: the site splices two
  Wikisource page images in as leaves 829-830 and numbers the archive's
  leaves 829 on as 831 on.
"""
from __future__ import annotations

import io
import zipfile
from functools import lru_cache
from pathlib import Path

from PIL import Image

from wikikit.corpora import current_corpus
from wikikit.export.pages import leaf_for_ws

SCAN_DIR = Path("data/raw/ia_scans")

# Leaves that only the site's own scan files hold: a whole volume (None) or a
# set of leaves.
SITE_FILES = {20: None, 6: {829, 830}}
# From a site leaf on, the archive zip's leaf is the site's plus a shift.
ARCHIVE_SHIFT = {6: (831, -2)}


def ia_identifier(vol: int) -> str:
    if vol in (3, 5, 6, 7, 8, 9, 11, 12, 13):
        return f"encyclopaediabrit{vol:02d}chisrich"
    return f"encyclopaediabri{vol:02d}chisrich"


def _site_only(vol: int, leaf: int) -> bool:
    return vol in SITE_FILES and (SITE_FILES[vol] is None or leaf in SITE_FILES[vol])


def _archive_leaf(vol: int, leaf: int) -> int:
    start, shift = ARCHIVE_SHIFT.get(vol, (None, 0))
    return leaf + shift if start is not None and leaf >= start else leaf


@lru_cache(maxsize=None)
def _zip(vol: int) -> zipfile.ZipFile:
    expected = SCAN_DIR / f"{ia_identifier(vol)}_jp2.zip"
    if not expected.exists():
        raise FileNotFoundError(f"no JP2 zip for volume {vol}: {expected}")
    return zipfile.ZipFile(expected)


def leaf_image(vol: int, leaf: int) -> Image.Image:
    """Site leaf `leaf` at the best resolution held."""
    if _site_only(vol, leaf):
        f = current_corpus().derived("scans") / f"vol{vol:02d}_leaf{leaf:04d}.jpg"
        if not f.exists():
            raise KeyError(f"leaf {leaf} of vol {vol} is held only as the site's file, and {f} is missing")
        return Image.open(f)
    z = _zip(vol)
    ident = Path(z.filename).stem.replace("_jp2", "")
    name = f"{ident}_jp2/{ident}_{_archive_leaf(vol, leaf):04d}.jp2"
    if name not in z.namelist():
        raise KeyError(f"leaf {leaf} is not in {Path(z.filename).name}")
    return Image.open(io.BytesIO(z.read(name)))


class NotATextPage(LookupError):
    """A Wikisource page the transcriber must not read: no printed number (a
    plate, a blank), or no one leaf both page maps agree it is."""


@lru_cache(maxsize=None)
def _printed(name: str) -> dict:
    import json
    return json.loads(current_corpus().derived(name).read_text(encoding="utf-8"))


def page_leaf(vol: int, ws_page: int) -> int:
    """The leaf a Wikisource page is read from: the one the reader's scan
    viewer shows for it — its printed number (printed_pages.json), then the
    leaf printing that number (printed_pages_leaf.json) — and the one
    `leaf_for_ws` (scan_map) gives, which must be the same.  Two answers that
    differ, or a page with no printed number, and the page is not read: a
    transcription from a doubtful leaf is a wrong page with our name on it
    (2026-10-07: 13 such, vol 20, 23, 24, 26)."""
    number = _printed("printed_pages.json").get(str(vol), {}).get(str(ws_page))
    if number is None:
        raise NotATextPage(f"vol {vol} ws {ws_page} has no printed number: a plate or a blank")
    leaves = [int(leaf) for leaf, n in _printed("printed_pages_leaf.json").get(str(vol), {}).items()
              if n == number]
    mapped = leaf_for_ws(vol, ws_page)
    if leaves != [mapped]:
        raise NotATextPage(f"vol {vol} ws {ws_page} (p. {number}): the viewer shows leaf "
                           f"{leaves or 'none'}, scan_map says {mapped}")
    return mapped


def page_scan(vol: int, ws_page: int) -> Image.Image:
    return leaf_image(vol, page_leaf(vol, ws_page))


def page_layout(vol: int, ws_page: int):
    """Every page the book transcribes is an article page, printed in two
    columns; the plates, which are not, are never transcribed."""
    from wikikit.scan.layout import PageLayout
    return PageLayout(columns=2)


def page_scan_url(vol: int, ws_page: int) -> str:
    """Where the leaf a transcription was read from is published — what it
    names as its source."""
    leaf = page_leaf(vol, ws_page)
    if vol == 20:
        return f"https://en.wikisource.org/wiki/Page:EB1911_-_Volume_20.djvu/{leaf - 1}"
    if _site_only(vol, leaf):
        return f"https://britannica11.org/data/scans/vol{vol:02d}_leaf{leaf:04d}.jpg"
    return f"https://archive.org/details/{ia_identifier(vol)}/page/n{_archive_leaf(vol, leaf)}"

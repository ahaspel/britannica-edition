"""The Britannica's page scans: the Internet Archive's JP2 leaves, held in
data/raw/ia_scans/ as one zip a volume (tools/fetch/fetch_ia_scans.sh).  The
site shows them downsampled (tools/diagnostics/extract_scan.py); the
transcriber (`wikikit.scan`) reads them at full resolution — 2340 px across,
where Wikisource's DjVu renders 1920.  A Wikisource page becomes its leaf
through the exporter's own `leaf_for_ws`, so a transcription is read from the
very leaf the article's page links show."""
from __future__ import annotations

import io
import zipfile
from functools import lru_cache
from pathlib import Path

from PIL import Image

from wikikit.export.pages import leaf_for_ws

SCAN_DIR = Path("data/raw/ia_scans")


def ia_identifier(vol: int) -> str:
    if vol in (3, 5, 6, 7, 8, 9, 11, 12, 13):
        return f"encyclopaediabrit{vol:02d}chisrich"
    if vol == 20:
        return "10689.10192"
    return f"encyclopaediabri{vol:02d}chisrich"


@lru_cache(maxsize=None)
def _zip(vol: int) -> zipfile.ZipFile:
    ident = ia_identifier(vol)
    expected = SCAN_DIR / f"{ident}_jp2.zip"
    if expected.exists():
        return zipfile.ZipFile(expected)
    for f in SCAN_DIR.iterdir():
        if f.suffix == ".zip" and f"vol{vol:02d}" in f.name.lower():
            return zipfile.ZipFile(f)
    raise FileNotFoundError(f"no JP2 zip for volume {vol} in {SCAN_DIR}")


def leaf_image(vol: int, leaf: int) -> Image.Image:
    """One leaf at the archive's full resolution."""
    z = _zip(vol)
    ident = Path(z.filename).stem.replace("_jp2", "")
    name = f"{ident}_jp2/{ident}_{leaf:04d}.jp2"
    if name not in z.namelist():
        raise KeyError(f"leaf {leaf} is not in {Path(z.filename).name}")
    return Image.open(io.BytesIO(z.read(name)))


def page_scan(vol: int, ws_page: int) -> Image.Image:
    return leaf_image(vol, leaf_for_ws(vol, ws_page))


def page_layout(vol: int, ws_page: int):
    """Every page the book transcribes is an article page, printed in two
    columns; the plates, which are not, are never transcribed."""
    from wikikit.scan.layout import PageLayout
    return PageLayout(columns=2)


def page_scan_url(vol: int, ws_page: int) -> str:
    """The leaf on the Internet Archive — what a transcription names as its
    source."""
    return f"https://archive.org/details/{ia_identifier(vol)}/page/n{leaf_for_ws(vol, ws_page)}"

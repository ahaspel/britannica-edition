"""The Dictionary of National Biography, as a book this engine builds.

Moved out of the engine's corpora.py (wikikit step 4).  Selected with
``WIKIKIT_CORPUS=dnb:DNB``, alongside its database URL.
"""
from __future__ import annotations

from wikikit.corpora import Corpus

# --- how many scanned pages each volume has ----------------------------------
# The DNB's were measured from the DjVu files themselves through the Wikisource
# API, all 71 volumes resolving, 33,824 pages in total.

_DNB_PAGES = {
    1: 504, 2: 472, 3: 474, 4: 472, 5: 462, 6: 490,
    7: 465, 8: 466, 9: 474, 10: 466, 11: 482, 12: 463,
    13: 462, 14: 467, 15: 468, 16: 430, 17: 458, 18: 454,
    19: 453, 20: 454, 21: 452, 22: 460, 23: 460, 24: 468,
    25: 468, 26: 454, 27: 441, 28: 450, 29: 463, 30: 452,
    31: 454, 32: 451, 33: 453, 34: 456, 35: 454, 36: 453,
    37: 476, 38: 461, 39: 461, 40: 457, 41: 463, 42: 470,
    43: 462, 44: 464, 45: 472, 46: 461, 47: 456, 48: 449,
    49: 504, 50: 468, 51: 473, 52: 424, 53: 491, 54: 453,
    55: 494, 56: 459, 57: 467, 58: 477, 59: 465, 60: 475,
    61: 482, 62: 457, 63: 466, 64: 500, 65: 468, 66: 542,
    67: 678, 68: 702, 69: 738, 70: 650, 71: 314,
}

_ROMAN = {1: "I", 2: "II", 3: "III"}


# --- the Dictionary of National Biography -------------------------------------
# Volume numbers are OURS, not the book's, because the pipeline is keyed on
# `volume: int` throughout and the DNB's own numbering restarts at each
# supplement.  The mapping is the corpus profile's whole job.
#
#    1-63  the original 1885-1900 series
#   64-66  the 1901 supplement          (the book calls them Sup. Vol I-III)
#   67-69  the 1912 supplement          (the book calls it the Second Supplement)
#      70  the 1927 supplement          (the Third Supplement, one volume)
#      71  the 1904 Errata
#
# The errata volume is a source in its own right: 314 transcribed pages holding
# 3,469 corrections, each already keyed to its article by a `<section begin=>`
# its transcribers wrote.  We append it as apparatus exactly as Wikisource does
# — the 1885 text stays as printed and the correction travels beside it.
# Rewriting the body would destroy the distinction between what the first
# edition said and what its editors later corrected.

def _dnb_scan(volume: int) -> str:
    if 1 <= volume <= 63:
        return f"Dictionary of National Biography volume {volume:02d}.djvu"
    if 64 <= volume <= 66:
        return f"Dictionary of National Biography. Sup. Vol {_ROMAN[volume - 63]} (1901).djvu"
    if 67 <= volume <= 69:
        return f"Dictionary of National Biography, Second Supplement, volume {volume - 66}.djvu"
    if volume == 70:
        return "Dictionary of National Biography, Third Supplement.djvu"
    if volume == 71:
        return "Dictionary of National Biography. Errata (1904).djvu"
    raise ValueError(f"the DNB has volumes 1-71; got {volume}")


DNB = Corpus(
    key="dnb",
    title="Dictionary of National Biography",
    scan_name=_dnb_scan,
    pages=_DNB_PAGES,
    raw_dir="dnb",
    # Its own roots, so its outputs can never land on EB1911's.
    derived_dir="data/dnb/derived",
    images_dir="data/dnb/images",
)

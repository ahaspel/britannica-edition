"""DjVu page-reference normalization.

Rewrites wikisource-style ``{{raw image|EB1911 - Volume N.djvu/PPPP}}``
references into the canonical local filename
``djvu_volNN_pagePPPP.jpg`` so they match the convention used by
``tools/pipeline/download_djvu_crops.py``.
"""

from __future__ import annotations

import re

_DJVU_PAGE_REF_RE = re.compile(
    # "EB1911 - Volume 24.djvu/1037"  (canonical wikisource page ref)
    # "EB1911 - Volume 20.djvu-694.png"  (typo variant)
    r"EB1911\s+-\s+Volume\s+(\d+)\.djvu[/\-](\d+)(?:\.png)?",
    re.IGNORECASE,
)

def _normalize_djvu_page_refs(text: str) -> str:
    """Rewrite wikisource-style DjVu page references to a canonical
    local filename `djvu_volNN_pagePPPP.jpg`.

    These references appear as `{{raw image|EB1911 - Volume 24.djvu/
    1037}}` (full-page plate, SHIPBUILDING) or `[[File:EB1911 -
    Volume 20.djvu-694.png]]` (typo variant — the `/` was replaced
    with `-` and `.png` appended so it parsed as a File link).
    Neither form is a valid Commons filename; the real content lives
    as a specific page of the volume's `.djvu` file.  The renamed
    filename matches the convention used by `download_djvu_crops.py`
    so a full-page render can be downloaded and served locally."""
    def _rewrite(m: re.Match) -> str:
        vol = int(m.group(1))
        page = int(m.group(2))
        return f"djvu_vol{vol:02d}_page{page:04d}.jpg"
    return _DJVU_PAGE_REF_RE.sub(_rewrite, text)



"""Shared editor-prose reference→article-link overrides.

Loads ``data/reference_link_overrides.json`` — the ONE override list both the
about page and the Reader's Guide consult when the shared
``LinkResolver.resolve_reference`` can't recall a reference on its tight rungs.
Keyed by UPPERCASE reference text; value is a canonical title or a ``.json``
filename pin.  Data, not code — accretes like corrections.json.
"""
from __future__ import annotations

import json
from pathlib import Path

_PATH = Path("data/reference_link_overrides.json")


def load_reference_overrides() -> dict[str, str]:
    if not _PATH.is_file():
        return {}
    data = json.loads(_PATH.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


REFERENCE_OVERRIDES: dict[str, str] = load_reference_overrides()

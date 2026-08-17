"""The `{{EB1911 contributor table/entry}}` front-matter grammar.

Each volume's front matter carries a contributor table: one entry per person,
holding their initials, name, description, and the subjects they wrote
(`subject1`/`lnksubject1`…).  TWO passes read it and both run in rebuild phase
5.4 — `tools/pipeline/build_contributor_table.py` builds the contributor rows,
`britannica.contributors.link_frontmatter` binds their subjects to articles.

Each carried its own reader: the same `_parse_field` byte-for-byte, plus its own
`_iter_entries` and its own spelling of the entry marker (one a literal, one a
compiled pattern).  They agreed on the 5,178 entries in the corpus, which is
precisely how a duplicate survives long enough to drift.
"""
from __future__ import annotations

import re
from typing import Iterator

from britannica.wikitext import iter_template_bodies

ENTRY_OPEN = re.compile(r"\{\{EB1911 contributor table/entry")


def iter_entries(text: str) -> Iterator[str]:
    """The brace-balanced inner content of each contributor-table entry."""
    for _offset, body in iter_template_bodies(text, ENTRY_OPEN):
        yield body


def parse_field(content: str, field_name: str) -> str:
    """One `| field = value` from an entry's body; `""` when absent.

    The value runs to the next top-level `|` at the start of a line, so a value
    may itself contain pipes (a linked subject does).
    """
    m = re.search(
        rf"\|\s*{field_name}\s*=\s*(.*?)(?=\n\s*\||\Z)", content, re.DOTALL
    )
    return m.group(1).strip() if m else ""

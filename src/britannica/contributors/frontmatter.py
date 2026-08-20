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

from britannica.wikitext import iter_template_bodies, template_param

ENTRY_OPEN = re.compile(r"\{\{EB1911 contributor table/entry")


def iter_entries(text: str) -> Iterator[str]:
    """The brace-balanced inner content of each contributor-table entry."""
    for _offset, body in iter_template_bodies(text, ENTRY_OPEN):
        yield body


def parse_field(content: str, field_name: str) -> str:
    """One `| field = value` from an entry's body; `""` when absent.

    Split on TOP-LEVEL pipes, which is what separates the parameters — a pipe
    inside `[[Subject|Display]]` or a nested template is content, and
    `split_top_pipes` already knows that.

    The regex this replaces ended a value at the next pipe THAT BEGAN A LINE
    (`(?=\\n\\s*\\|)`), a layout convention rather than a grammar.  Where a
    transcriber put two parameters on ONE line, the first swallowed the second:
    eleven contributors reached the database with `| brace = «SPAN[style:
    display:inline-block; transform:scaleY(2)…` or `| subject1 = Gynaecology`
    as their DESCRIPTION, and it rendered on contributors.html.  A grammar the
    source obeys beats a layout it merely usually follows
    ([[feedback_hard_means_unencoded_knowledge]]).
    """
    return template_param(content, field_name)

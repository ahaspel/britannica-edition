"""EB1911's contributor-table entry reader (`{{EB1911 contributor table/entry}}`)
on the shared brace walk — split from test_wikitext.py, whose engine half
tests the walk itself."""
from __future__ import annotations

from eb1911.contributors.frontmatter import iter_entries, parse_field


ENTRY = """
{{EB1911 contributor table/entry
| initials = J. D. {{sc|v. d.}} W.
| name = [[Author:Johannes van der Waals|J. D. van der Waals]]
| description = Professor of Physics {{brace2|Amsterdam}}
| subject1 = MOLECULE
| lnksubject2 = [[EB1911:CONDENSATION|CONDENSATION OF GASES]]
}}
"""


def test_entry_reader_survives_nested_templates_in_every_field():
    (body,) = iter_entries(ENTRY)
    assert parse_field(body, "initials") == "J. D. {{sc|v. d.}} W."
    assert parse_field(body, "subject1") == "MOLECULE"
    assert parse_field(body, "lnksubject2") == \
        "[[EB1911:CONDENSATION|CONDENSATION OF GASES]]"
    assert parse_field(body, "nosuchfield") == ""


def test_entry_reader_finds_every_entry_in_a_page():
    assert len(list(iter_entries(ENTRY * 3))) == 3

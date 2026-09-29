"""EB1911's alias harvest must learn nothing from a `{{DNB lkpl}}` citation —
split from test_cross_work_links.py (whose engine half tests that the
citation prints and does not link).  The defect is told there."""
from __future__ import annotations

from collections import defaultdict


def test_alias_table_ignores_dnb_templates():
    """The alias harvest is EB1911-only; a DNB citation teaches it nothing."""
    from eb1911.aliases import _extract_aliases_from_wikitext

    aliases = defaultdict(list)
    _extract_aliases_from_wikitext(
        "''{{DNB lkpl|Walsh, Peter|Dict. Nat. Biog}}''", aliases)

    assert not aliases, f"DNB citation still feeds the EB1911 alias table: {dict(aliases)}"


def test_alias_table_still_learns_eb1911_aliases():
    """Guard on the guard: the harvest is narrowed, not disabled."""
    from eb1911.aliases import _extract_aliases_from_wikitext

    aliases = defaultdict(list)
    _extract_aliases_from_wikitext(
        "{{EB1911 lkpl|Aachen|Aix-la-Chapelle}}", aliases)

    assert dict(aliases) == {"AIX-LA-CHAPELLE": ["AACHEN"]}

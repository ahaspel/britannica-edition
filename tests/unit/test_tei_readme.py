"""The README that ships inside the TEI bundle.

This exists because the README broke a full rebuild.  It quotes BibTeX —
``author = {Haspel, Aaron}`` — and the renderer was ``str.format()``, which
reads those braces as field names and raises ``unexpected '{' in field name``.
Nothing caught it until a two-hour build died at its last phase, because the
README is prose and prose looks like it cannot fail.
"""
import re

from britannica.export._tei_readme import TEI_README


def render(n: int = 37_225) -> str:
    """Exactly what ``download.build_tei_bundle`` does."""
    return TEI_README.replace("ARTICLE_COUNT", f"{n:,}")


def test_it_renders_at_all():
    out = render()
    assert out
    assert "ARTICLE_COUNT" not in out, "a substitution point was left unrendered"


def test_the_count_reaches_the_reader():
    assert render(37_225).count("37,225") == 2


def test_bibtex_survives_intact():
    """The block that broke the build.

    Its braces must arrive at the reader unchanged — including the nested
    ``{TEI}-{P5}``, which is BibTeX's way of protecting capitals from being
    lowercased by a style, and which is exactly the shape ``format`` choked on.
    """
    out = render()
    assert "@dataset{haspel_eb1911_tei," in out
    assert "author    = {Haspel, Aaron}," in out
    assert "{TEI}-{P5}" in out


def test_prose_may_contain_any_braces():
    """The property, not the instance.

    Escaping the braces would also have fixed the build, and would have left the
    next person to add a BibTeX, JSON or LaTeX snippet to discover — from a dead
    build — that they had to double them.  Substitution by token means the
    document can hold anything.
    """
    hostile = TEI_README + '\n{"json": {"nested": [1, 2]}} \\cite{foo{bar}} {n} {0} {}'
    out = hostile.replace("ARTICLE_COUNT", "37,225")
    assert "{n}" in out and "{}" in out and "foo{bar}" in out


def test_no_format_placeholders_remain_in_the_template():
    """A guard against reintroducing the old mechanism.

    If someone puts a ``{n}``-style field back into the template, the token
    renderer will not fill it and the reader gets a literal ``{n}``.  Catch that
    here rather than in the shipped bundle.
    """
    body = re.sub(r"@dataset\{.*?\n\s*\}", "", TEI_README, flags=re.S)  # BibTeX is allowed braces
    stray = re.findall(r"\{[a-z_]+(?::[^}]*)?\}", body)
    assert not stray, f"format-style placeholders left in the template: {stray}"

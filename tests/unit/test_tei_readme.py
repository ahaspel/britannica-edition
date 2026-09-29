"""The README that ships inside the TEI bundle.

This exists because the README broke a full rebuild.  It quotes BibTeX —
``author = {Haspel, Aaron}`` — and the renderer was ``str.format()``, which
reads those braces as field names and raises ``unexpected '{' in field name``.
Nothing caught it until a two-hour build died at its last phase, because the
README is prose and prose looks like it cannot fail.

Since wikikit step 2c the README is the BOOK's template
(``data/templates/tei_readme.md``) filled by ``Corpus.template``: ``$name``
placeholders, strict substitution.  The guards below are the same guards,
pointed at the new mechanism.
"""
import re


from eb1911 import EB1911

README = "templates/tei_readme.md"


def render(n: int = 37_225) -> str:
    """Exactly what ``download.build_tei_bundle`` does."""
    return EB1911.template(README, article_count=f"{n:,}", site=EB1911.site,
                           slug=EB1911.slug, concept_doi=EB1911.concept_doi)


def test_it_renders_at_all():
    out = render()
    assert out
    assert "$" not in out, "a placeholder was left unrendered"


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


def test_no_format_placeholders_remain_in_the_template():
    """A guard against reintroducing the old mechanism: a ``{n}``-style field
    would reach the reader literally."""
    text = EB1911.data(README).read_text(encoding="utf-8")
    body = re.sub(r"@dataset\{.*?\n\s*\}", "", text, flags=re.S)  # BibTeX is allowed braces
    # `${slug}` is string.Template's own braced form — only a brace NOT after `$`
    # is a format()-style field.
    stray = re.findall(r"(?<!\$)\{[a-z_]+(?::[^}]*)?\}", body)
    assert not stray, f"format-style placeholders left in the template: {stray}"

"""EB1911's contributor process — who wrote which article.

The Britannica signs an article with INITIALS alone, and names the people
behind them in two indices of its own: the per-volume front-matter tables
and the volume-29 master Index of Contributors.  Binding a byline therefore
means building a roster from those indices (``build_contributor_table``,
``link_vol29_contributors``), harvesting each article's signatures from its
Wikisource footer (``author_links``), crediting the index's subject lists
(``link_frontmatter``, ``vol29_kind_match``), and voting a canonical name —
all orchestrated by ``resolve_contributors_post.bind_contributors``, the
book's ``Corpus.bind_contributors`` hook.

Moved out of the engine (src/wikikit/contributors) and tools/pipeline in
wikikit step 5: no other book signs its articles this way.  The engine keeps
what any roster needs — the name/initials matcher (``contributors.resolver``),
name cleaning and slugs (``contributors.names``), and the declared alias file
(``contributors.aliases``).
"""

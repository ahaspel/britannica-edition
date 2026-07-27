"""epub.pack unit tests — namespacing, section-boundary splitting, chunk resolution.

Synthetic articles mirror the render's real shape (card / body-text / section-head h3 /
footnote asides / trailing xref card); the invariants are the builder's gates in miniature:
ids collision-free, splits text-preserving, every token resolvable.
"""
import re

from britannica.epub import pack


def _article(stem, n_secs=6, sec_words=12, with_fn=True):
    """A namespaced staged article, structurally shaped like render_article output."""
    a = pack.article_anchor(stem)
    body = ""
    for i in range(n_secs):
        body += (f'<h3 class="section-head" id="{a}-section-s{i}">S{i}</h3>'
                 f"<p>sec{i} {'w' + str(i) + ' ' * 1} " + f"word{i} " * sec_words + "</p>")
    fn_sup = (f'<sup class="footnote-ref" id="{a}-fnref-1">'
              f'<a epub:type="noteref" role="doc-noteref" href="#{a}-fn-1">1</a></sup>')
    body = body.replace("</p>", fn_sup + "</p>", 1)   # noteref in section 0
    aside = (f'<aside epub:type="footnote" role="doc-footnote" id="{a}-fn-1"><p>'
             f'<a epub:type="backlink" href="#{a}-fnref-1">1.</a> note text</p></aside>')
    return (f'\n<div class="card" id="{a}"><h1>T {stem}</h1>'
            f'<div class="body-text">{body}</div>{aside}</div>\n'
            f'<div class="card"><h2>Cross-references</h2>'
            f'<ul><li><a href="epublink:{stem}#section-s1">S1</a></li></ul></div>')


def test_namespace_ids_prefixes_and_injects_anchor():
    html = ('<div class="card"><p id="fn-1">x</p>'
            '<a href="#fn-1">y</a>'
            '<template data-popup-id="fnpop-1">z</template>'
            '<svg><path id="MJX-1" clip-path="url(#MJX-1)"/></svg></div>')
    out = pack.namespace_ids(html, "01-0001-abc123")
    a = "a01-0001-abc123"
    assert f'<div class="card" id="{a}">' in out
    assert f'id="{a}-fn-1"' in out
    assert f'href="#{a}-fn-1"' in out
    assert 'data-popup-id="fnpop-1"' in out            # *-id attrs are not ids
    assert 'id="MJX-1"' in out                         # svg internals shielded


def test_split_article_small_passthrough():
    x = _article("01-0002-def456")
    assert pack.split_article(x) == [x]


def test_split_article_sections_preserved():
    stem = "01-0003-a1b2c3"
    x = _article(stem, n_secs=8, sec_words=40)
    pieces = pack.split_article(x, target=2000, hard=3000)
    assert len(pieces) > 1
    # nothing lost, nothing doubled — the bank gate (asides may relocate, only)
    assert pack.split_invariant("".join(pieces)) == pack.split_invariant(x)
    a = pack.article_anchor(stem)
    # the article anchor exactly once, on the first piece
    assert f'id="{a}"' in pieces[0]
    assert sum(p.count(f'id="{a}"') for p in pieces) == 1
    # the aside travels with its noteref's piece
    for p in pieces:
        assert (f'id="{a}-fn-1"' in p) == (f'id="{a}-fnref-1"' in p)
    # the xref card rides last
    assert "Cross-references" in pieces[-1]
    assert all("Cross-references" not in p for p in pieces[:-1])
    # every piece is well-formed XML on its own
    from xml.etree import ElementTree as ET
    for p in pieces:
        ET.fromstring('<r xmlns:epub="http://www.idpf.org/2007/ops">' + p + "</r>")


def test_resolve_chunk_tokens_and_fragments():
    a_here = pack.article_anchor("01-0004-aaaaaa")
    a_there = pack.article_anchor("02-0100-bbbbbb")
    html = (f'<a href="epublink:01-0004-aaaaaa">self</a>'
            f'<a href="epublink:02-0100-bbbbbb#section-x">other sec</a>'
            f'<a href="epublink:99-9999-zzzzzz">absent</a>'
            f'<a href="epubcontrib:smith-john">byline</a>'
            f'<a href="#{a_here}-fn-1">note</a>'
            f'<a href="#{a_there}-fn-2">cross</a>'
            f'<a href="/search.html?q=x">search</a>')
    own = {a_here, f"{a_here}-fn-1"}
    anchor_map = {a_there: "c0007.xhtml", f"{a_there}-section-x": "c0007.xhtml",
                  f"{a_there}-fn-2": "c0007.xhtml", a_here: "c0001.xhtml"}
    out, dangling = pack.resolve_chunk(html, own, anchor_map, {"smith-john": "contributors-02.xhtml"})
    assert f'href="#{a_here}"' in out                                  # in-chunk self
    assert f'href="c0007.xhtml#{a_there}-section-x"' in out            # cross-chunk section
    assert 'href="https://britannica11.org/article/99-9999-zzzzzz"' in out   # absent → site
    assert 'href="contributors-02.xhtml#contrib-smith-john"' in out
    assert f'href="#{a_here}-fn-1"' in out                             # same-chunk fragment kept
    assert f'href="c0007.xhtml#{a_there}-fn-2"' in out                 # cross-chunk fragment
    assert 'href="https://britannica11.org/search.html?q=x"' in out    # root-relative → absolute
    assert dangling == []
    assert "epublink:" not in out and "epubcontrib:" not in out


def test_resolve_chunk_reports_dangling():
    out, dangling = pack.resolve_chunk('<a href="#nowhere-at-all">x</a>', set(), {}, {})
    assert dangling == ["#nowhere-at-all"]


def test_xhtml5_sanitize_legacy_attrs_and_empty_decls():
    html = ('<table cellpadding="2" cellspacing="0" rules="all" summary="chart" border="1">'
            '<td style="width:;text-align:left">x</td></table>'
            '<p style="width:">cellpadding=1 prose mention</p>')
    out = pack.xhtml5_sanitize(html)
    assert 'data-cellpadding="2"' in out and 'data-rules="all"' in out
    assert 'border="1"' in out                       # border IS valid XHTML5 — untouched
    assert 'style="text-align:left"' in out          # empty decl dropped, real one kept
    assert 'style=""' in out                         # all-empty style emptied
    assert "cellpadding=1 prose mention" in out      # text content untouched


def test_fix_nested_lists_validates():
    from britannica.epub.build import to_xhtml_body
    out = to_xhtml_body("<ul><li>a</li><ul><li>b</li></ul></ul>"
                        "<ul><ul><li>lead</li></ul></ul>")
    from xml.etree import ElementTree as ET
    root = ET.fromstring("<r>" + out + "</r>")
    for ul in root.iter("ul"):
        assert all(c.tag == "li" for c in ul)        # XHTML5: only li under ul
    assert pack.text_of(out) == "a b lead"


def test_fix_phrasing_blocks():
    from britannica.epub.build import to_xhtml_body
    out = to_xhtml_body('<span class="cell-verse">A. Gallery<p>B. Corridor</p>'
                        '<p><p>deep</p></p></span>')
    assert "<p" not in out
    assert 'style="display:block"' in out
    assert pack.text_of(out) == "A. Gallery B. Corridor deep"


def test_xhtml5_sanitize_entity_safe_and_junk_decls():
    # &quot; ends with `;` — a naive decl split cuts inside it (the RSC-016 fatal class)
    html = '<span style="font-family:&quot;Times New Roman&quot;;color:red">x</span>'
    assert pack.xhtml5_sanitize(html) == html
    out = pack.xhtml5_sanitize('<td style="width=5%;nowrap;color:red">x</td>')
    assert 'style="color:red"' in out
    out = pack.xhtml5_sanitize('<td scope="row" colspan="2">x</td>'
                               '<tr colspan="3"><img max-width="100%"/></tr>')
    assert 'data-scope="row"' in out
    assert '<td data-scope="row" colspan="2">' in out       # colspan VALID on td
    assert '<tr data-colspan="3">' in out                    # colspan invalid on tr
    assert 'data-max-width="100%"' in out


def test_fix_phrasing_blocks_structural_children():
    from britannica.epub.build import to_xhtml_body
    out = to_xhtml_body('<span class="small-caps"><table><tbody><tr><td>x</td></tr></tbody></table></span>'
                        '<h3 class="section-head">head<p>swallowed</p></h3>')
    from xml.etree import ElementTree as ET
    root = ET.fromstring("<r>" + out + "</r>")
    kinds = {(p.tag, c.tag) for p in root.iter() for c in p}
    assert ("span", "table") not in kinds                    # wrapper retagged to div
    assert ("h3", "p") not in kinds                          # p → display:block span
    assert 'style="display:inline"' in out
    assert pack.text_of(out) == "x head swallowed"


def test_sanitize_round2_classes():
    # border value ∉ {"", "1"} → data-*; direction:rtl → dir attr + banned props dropped;
    # odd &quot; in a style value is junk; even counts are real quoted strings.
    out = pack.xhtml5_sanitize('<table border="2"><td border="1">x</td></table>')
    assert '<table data-border="2">' in out and '<td border="1">' in out
    out = pack.xhtml5_sanitize('<span style="direction:rtl;unicode-bidi:bidi-override;color:red">x</span>')
    assert 'dir="rtl"' in out and "direction" not in out.replace('dir="rtl"', "")
    assert 'style="color:red"' in out
    out = pack.xhtml5_sanitize('<span style="font-size:92%&quot;">x</span>')
    assert 'style="font-size:92%"' in out
    out = pack.xhtml5_sanitize('<span style="font-family:&quot;Times&quot;">x</span>')
    assert "&quot;Times&quot;" in out


def test_lift_markers_out_of_tags():
    bad = '<tr style="vertical-align:top" <span class="page-marker" data-page="704" data-vol="23"></span> ><td>x</td></tr>'
    out = pack.lift_markers_out_of_tags(bad)
    assert out.startswith('<tr style="vertical-align:top">')
    assert '<span class="page-marker" data-page="704" data-vol="23"></span>' in out


def test_resolve_encodes_quotes_in_external_urls():
    html = '<a href="https://en.wikisource.org/wiki/The_&quot;Narcissus&quot;">x</a>'
    out, _ = pack.resolve_chunk(html, set(), {}, {})
    assert 'href="https://en.wikisource.org/wiki/The_%22Narcissus%22"' in out


def test_round3_classes():
    from britannica.epub.build import to_xhtml_body
    # junk attr name from a mangled tag → dropped at the ET boundary
    out = to_xhtml_body('<tr style="" -- ><td>x</td></tr>')
    assert '-=""' not in out
    # a> structural child: retag keeps the link as data-href, not an invalid div@href
    out = to_xhtml_body('<a href="c1.xhtml#x" class="article-link"><table><tbody><tr><td>t</td></tr></tbody></table></a>')
    assert out.startswith("<div ") and 'data-href="c1.xhtml#x"' in out
    assert ' href="' not in out
    # leaked template braces in a style value → decl dropped
    assert pack.xhtml5_sanitize('<span style="width:400px}};color:red">x</span>').count("width") == 0


def test_epub_title_is_one_searchable_text_node():
    # The site's drop-cap span splits the h1 text ("D" + "YNAMICS"); a reader's text
    # search — the book's only search — can't match across it.  EPUB h1 = plain text.
    from britannica.render.article import _render_title_h1, RenderContext
    site = RenderContext("1", "scans.html", {}, target="site")
    epub = RenderContext("1", "scans.html", {}, target="epub")
    m = "«TITLE:DYNAMICS«/TITLE»"
    assert "<span" in _render_title_h1(m, site)
    assert _render_title_h1(m, epub) == "<h1>DYNAMICS</h1>"


def test_diet_preserves_alpha(tmp_path):
    # v1 dropped the alpha channel (convert composites transparency onto BLACK) —
    # the A article's letterform glyphs shipped as solid-black 140-byte rectangles.
    import io as _io
    import random
    from PIL import Image
    from britannica.epub import images as IMG
    im = Image.new("RGBA", (1400, 500), (0, 0, 0, 0))
    px = im.load()
    rnd = random.Random(7)
    for _ in range(20000):        # noisy strokes so the file exceeds the 12KB skip
        px[rnd.randrange(1400), rnd.randrange(500)] = (10, 10, 10, 255)
    p = tmp_path / "glyph.png"
    im.save(p, "PNG")
    assert p.stat().st_size > 12 * 1024
    out, ext = IMG.diet_image(str(p))
    assert ext == ".png"
    got = Image.open(_io.BytesIO(out)).convert("RGBA")
    assert min(a for *_x, a in got.getdata()) < 128        # transparency survived
    comp = Image.alpha_composite(
        Image.new("RGBA", got.size, (255, 255, 255, 255)), got).convert("L")
    vals = sorted(set(comp.getdata()))
    assert vals[0] < 100 and vals[-1] > 200                # strokes AND background


def test_kindle_style_transforms():
    # Kindle blocks CSS transforms (Previewer publish errors, vol-1 c0010 braces).
    brace = '<span style="display:inline-block; transform:scaleY(8); transform-origin:center">{</span>'
    out = pack.kindle_style_transforms(brace)
    assert "transform" not in out
    assert "font-size:6em" in out                    # capped stretch approximation
    cond = '<span style="transform:scaleX(0.8);display:inline-block">x</span>'
    out = pack.kindle_style_transforms(cond)
    assert "transform" not in out and "font-size" not in out   # fractional: dropped
    assert 'style="display:inline-block"' in out
    plain = '<td style="width:25%">y</td>'
    assert pack.kindle_style_transforms(plain) == plain        # untouched fast path


def test_stamp_img_dims(tmp_path):
    # E00192: ET's rasterizer dies on an image node with no computed dimensions.
    import os
    from PIL import Image
    from britannica.epub.build import stamp_img_dims
    os.makedirs(tmp_path / "images", exist_ok=True)
    Image.new("RGB", (300, 120), (200, 200, 200)).save(tmp_path / "images" / "fig.jpg")
    cache = {}
    out = stamp_img_dims('<p><img src="images/fig.jpg" alt="f" style="max-width:100%"/></p>'
                         '<img src="images/fig.jpg" width="10" height="4"/>'
                         '<img src="https://x/y.png"/>', str(tmp_path), cache)
    assert 'src="images/fig.jpg" alt="f" style="max-width:100%" width="300" height="120"/>' in out
    assert 'width="10" height="4"' in out                      # existing attrs untouched
    assert out.count('width="300"') == 1
    assert '<img src="https://x/y.png"/>' in out               # non-local: untouched


def test_kindle_css_carries_no_transforms():
    # .mirror-h's stylesheet transform sent ALPHABET's 18 mirrored letterforms to
    # Amazon's rasterizer, which dies on bare mirrored text (E00192) and takes the
    # whole book out of Enhanced Typesetting.
    from britannica.epub.build import epub_css
    assert "transform" in epub_css("epub")          # site/epub readers mirror correctly
    assert "transform" not in epub_css("kindle")

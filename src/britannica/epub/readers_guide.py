"""Reader's Guide pages for the EPUB (back matter, after Contributors).

The site tree — hub → 6 parts → 71 chapters (``tools/viewer/readers-guide*.html``,
built from the Gutenberg edition by ``build_readers_guide.py``) — maps 1:1 onto
book pages: ``guide.xhtml`` → ``guide-part-N.xhtml`` → ``guide-ch-NN.xhtml``.
Extraction drops each page's chrome card and keeps the rest of the page div;
guide-internal links are rewritten to the book filenames BEFORE the shared
front-matter adaptation absolutizes what remains.  Article citations
(``/article/{stem}``) leave here as absolute site URLs; the build substitutes
presence-aware internal hrefs once the anchor map exists (absent stems keep the
site URL — the packer's standing policy).
"""
import os
import re

import html5lib

from britannica.epub.front_matter import ROOT, SITE, _adapt, _find_div, _inner_html

_GUIDE_DIR = os.path.join(ROOT, "tools", "viewer")
_CH_RE = re.compile(r"readers-guide-ch([ivxlc]+)-")
_ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100}


def _roman(s):
    total = 0
    for a, b in zip(s, s[1:] + "\0"):
        v = _ROMAN[a]
        total += -v if _ROMAN.get(b, 0) > v else v
    return total


def _chapter_files():
    """All chapter basenames in chapter-number order (numbering is global I..LXXI)."""
    names = [f for f in os.listdir(_GUIDE_DIR)
             if _CH_RE.match(f) and f.endswith(".html")]
    return sorted(names, key=lambda f: _roman(_CH_RE.match(f).group(1)))


def _page_div(path):
    doc = html5lib.parse(open(path, encoding="utf-8").read(),
                         treebuilder="etree", namespaceHTMLElements=False)
    page = _find_div(doc, "page")
    if page is None:
        raise RuntimeError(f"{path}: no <div class='page'>")
    # Drop the site-chrome card (the first card: logo + site nav), keep the rest.
    for el in list(page):
        if el.tag == "div" and "card" in (el.get("class") or "").split():
            page.remove(el)
            break
    # Site analytics tags ride INSIDE the page div on chapter pages; a script
    # element makes the content doc "scripted" and its src a phantom resource.
    for parent in page.iter():
        for child in list(parent):
            if child.tag in ("script", "style", "link"):
                parent.remove(child)
    return page


def _retarget(el, fname_of):
    for a in el.iter("a"):
        h = a.get("href") or ""
        base = h.lstrip("/").split("#")[0]
        if base in fname_of:
            a.set("href", fname_of[base])


def _h1_title(el):
    h1 = next(el.iter("h1"), None)
    return " · ".join(t.strip() for t in h1.itertext() if t.strip()) if h1 is not None else ""


def pages():
    """[(fname, nav title, body HTML, part index | None)] — hub, parts, chapters.

    part index: None for the hub, 1-6 for part pages, and for a chapter the part
    it belongs to (from the part-page listings) so the nav can nest chapters
    under their parts."""
    part_romans = ["i", "ii", "iii", "iv", "v", "vi"]
    chapters = _chapter_files()
    fname_of = {"readers-guide.html": "guide.xhtml"}
    for n, r in enumerate(part_romans, 1):
        fname_of[f"readers-guide-part-{r}.html"] = f"guide-part-{n}.xhtml"
    for i, ch in enumerate(chapters, 1):
        fname_of[ch] = f"guide-ch-{i:02d}.xhtml"

    part_of = {}
    for n, r in enumerate(part_romans, 1):
        p = os.path.join(_GUIDE_DIR, f"readers-guide-part-{r}.html")
        for m in re.finditer(r'href="/?(readers-guide-ch[^"#]+\.html)"',
                             open(p, encoding="utf-8").read()):
            part_of.setdefault(m.group(1), n)

    out = []
    images = {}                       # bundled basename -> absolute source path

    def _emit(basename, title, part):
        el = _page_div(os.path.join(_GUIDE_DIR, basename))
        _retarget(el, fname_of)
        for img in el.iter("img"):
            src = img.get("src") or ""
            if src and "://" not in src and not src.startswith("/"):
                b = os.path.basename(src)
                img.set("src", f"images/{b}")
                images[b] = os.path.join(_GUIDE_DIR, b)
        _adapt(el)
        body = _inner_html(el)
        if not title:
            title = _h1_title(el)
        out.append((fname_of[basename], title, body, part))

    _emit("readers-guide.html", "Reader’s Guide", None)
    for n, r in enumerate(part_romans, 1):
        _emit(f"readers-guide-part-{r}.html", f"Part {['I','II','III','IV','V','VI'][n-1]}", n)
    for ch in chapters:
        _emit(ch, "", part_of.get(ch))
    return out, images

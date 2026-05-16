"""Legacy plate parser — wikitable-based grid extractor.

Production code now uses ``britannica.parsers.plate.parse_plate`` for
plate rendering.  This module is retained because:

  * ``tools/pipeline/check_plate_extraction.py`` imports ``_transform_plate``
    for diagnostic comparison runs.
  * ``tools/diagnostics/plate_rewrite_compare.py`` references it as the
    OLD baseline against which the new parser is graded.

Nothing in the live transform pipeline calls these.  Candidate for
deletion alongside the diagnostic tools when the new parser is
considered settled.
"""

from __future__ import annotations

import re

from britannica.pipeline.stages.transform_articles.body_text import (
    _transform_body_text,
)

def _split_inline_cells(s: str) -> list[str]:
    """Split a wiki-table cell line on top-level ``||`` separators.

    MediaWiki accepts two cell delimiters within a row:
      • ``\\n|`` — one cell per line.
      • ``||``  — multiple cells on one line.

    The split must be aware of ``[[…]]`` link brackets and ``{{…}}``
    template braces so that ``[[Image:X|center|500px|]]`` doesn't get
    chopped at the ``||`` that's actually inside the link's pipe-
    parameter list (well, the link uses single pipes — but we still
    have to mind the brackets in case future markup nests ``||``).
    """
    parts: list[str] = []
    cur: list[str] = []
    depth_brace = 0
    depth_bracket = 0
    i = 0
    while i < len(s):
        if s[i] == "{" and i + 1 < len(s) and s[i + 1] == "{":
            depth_brace += 1
            cur.append("{{")
            i += 2
            continue
        if s[i] == "}" and i + 1 < len(s) and s[i + 1] == "}":
            depth_brace -= 1
            cur.append("}}")
            i += 2
            continue
        if s[i] == "[" and i + 1 < len(s) and s[i + 1] == "[":
            depth_bracket += 1
            cur.append("[[")
            i += 2
            continue
        if s[i] == "]" and i + 1 < len(s) and s[i + 1] == "]":
            depth_bracket -= 1
            cur.append("]]")
            i += 2
            continue
        if (s[i] == "|" and i + 1 < len(s) and s[i + 1] == "|"
                and depth_brace == 0 and depth_bracket == 0):
            parts.append("".join(cur))
            cur = []
            i += 2
            continue
        cur.append(s[i])
        i += 1
    parts.append("".join(cur))
    return parts


def _split_table_cell(part: str) -> str:
    """Strip a table cell's leading style/attribute segment.

    Wiki cell syntax: ``| style="…" | content`` — the first unbracketed
    ``|`` after the cell-start marker separates attributes from content.
    Templates and image-links contain their own ``|`` characters which
    must be ignored.
    """
    depth = 0
    for i, c in enumerate(part):
        if c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
        elif c == "|" and depth == 0:
            return part[i + 1:]
    return part


def _clean_grid_caption(text: str) -> str:
    """Reduce a plate-grid caption cell to its core breed/figure label.

    Cells often carry an attribution wrapped in ``{{smaller|''…''}}``
    followed by ``<br />`` and the actual caption.  Drop the attribution
    and keep the trailing label.
    """
    # If a <br /> separates an attribution from a label, keep the label.
    parts = re.split(r"<br\s*/?>", text, flags=re.IGNORECASE)
    if len(parts) > 1:
        # Last non-empty part is the label
        for p in reversed(parts):
            if p.strip():
                text = p
                break
    # Unwrap formatting templates
    for _ in range(3):
        new = re.sub(
            r"\{\{\s*(?:sc|small-caps|smaller|small|c|center|big|nowrap)"
            r"\s*\|([^{}]*)\}\}",
            r"\1", text, flags=re.IGNORECASE,
        )
        if new == text:
            break
        text = new
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r'«/?[BI]»', '', text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.rstrip(",.|;")


_GRID_TABLE_RE = re.compile(r"\{\|[^\n]*\n(.*?)\n\|\}", re.DOTALL)

def _parse_cell_attrs(part: str) -> tuple[dict, str]:
    """Strip a wiki-cell's leading ``style|attrs`` segment, returning
    ``(attrs_dict, content)``.  Tracks brace/bracket depth so ``|``
    inside templates and image-links isn't mistaken for the
    attrs-vs-content separator."""
    depth = 0
    for i, c in enumerate(part):
        if c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
        elif c == "|" and depth == 0:
            attrs_str = part[:i]
            content = part[i + 1:]
            attrs: dict = {}
            cm = re.search(r'colspan\s*=\s*"?(\d+)"?', attrs_str)
            if cm:
                attrs["colspan"] = cm.group(1)
            return attrs, content.strip()
    return {}, part.strip()


def _wiki_table_cells(body: str):
    """Yield ``(cell_content, attrs_dict)`` for each cell in a wiki
    table body, in document order.  Handles both ``\\n|`` (one cell
    per line) and ``||`` (inline) cell separators."""
    rows = re.split(r"\n\|-+[^\n]*", body)
    for row in rows:
        cell_segments = re.split(r"\n\|(?!\})", "\n" + row)
        for seg in cell_segments:
            if not seg.strip():
                continue
            for inline in _split_inline_cells(seg):
                if not inline.strip():
                    continue
                attrs, content = _parse_cell_attrs(inline)
                if content:
                    yield content, attrs


def _html_table_cells(body: str):
    """Yield ``(cell_content, attrs_dict)`` for each ``<td>`` cell in
    an HTML table body, in document order."""
    for cm in re.finditer(
        r"<td\b([^>]*)>(.*?)</td>",
        body, re.DOTALL | re.IGNORECASE,
    ):
        attrs_str = cm.group(1)
        content = cm.group(2).strip()
        attrs: dict = {}
        am = re.search(r'colspan\s*=\s*"?(\d+)"?', attrs_str)
        if am:
            attrs["colspan"] = am.group(1)
        yield content, attrs


def _extract_pairs_from_cells(
    cells_iter,
) -> tuple[list[tuple[str, str]], list[tuple[str, str | None]]]:
    """Walk plate-table cells in order; classify each as an image
    cell, caption-only cell, or collective legend cell, then return
    image+caption pairs and legend tuples.

    The unifying observation: once a page is known to be a plate,
    every table cell is one of {image, caption-of-an-image, collective
    legend, spacer}.  Images may be paired with captions in three
    ways — row-of-images + row-of-captions (DOG), one-image-and-
    caption-per-cell (SHAKESPEARE Plate II inline), or multiple
    image+caption pairs within a single cell (AEGEAN Plate I bottom
    half).  All three reduce to the same algorithm:

      • Inside each cell, pair every image with the caption text that
        immediately follows it (up to the next image or the end of
        the cell).
      • Cells with no images become caption-only entries; the next
        unmatched image takes the next caption-only entry in order.
      • Cells with ``colspan>1`` and no image are collective legends.
    """
    images: list[tuple[str, str]] = []
    captions: list[str] = []
    legends: list[tuple[str, str | None]] = []

    img_link_re = re.compile(
        r"\[\[(?:File|Image):([^|\]]+)[^\]]*\]\]",
        re.IGNORECASE,
    )

    for cell, attrs in cells_iter:
        img_matches = list(img_link_re.finditer(cell))
        if img_matches:
            for i, m in enumerate(img_matches):
                filename = m.group(1).strip()
                cap_start = m.end()
                cap_end = (
                    img_matches[i + 1].start()
                    if i + 1 < len(img_matches)
                    else len(cell)
                )
                inline = _clean_html_caption(cell[cap_start:cap_end])
                if inline and re.search(r"[A-Za-z]{3,}", inline):
                    # Drop leading "1. " or "Fig. 4.—" prefix the
                    # in-print numbering carries; the rendered figure
                    # already conveys ordering.
                    inline = re.sub(r"^\d+\.\s*", "", inline)
                    inline = re.sub(
                        r"^(?:&mdash;|&ndash;|[—–\-])\s*",
                        "", inline,
                    )
                    inline = re.sub(
                        r"^Fig\.\s*\d+\.?\s*"
                        r"(?:&mdash;|&ndash;|[—–\-])\s*",
                        "", inline, flags=re.IGNORECASE,
                    )
                    images.append((filename, inline))
                else:
                    images.append((filename, ""))
            continue
        text = _clean_html_caption(cell)
        if not text or not re.search(r"[A-Za-z]{4,}", text):
            continue
        try:
            colspan = int(attrs.get("colspan", "1"))
        except ValueError:
            colspan = 1
        if colspan > 1:
            legend, credit = _split_legend_and_credit(cell)
            if legend and re.search(r"[A-Za-z]{3,}", legend):
                legends.append((legend, credit))
            continue
        captions.append(text)

    pairs: list[tuple[str, str]] = []
    cap_idx = 0
    for filename, inline in images:
        if inline:
            pairs.append((filename, inline))
        elif cap_idx < len(captions):
            pairs.append((filename, captions[cap_idx]))
            cap_idx += 1
        else:
            pairs.append((filename, ""))
    return pairs, legends


def _split_legend_and_credit(cell_text: str) -> tuple[str, str | None]:
    """Split a plate-legend cell into ``(legend, credit)``.

    Wikisource transcribers typically place a ``{{smaller|''…''}}`` photo
    credit in the same cell as the collective legend, separated by
    ``<br />`` or ``{{dhr|…}}``.  Pull the credit out first, then
    clean the remainder as the legend.
    """
    credit: str | None = None
    m = re.search(
        r"\{\{smaller\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
        cell_text, re.IGNORECASE,
    )
    if m:
        credit_text = m.group(1)
        credit_text = re.sub(r'«/?[BI]»', '', credit_text).strip(" ()")
        if credit_text:
            credit = credit_text
        cell_text = cell_text.replace(m.group(0), "")
    legend = _clean_grid_caption(cell_text)
    return legend, credit


_TOP_LEGEND_RE = re.compile(
    r"\{\{(?:c|center)\|([^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
    re.IGNORECASE,
)

def _extract_top_legends(
    text: str,
) -> tuple[list[tuple[str, str | None]], list[tuple[str, str]], str]:
    """Extract ``{{c|…}}``/``{{center|…}}`` blocks that sit *outside* any
    wikitable, classifying each as either:

      • A **collective legend** (text only): "PORTRAITS OF SHAKESPEARE",
        "PAINTING".  Returned as ``(legend, credit)``.
      • A **centered image group** (contains ``[[Image:]]``/``[[File:]]``
        links): vol05 CATTLE plates wrap their entire layout in one
        ``{{center|…}}``; vol11/14 wrap a single image.  Routed through
        the unified cell walker to extract image+caption pairs.

    Returns ``(legends, image_pairs, modified_text)``.  Inside-table
    ``{{center|…}}`` hits are skipped via masking so per-image captions
    stay in place for downstream logic.
    """
    legends: list[tuple[str, str | None]] = []
    image_pairs: list[tuple[str, str]] = []
    masked = re.sub(r"\{\|.*?\|\}", "", text, flags=re.DOTALL)
    out_text = text
    for m in _TOP_LEGEND_RE.finditer(masked):
        content = m.group(1)
        if re.search(r"\[\[(?:File|Image):", content, re.IGNORECASE):
            pairs, _ = _extract_pairs_from_cells([(content, {})])
            if pairs:
                image_pairs.extend(pairs)
                out_text = out_text.replace(m.group(0), "", 1)
            continue
        legend, credit = _split_legend_and_credit(content)
        if not legend or not re.search(r"[A-Za-z]{3,}", legend):
            continue
        if re.match(r"^\d+\.\s", legend):
            continue
        legends.append((legend, credit))
        out_text = out_text.replace(m.group(0), "", 1)
    return legends, image_pairs, out_text


def _extract_plate_grid_pairs(
    text: str,
) -> tuple[list[tuple[str, str]], list[tuple[str, str | None]], str]:
    """Extract image+caption pairs and collective legends from plate-grid
    wikitables; return the text with those tables removed.

    Delegates to :func:`_extract_pairs_from_cells` after iterating
    cells via :func:`_wiki_table_cells`."""
    pairs: list[tuple[str, str]] = []
    legends: list[tuple[str, str | None]] = []

    def replace(m: re.Match) -> str:
        body = m.group(1)
        local_pairs, local_legends = _extract_pairs_from_cells(
            _wiki_table_cells(body)
        )
        if local_pairs or local_legends:
            pairs.extend(local_pairs)
            legends.extend(local_legends)
            return ""
        return m.group(0)

    new_text = _GRID_TABLE_RE.sub(replace, text)
    return pairs, legends, new_text


_HTML_TABLE_RE = re.compile(
    r"<table\b[^>]*>(.*?)</table>", re.DOTALL | re.IGNORECASE,
)
_HTML_TD_RE = re.compile(
    r"<td\b[^>]*>(.*?)</td>", re.DOTALL | re.IGNORECASE,
)

def _clean_html_caption(text: str) -> str:
    """Clean an HTML-table plate caption cell, joining ``<br>``-separated
    lines into a single string.

    ``_clean_grid_caption`` keeps only the *last* ``<br>``-segment (the
    breed name in DOG plates).  HTML plates put multi-line captions in a
    single cell — every line is part of the caption — so they all
    have to be preserved.
    """
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    for _ in range(8):
        # Round 1: unwrap known formatting templates (single arg).
        new = re.sub(
            r"\{\{\s*(?:sc|small-caps|smaller|small|c|center|big|nowrap|lh)"
            r"\s*\|([^{}]*)\}\}",
            r"\1", text, flags=re.IGNORECASE,
        )
        # Round 2: for any remaining innermost template, keep its
        # last pipe-separated argument (the convention in MediaWiki
        # display templates: the rendered text is the final arg).
        new = re.sub(
            r"\{\{[^{}]*\|([^{}|]*)\}\}",
            r"\1", new,
        )
        if new == text:
            break
        text = new
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r'«/?[BI]»', '', text)
    text = re.sub(r"<[^>]+>", "", text)
    # Defensive: any wiki-table markers that survived the upstream
    # extractors don't belong in a caption.  Without this, the rare
    # case where outer-table walking went sideways shows up to the
    # reader as ``{| width="100%"`` literal text inside a caption.
    text = re.sub(r"\{\|[^\n]*", "", text)
    text = re.sub(r"\|\}", "", text)
    text = re.sub(r"&mdash;", "—", text)
    text = re.sub(r"&ndash;", "–", text)
    text = re.sub(r"&nbsp;|&emsp;|&ensp;|&thinsp;", " ", text)
    # Numeric entities collapse to a placeholder space rather than the
    # actual codepoint — they're decorative spacing in plate cells, never
    # caption content.
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.rstrip(",.|;")


def _extract_html_grid_pairs(
    text: str,
) -> tuple[list[tuple[str, str]], str]:
    """Extract image+caption pairs from HTML ``<table>`` plate layouts
    and return the text with those tables removed.

    Delegates to :func:`_extract_pairs_from_cells` after iterating
    cells via :func:`_html_table_cells`.
    """
    pairs: list[tuple[str, str]] = []

    def replace(m: re.Match) -> str:
        body = m.group(1)
        local_pairs, _ = _extract_pairs_from_cells(
            _html_table_cells(body)
        )
        if local_pairs:
            pairs.extend(local_pairs)
            return ""
        return m.group(0)

    new_text = _HTML_TABLE_RE.sub(replace, text)
    return pairs, new_text


def _transform_plate(raw_wikitext: str) -> str:
    """Transform a plate page: extract images and numbered captions, pair them.

    Plate pages are image grids with captions — not regular article text.
    No table processing, no text transformation. Just images and captions.
    """
    # Strip noinclude, section tags, comments
    text = re.sub(r"<noinclude>.*?</noinclude>", "", raw_wikitext,
                  flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<section[^>]+>', "", text, flags=re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Pull out collective legends + any centered image-group blocks
    # from outside-table {{c|…}}/{{center|…}} markup.  Top legends
    # (SHAKESPEARE, AMPHITHEATRE) become heading-text; image-group
    # blocks (vol05 CATTLE plates, vol11/14 single-image plates) feed
    # back as image+caption pairs.
    top_legends, top_pairs, text = _extract_top_legends(text)

    # Peel off plate-grid tables (image-row + caption-row).  Returns
    # any colspan-row legends (bottom form: DOG) alongside the pairs.
    wiki_pairs, bottom_legends, text = _extract_plate_grid_pairs(text)

    # HTML <table> plates (SHAKESPEARE Plate I, GLASS Plate II): walk
    # <td> cells in order, classify, pair positionally.
    html_pairs, text = _extract_html_grid_pairs(text)

    grid_pairs = top_pairs + wiki_pairs + html_pairs
    grid_imgs = {fn for fn, _ in grid_pairs}
    legends = top_legends + bottom_legends

    # Extract any remaining (non-grid) images
    images = []
    for m in re.finditer(r"\[\[(?:File|Image):([^|\]]+)", text, re.IGNORECASE):
        fn = m.group(1).strip()
        if fn not in grid_imgs:
            images.append(fn)

    # Extract all numbered captions.
    # Formats: "N. ALL CAPS CAPTION" or "Fig. N.—Mixed case description"
    captions = {}
    # Strip [[File:...]] content before caption search — filenames often
    # contain "Fig. N.—..." embedded in them (EB1911 - Globe - Fig. 18.—
    # The Indian Ocean...jpg), which would otherwise match the caption
    # regex and produce garbage.
    caption_text = re.sub(r"\[\[(?:File|Image):[^\]]*\]\]", "",
                          text, flags=re.IGNORECASE)
    # Format 1: N. ALL CAPS
    for m in re.finditer(r"(?<!\w)(\d+)\.\s+([A-Z][A-Z\s,.:;()\-']+)", caption_text):
        num = int(m.group(1))
        cap = m.group(2).strip().rstrip(",.|;")
        if len(cap) >= 3 and num not in captions:
            captions[num] = cap
    # Format 2: {{sc|Fig.}} N.—description, {{sc|Fig. N.}}—description,
    # or plain Fig. N.—description. Captions may wrap across lines
    # (inside <td> blocks), so capture until </td>, next Fig heading,
    # or newline.
    for m in re.finditer(
        r"(?:\{\{(?:small-caps|sc)\|Fig\.\s*(\d+)\.?\s*\}\}"
        r"|(?:\{\{(?:small-caps|sc)\|Fig\.\}\}|Fig\.)\s*(\d+)\.?)"
        r"\s*[\u2014\u2013\-]\s*"
        r"(.+?)(?=</td>|\|-|\n|\{\{(?:small-caps|sc)\|Fig\.|Fig\.\s*\d+\.|$)",
        caption_text, re.DOTALL,
    ):
        # Number is in group 1 ({{sc|Fig. N.}}) or group 2 ({{sc|Fig.}} N).
        num = int(m.group(1) or m.group(2))
        cap = m.group(3).strip().rstrip(",.|;")
        # Clean wiki markup from caption — unwrap templates that wrap text
        cap = re.sub(r"\{\{(?:uc|sc|nowrap|lang\|[^{}]*)\|([^{}]*)\}\}", r"\1", cap, flags=re.IGNORECASE)
        cap = re.sub(r"\{\{[^{}]*\}\}", "", cap)
        cap = re.sub(r'«/?[BI]»', '', cap)
        cap = re.sub(r"&amp;", "&", cap)
        cap = re.sub(r"\|\}", "", cap)  # stray table close
        cap = re.sub(r"\}\}+", "", cap)  # stray closing braces
        cap = re.sub(r"\s+", " ", cap).strip()
        if len(cap) >= 3 and num not in captions:
            captions[num] = f"Fig. {num}. {cap}"

    # Pair images with captions by keyword matching
    sorted_caps = sorted(captions.items())
    used_images = set()
    unmatched_caps = []
    paired = []

    def _img_words(filename):
        name = filename.rsplit("/", 1)[-1]
        name = re.sub(r"\.jpg$|\.png$", "", name, flags=re.IGNORECASE)
        if " - " in name:
            name = name.rsplit(" - ", 1)[-1]
        return set(re.findall(r"[A-Za-z]{3,}", name.upper()))

    for num, cap in sorted_caps:
        cap_words = set(re.findall(r"[A-Z]{3,}", cap))
        best_img = None
        best_score = 0
        for i, img in enumerate(images):
            if i in used_images:
                continue
            img_words = _img_words(img)
            score = len(cap_words & img_words)
            if score > best_score:
                best_score = score
                best_img = i
        if best_img is not None and best_score > 0:
            used_images.add(best_img)
            paired.append(f"{{{{IMG:{images[best_img]}|{cap}}}}}")
        else:
            unmatched_caps.append((num, cap))

    # Positional fallback: pair unmatched captions with unmatched images in order
    unmatched_imgs = [i for i in range(len(images)) if i not in used_images]
    for j, (num, cap) in enumerate(unmatched_caps):
        if j < len(unmatched_imgs):
            img_idx = unmatched_imgs[j]
            used_images.add(img_idx)
            paired.append(f"{{{{IMG:{images[img_idx]}|{cap}}}}}")
        else:
            paired.append(cap)

    # Add remaining unmatched images
    for i, img in enumerate(images):
        if i not in used_images:
            paired.append(f"{{{{IMG:{img}}}}}")

    # Assemble: legends (with italic credits) → grid pairs → numbered-
    # caption paired images → unmatched images.  Legend text is already
    # ALL-CAPS and stands out as a heading; credit lines render in
    # italics via the «I»…«/I» marker the viewer already understands.
    result_parts = []
    for legend, credit in legends:
        result_parts.append(legend)
        if credit:
            result_parts.append(f"«I»{credit}«/I»")
    for fn, cap in grid_pairs:
        if cap:
            result_parts.append(f"{{{{IMG:{fn}|{cap}}}}}")
        else:
            result_parts.append(f"{{{{IMG:{fn}}}}}")
    result_parts.extend(paired)

    return "\n\n".join(result_parts)



"""The vision-OCR transcription language, and its conversion to HTML.

The two vol-29 ancillary pieces and the Classified Table of Contents
introduction are VISION transcriptions, not wikitext: a small plain-text
convention (`*italic*`, `**bold**`, ALL-CAPS heading lines, `>> ` shoulder
notes, tab-separated abbreviation rows) produced by
`tools/vol29/vision_ocr_ancillary.py`.

This module owns reading that language.  It lives apart from
`build_ancillary_pages` because the Topics page needs the same conversion for
the Classified Table of Contents introduction, and the alternatives were both
worse: copying it, or importing the viewer page builder and with it the entire
render stack for three functions that only touch strings.
"""
import re

from britannica.util.strings import section_slug


_ALLCAPS_LINE = re.compile(r"[A-Z][A-Z .ÆŒ'’-]{2,40}")

def _strip_running_heads(text: str) -> str:
    """Remove the printed page's RUNNING HEADS, rejoining the prose they split.

    The transcription records the page exactly as it reads, so the header at the
    top of each printed page lands in the middle of whatever sentence spans the
    page break: "To help the reader to find / PREFACE / what he wants in the
    quickest and easiest way".  Three of them in the Index preface, one more in
    the abbreviations — every one cutting a sentence in half.

    THE DISCRIMINATOR IS REPETITION, not a list of words.  A standalone all-caps
    line that has already appeared is the page furniture; its first appearance is
    the real heading.  That keeps `LIST OF ABBREVIATIONS` where it is first used
    as a heading, keeps the Index preface's own `INDEX` / `VOLUME XXIX` /
    `PREFACE` title block (which `_drop_leading_title` then removes, on the
    separate ground that it is at the HEAD and the page has its own heading —
    this rule has no opinion about it), and — the
    case a word list would have got wrong — keeps the signatures
    `JANET E. HOGARTH.` and `J. MALCOLM MITCHELL.`, which are all-caps, stand
    alone, and are content.

    Removing the line is not enough: it sits between two blank lines, so deleting
    it alone leaves the sentence split across two paragraphs.  The surrounding
    break is closed as well, which is what rejoins the prose.
    """
    lines = text.split("\n")
    seen: set[str] = set()
    drop: set[int] = set()
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s or not _ALLCAPS_LINE.fullmatch(s):
            continue
        if s in seen:
            drop.add(i)
        else:
            seen.add(s)
    if not drop:
        return text
    out: list[str] = []
    i = 0
    while i < len(lines):
        if i in drop:
            # swallow the blank line before and after, so the prose closes up
            while out and not out[-1].strip():
                out.pop()
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if out and j < len(lines):
                out[-1] = out[-1].rstrip() + " " + lines[j].lstrip()
                i = j + 1
                continue
            i = j
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)

def _drop_leading_title(text: str) -> str:
    """Drop the printed TITLE BLOCK at the head of the transcription.

    Leaf 11 opens with the page's own title furniture — `INDEX`, `VOLUME XXIX`,
    `PREFACE` — which `_strip_running_heads` deliberately KEEPS, because its
    discriminator is repetition and these are first appearances.  They are
    furniture all the same: the page supplies its own heading, so carrying them
    states the title three more times before a word of prose, and the drop-initial
    rule then lands on `INDEX` and renders it as a large `I` followed by `NDEX`.

    The rule is POSITIONAL — every standalone all-caps line before the first line
    of prose — not a list of words, which would have to be extended for the next
    page.  It is the same thing `render_pages` means by `drop_leading_title`, and
    it carries that name so the two paths read as one idea.
    """
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s or _ALLCAPS_LINE.fullmatch(s):
            i += 1
            continue
        break
    return "\n".join(lines[i:])

def _vision_to_html(text: str, drop_leading_title: bool = False) -> tuple[str, list]:
    """Convert vision-OCR transcription to (html, toc).

    The toc is `(section_id, label)` per shoulder heading, the same shape
    `build_preface.build_toc_html` consumes — one contents-list builder for
    both prefaces rather than a second one here."""
    toc: list = []
    text = _strip_running_heads(text)
    if drop_leading_title:
        text = _drop_leading_title(text)
    # Bold markers **text**
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    # Italic markers *text*
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    # Section headings (ALL CAPS lines)
    lines = text.split("\n")
    result = []
    in_abbrev_list = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append("")
            continue
        # Detect abbreviation list entries (tab-separated)
        if "\t" in stripped and not in_abbrev_list:
            # Start of abbreviation table
            result.append('<table class="abbrev-table">')
            in_abbrev_list = True
        if in_abbrev_list:
            if "\t" in stripped:
                parts = stripped.split("\t", 1)
                result.append(f'<tr><td class="abbr">{parts[0]}</td>'
                              f'<td>{parts[1]}</td></tr>')
                continue
            else:
                result.append("</table>")
                in_abbrev_list = False
        # SHOULDER NOTES, on the Editorial Preface's model: a positioned SPAN
        # inside the paragraph, not a block pulled out of it.  In print the note
        # stands in the margin beside the sentence it annotates; an absolutely
        # positioned span sits exactly there and interrupts nothing, which is
        # both more faithful and simpler than lifting it out.  (Emitting a <div>
        # inside a <p> was the original bug — invalid, and it split sentences
        # across three lines.)  Anchored by slug so the contents list can link
        # to it, exactly as `build_preface` does.
        if stripped.startswith(">> "):
            label = re.sub(r"<[^>]+>", "", stripped[3:]).strip().rstrip(".")
            sid = f"section-{section_slug(label)}"
            toc.append((sid, label))
            result.append(
                f'<span class="shoulder-heading" id="{sid}">{stripped[3:]}</span>')
            continue
        result.append(stripped)
    if in_abbrev_list:
        result.append("</table>")

    # Join and make paragraphs from consecutive non-tag lines
    html = "\n".join(result)
    # Split on blank lines for paragraphs
    blocks = re.split(r"\n\n+", html)
    output = []
    pending: list = []      # notes transcribed on their own line, awaiting prose
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if block.startswith("<table") or block.startswith("<tr") or block.startswith("<div"):
            output.append(block)
        elif block.startswith("<h"):
            output.append(block)
        else:
            # The shoulder span stays IN the paragraph — the CSS lifts it into
            # the margin, and it must be inside for `position: absolute` to
            # anchor against `p { position: relative }`.  But it is hoisted to
            # the FRONT of the paragraph, which is where the Editorial Preface
            # always has it: that source marks the note at a paragraph boundary,
            # while this OCR transcription records it wherever the eye met it in
            # the margin — sometimes mid-sentence ("a title such as the /
            # Concordance ideal avoided. / earldom of Derby").  Leading the
            # paragraph puts the note beside the passage it labels, exactly as
            # in print, AND leaves the prose unbroken for reading aloud, copying
            # and search, which an interleaved span does not.
            notes = pending + re.findall(
                r'<span class="shoulder-heading".*?</span>', block, re.S)
            for n in notes:
                block = block.replace(n, " ", 1)
            block = re.sub(r"\s+", " ", block).strip()
            # A note the transcription recorded on a line of its OWN, with blank
            # lines either side, arrives here as a block with no prose in it.
            # Emitting that as its own <p> produced an empty paragraph holding a
            # margin note anchored to nothing, and pushed the passage it labels
            # into the NEXT paragraph — visible in the Index preface as four
            # notes floating a paragraph above their text.  Carry it forward to
            # the paragraph it actually annotates, which is the same place the
            # hoist below puts every other note.
            if not block:
                pending = notes
                continue
            pending = []
            output.append(f"<p>{''.join(notes)}{block}</p>")
    return "\n".join(output), toc

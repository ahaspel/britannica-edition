import re


def reflow_paragraphs(text: str) -> str:
    """Join hard-wrapped lines into paragraphs.

    Single newlines (hard wraps from column breaks) are joined with spaces.
    Double newlines (paragraph breaks) are preserved.
    Table and image markers are passed through unchanged.
    """
    # Protect newlines inside block markers BEFORE paragraph splitting.
    # Without this, a TABLE embedded mid-paragraph has its row-separating
    # newlines joined into one line by the reflow logic below.
    def _protect_newlines(m: re.Match) -> str:
        return m.group(0).replace("\n", "\x02")

    # Marker patterns accept the optional ``[style:\u2026]`` slot the
    # producers may emit (whole-table styling from the source
    # ``{|<attrs>`` opener \u2014 TABLE / VERSE / PRE markers carry this
    # since the table-opener Ts work landed).  Without the optional
    # slot in the lookahead, a styled marker like
    # ``\u00abPRE[style:text-align:center]:\u2026\u00ab/PRE\u00bb`` would NOT match \u2014 the
    # newlines inside it wouldn't be protected, and reflow would flatten
    # the row separators to spaces (TABLE_TO_PRE_FLATTENS_ROWS regression).
    text = re.sub(r"\{\{TABLE.*?\}TABLE\}", _protect_newlines, text, flags=re.DOTALL)
    text = re.sub(r"\{\{VERSE(?:\[style:[^\]]*\])?:.*?\}VERSE\}", _protect_newlines, text, flags=re.DOTALL)
    text = re.sub(r"\{\{LEGEND:.*?\}LEGEND\}", _protect_newlines, text, flags=re.DOTALL)
    text = re.sub(r"\u00abPRE(?:\[style:[^\]]*\])?:.*?\u00ab/PRE\u00bb", _protect_newlines, text, flags=re.DOTALL)
    text = re.sub(r"\u00abOUTLINE:.*?\u00ab/OUTLINE\u00bb", _protect_newlines, text, flags=re.DOTALL)

    paragraphs = re.split(r"\n\n+", text)

    result = []
    for para in paragraphs:
        # Don't reflow table blocks, image markers, or preformatted blocks
        if para.strip().startswith(("{{TABLE", "{{IMG:", "{{VERSE",
                                     "{{LEGEND:", "\u00abPRE", "\u00abOUTLINE:")):
            result.append(para.strip())
            continue

        lines = para.split("\n")
        joined = " ".join(line.strip() for line in lines if line.strip())
        if joined:
            result.append(joined)

    text = "\n\n".join(result)

    # Restore protected newlines within table and verse blocks.
    # Collapse runs of \x02 to a single \n (multiple \x02 would create \n\n
    # which splits the table into separate paragraphs in the viewer).
    def _restore_protected_newlines(m: re.Match) -> str:
        return re.sub(r"\x02+", "\n", m.group(0))

    text = re.sub(
        r"\{\{TABLE.*?\}TABLE\}",
        _restore_protected_newlines,
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\{\{VERSE(?:\[style:[^\]]*\])?:.*?\}VERSE\}",
        lambda m: m.group(0).replace("\x02", "\n"),
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\{\{LEGEND:.*?\}LEGEND\}",
        lambda m: m.group(0).replace("\x02", "\n"),
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\u00abPRE(?:\[style:[^\]]*\])?:.*?\u00ab/PRE\u00bb",
        lambda m: m.group(0).replace("\x02", "\n"),
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\u00abOUTLINE:.*?\u00ab/OUTLINE\u00bb",
        lambda m: m.group(0).replace("\x02", "\n"),
        text,
        flags=re.DOTALL,
    )

    return text

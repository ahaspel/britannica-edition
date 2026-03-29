import re


def reflow_paragraphs(text: str) -> str:
    """Join hard-wrapped lines into paragraphs.

    Single newlines (hard wraps from column breaks) are joined with spaces.
    Double newlines (paragraph breaks) are preserved.
    Table and image markers are passed through unchanged.
    """
    paragraphs = re.split(r"\n\n+", text)

    result = []
    for para in paragraphs:
        # Don't reflow table blocks or image markers
        if para.strip().startswith("{{TABLE:") or para.strip().startswith("{{IMG:"):
            result.append(para.strip())
            continue

        lines = para.split("\n")
        joined = " ".join(line.strip() for line in lines if line.strip())
        if joined:
            result.append(joined)

    text = "\n\n".join(result)

    # Restore protected newlines within table blocks
    text = re.sub(
        r"\{\{TABLE:.*?\}TABLE\}",
        lambda m: m.group(0).replace("\x02", "\n"),
        text,
        flags=re.DOTALL,
    )

    return text

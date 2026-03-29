import re


def reflow_paragraphs(text: str) -> str:
    """Join hard-wrapped lines into paragraphs.

    Single newlines (hard wraps from column breaks) are joined with spaces.
    Double newlines (paragraph breaks) are preserved.
    """
    paragraphs = re.split(r"\n\n+", text)

    result = []
    for para in paragraphs:
        lines = para.split("\n")
        joined = " ".join(line.strip() for line in lines if line.strip())
        if joined:
            result.append(joined)

    return "\n\n".join(result)

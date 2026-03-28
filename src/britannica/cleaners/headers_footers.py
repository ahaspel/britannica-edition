def strip_headers(text: str) -> tuple[str, list[str]]:
    lines = text.splitlines()
    removed: list[str] = []

    if lines:
        first = lines[0].strip()
        if first and len(first) < 60 and first.upper() == first:
            removed.append(first)
            lines = lines[1:]

    return "\n".join(lines), removed
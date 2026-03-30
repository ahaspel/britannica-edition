def strip_headers(text: str) -> tuple[str, list[str]]:
    lines = text.splitlines()
    removed: list[str] = []

    if lines:
        first = lines[0].strip()
        # Strip first line if it's a short all-caps page header,
        # but not if the page looks like a plate (has image markers nearby)
        if (first and len(first) < 60 and first.upper() == first
                and "{{IMG:" not in text[:500]):
            removed.append(first)
            lines = lines[1:]

    return "\n".join(lines), removed
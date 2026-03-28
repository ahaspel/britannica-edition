import re


def fix_hyphenation(text: str) -> tuple[str, list[tuple[str, str]]]:
    changes: list[tuple[str, str]] = []

    def repl(match: re.Match[str]) -> str:
        before = match.group(0)
        after = match.group(1) + match.group(2)
        changes.append((before, after))
        return after

    new_text = re.sub(r"(\w+)-\n(\w+)", repl, text)
    return new_text, changes
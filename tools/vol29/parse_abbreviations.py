"""Parse the vol 29 abbreviation list into a JSON lookup table.

Input:  data/derived/vol29_ancillary.json (rules_and_abbreviations section)
Output: data/derived/abbreviations.json  {"Aby.": "Abyssinia", ...}

The abbreviation list is tab-separated (one entry per line) after
the "LIST OF ABBREVIATIONS" heading.
"""
import json
import re
from pathlib import Path

IN = Path("data/derived/vol29_ancillary.json")
OUT = Path("data/derived/abbreviations.json")


def main() -> None:
    data = json.loads(IN.read_text(encoding="utf-8"))
    text = data["rules_and_abbreviations"]

    # Find the abbreviation list (after the heading).
    marker = "LIST OF ABBREVIATIONS"
    idx = text.find(marker)
    if idx < 0:
        print(f"[error] '{marker}' not found in transcription.")
        return
    abbrev_text = text[idx + len(marker):]

    lookup: dict[str, str] = {}
    for line in abbrev_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Tab-separated: ABBR<tab>EXPANSION
        if "\t" in line:
            parts = line.split("\t", 1)
            abbr = parts[0].strip()
            expansion = parts[1].strip()
            if abbr and expansion:
                lookup[abbr] = expansion
        # Some entries might use multiple spaces instead of tab
        elif "  " in line:
            parts = re.split(r"  +", line, maxsplit=1)
            if len(parts) == 2:
                abbr = parts[0].strip()
                expansion = parts[1].strip()
                if abbr and expansion:
                    lookup[abbr] = expansion

    OUT.write_text(
        json.dumps(lookup, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Parsed {len(lookup)} abbreviations -> {OUT}")


if __name__ == "__main__":
    main()

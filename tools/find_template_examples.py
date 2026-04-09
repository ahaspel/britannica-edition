"""Find examples of wiki templates in raw wikitext with surrounding context."""

import json
import os
import re
import sys

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "wikisource")

TEMPLATES = [
    ("{{ne|...}}", r"\{\{ne\|"),
    ("{{ditto}}", r"\{\{ditto[|}]"),
    ("{{...}}", r"\{\{\.\.\.\}\}"),
    ("{{nop}}", r"\{\{nop\}\}"),
    ("{{clear}}", r"\{\{clear\}\}"),
    ("{{blackletter|...}}", r"\{\{blackletter\|"),
]

MAX_EXAMPLES = 5
CONTEXT_CHARS = 80


def find_examples():
    # Track how many examples found per template
    found = {name: [] for name, _ in TEMPLATES}
    all_done = False

    for vol_dir in sorted(os.listdir(DATA_DIR)):
        if all_done:
            break
        vol_path = os.path.join(DATA_DIR, vol_dir)
        if not os.path.isdir(vol_path):
            continue
        for fname in sorted(os.listdir(vol_path)):
            if all_done:
                break
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(vol_path, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue
            raw = data.get("raw_text", "")
            if not raw:
                continue

            for name, pattern in TEMPLATES:
                if len(found[name]) >= MAX_EXAMPLES:
                    continue
                for m in re.finditer(pattern, raw, re.IGNORECASE):
                    if len(found[name]) >= MAX_EXAMPLES:
                        break
                    start = max(0, m.start() - CONTEXT_CHARS)
                    end = min(len(raw), m.start() + CONTEXT_CHARS * 2)
                    snippet = raw[start:end]
                    # Collapse newlines for readability
                    snippet = snippet.replace("\n", "\\n")
                    loc = f"{vol_dir}/{fname}"
                    found[name].append((loc, snippet))

            # Check if all templates have enough examples
            if all(len(v) >= MAX_EXAMPLES for v in found.values()):
                all_done = True

    # Print results
    for name, _ in TEMPLATES:
        print(f"\n{'='*80}")
        print(f"  {name}  ({len(found[name])} examples found)")
        print(f"{'='*80}")
        for loc, snippet in found[name]:
            print(f"\n  [{loc}]")
            print(f"  ...{snippet}...")
        print()


if __name__ == "__main__":
    find_examples()

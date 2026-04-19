"""Clean up the classified TOC:
1. Remove entries pointing to known OCR-artifact targets (SEE, GENERAL).
2. De-duplicate articles within each TOC node (keep first occurrence).

Writes back in place to data/derived/classified_toc.json.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TOC_FILE = Path("data/derived/classified_toc.json")

# Targets that are always OCR artifacts (section-header bleed, "see also"
# references mistakenly parsed as entries). The article file they point to
# is never contextually appropriate.
ARTIFACT_TARGETS = {"SEE", "GENERAL"}


def clean_node(node, stats):
    articles = node.get("articles", [])
    if articles:
        seen = set()
        filtered = []
        for a in articles:
            target = a.get("target", "")
            filename = a.get("filename")
            if target in ARTIFACT_TARGETS:
                stats["artifacts_removed"] += 1
                continue
            if filename and filename in seen:
                stats["dupes_removed"] += 1
                continue
            seen.add(filename)
            filtered.append(a)
        node["articles"] = filtered
    for ch in node.get("children", []):
        clean_node(ch, stats)
    for sub in node.get("subsections", []):
        clean_node(sub, stats)


def main():
    toc = json.loads(TOC_FILE.read_text(encoding="utf-8"))
    stats = {"artifacts_removed": 0, "dupes_removed": 0}
    for cat in toc["categories"]:
        clean_node(cat, stats)
    TOC_FILE.write_text(
        json.dumps(toc, indent=2, ensure_ascii=False),
        encoding="utf-8")
    print(f"Artifact entries removed: {stats['artifacts_removed']}")
    print(f"Duplicate entries removed: {stats['dupes_removed']}")
    print(f"Wrote {TOC_FILE}")


if __name__ == "__main__":
    main()

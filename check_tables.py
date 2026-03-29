import json, sys
sys.stdout.reconfigure(encoding="utf-8")
from tools.fetch.fetch_wikisource_pages import clean_wikisource_page_text

for pg in [64, 159]:
    with open(f"data/raw/wikisource/vol_01/vol01-page{pg:04d}.json", encoding="utf-8") as f:
        data = json.load(f)
    cleaned = clean_wikisource_page_text(data["raw_text"])

    # Find table markers
    import re
    for m in re.finditer(r"\{\{TABLE:\n.*?\n\}TABLE\}", cleaned, flags=re.DOTALL):
        text = m.group(0)
        print(f"=== Page {pg} table ({len(text)} chars) ===")
        print(text[:500])
        print()
        break

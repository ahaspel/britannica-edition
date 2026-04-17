"""One-off: build a mock LIGHTHOUSE article containing Tables IV-VII
for local viewer inspection while the full rebuild runs."""
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "src")

from britannica.pipeline.stages.transform_articles import _transform_text_v2


def load_page(pn: int) -> str:
    with open(f"data/raw/wikisource/vol_16/vol16-page0{pn}.json", encoding="utf-8") as f:
        return json.load(f)["raw_text"]


parts = []
for pn in (652, 669, 670, 671, 672):
    raw = load_page(pn)
    # Strip noinclude blocks & page headings
    raw = re.sub(r"<noinclude>.*?</noinclude>", "", raw, flags=re.DOTALL)
    parts.append(f"\x01PAGE:{pn}\x01{raw}")

joined = "\n\n".join(parts)
body = _transform_text_v2(joined, 16, 669)

article = {
    "id": 9999999,
    "title": "LIGHTHOUSE (test tables)",
    "volume": 16,
    "page_start": 669,
    "page_end": 672,
    "body": body,
    "article_type": "article",
    "contributors": [],
}

with open("data/derived/articles/9999999-LIGHTHOUSE_TEST.json",
          "w", encoding="utf-8") as f:
    json.dump(article, f, ensure_ascii=False)

print("Wrote mock article: 9999999-LIGHTHOUSE_TEST")
print("View: http://localhost:8000/tools/viewer/viewer.html?article=9999999-LIGHTHOUSE_TEST")
htmltables = re.findall(r"\u00abHTMLTABLE:(.*?)\u00ab/HTMLTABLE\u00bb", body, re.DOTALL)
tables = re.findall(r"\{\{TABLE[H]?:(.*?)\}TABLE\}", body, re.DOTALL)
print(f"HTMLTABLE blocks: {len(htmltables)}, {{TABLE:}} blocks: {len(tables)}")
for i, h in enumerate(htmltables):
    rows = re.findall(r"<tr[^>]*>.*?</tr>", h, re.DOTALL)
    if rows:
        first = rows[0]
        cells = re.findall(r"<td[^>]*>|<th[^>]*>", first, re.IGNORECASE)
        cspans = [int(re.search(r'colspan="?(\d+)', c).group(1))
                  if re.search(r'colspan="?(\d+)', c) else 1 for c in cells]
        print(f"  HTMLTABLE #{i}: {len(rows)} rows, row0 {len(cells)} cells sum_colspans={sum(cspans)}")

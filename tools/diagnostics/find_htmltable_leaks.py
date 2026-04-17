"""List articles flagged by the unhandled_marker_in_htmltable check."""
import glob
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

for f in sorted(glob.glob("data/derived/articles/*.json")):
    if "index.json" in f or "contributors.json" in f:
        continue
    try:
        a = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    body = a.get("body", "")
    for ht in re.findall(
        r"\u00abHTMLTABLE:(.*?)\u00ab/HTMLTABLE\u00bb",
        body, re.DOTALL,
    ):
        stripped = re.sub(
            r"</?(?:table|tr|td|th)(?:\s[^>]*)?>", "", ht)
        stripped = re.sub(
            r"\u00ab/?(?:B|I|SC|FN|MATH)(?::[^\u00ab]*)?\u00bb",
            "", stripped)
        stripped = re.sub(r"\{\{IMG:[^}]*\}\}", "", stripped)
        stripped = re.sub(
            r"\{\{VERSE:.*?\}VERSE\}", "", stripped, flags=re.DOTALL)
        stripped = re.sub(r"\[hieroglyph:[^\]]*\]", "", stripped)
        m1 = re.search(r"\u00ab[^\u00bb]+\u00bb", stripped)
        m2 = "{{" in stripped
        if m1 or m2:
            print(f"\n{a.get('stable_id')} — {a.get('title')}")
            if m1:
                print(f"  unknown «»: {m1.group(0)!r}")
            if m2:
                idx = stripped.find("{{")
                print(f"  unknown {{{{}}}}: {stripped[idx:idx+80]!r}")
            break

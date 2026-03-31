#!/usr/bin/env python3
"""Quick quality check on a single volume."""
import json, re, glob, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")

vol = int(sys.argv[1]) if len(sys.argv) > 1 else 1

issues = Counter()
examples: dict[str, list[str]] = {}

def flag(category, title, detail):
    issues[category] += 1
    if category not in examples:
        examples[category] = []
    if len(examples[category]) < 3:
        examples[category].append(f"  [{title}] {detail[:80]}")

files = sorted(
    f for f in glob.glob("data/derived/articles/*.json")
    if "index.json" not in f and "contributors.json" not in f
)

count = 0
for f in files:
    with open(f, encoding="utf-8") as fh:
        a = json.load(fh)
    if a.get("volume") != vol:
        continue
    count += 1
    title = a["title"]
    body = a.get("body", "")
    if not body:
        continue

    # Check for stray }} not part of IMG or TABLE markers
    check_body = re.sub(r"\{\{IMG:[^}]*\}\}", "", body)
    check_body = re.sub(r"\{\{TABLEH?:.*?\}TABLE\}", "", check_body, flags=re.DOTALL)
    if "}}" in check_body:
        idx = check_body.find("}}")
        flag("stray_braces", title, check_body[max(0,idx-20):idx+10])
    if "{{" in body and "{{IMG:" not in body and "{{TABLE" not in body:
        idx = body.find("{{")
        flag("stray_open_braces", title, body[idx:idx+30])
    if "[[" in body:
        idx = body.find("[[")
        flag("stray_wikilink", title, body[idx:idx+40])
    fn_opens = body.count("\u00abFN:")
    fn_closes = body.count("\u00ab/FN\u00bb")
    if fn_opens != fn_closes:
        flag("unclosed_footnote", title, f"opens={fn_opens} closes={fn_closes}")
    if body.count("{{TABLE") != body.count("}TABLE}"):
        flag("unclosed_table", title, "mismatched")

    bare = re.sub(r"\{\{TABLE.*?\}TABLE\}", "", body, flags=re.DOTALL)
    if " | " in bare and bare.count(" | ") > 3:
        flag("pipe_leak", title, f"{bare.count(' | ')} bare pipes")

print(f"Volume {vol}: {count} articles\n")
for cat, cnt in issues.most_common():
    print(f"{cat}: {cnt}")
    for ex in examples.get(cat, []):
        print(ex)
    print()
if not issues:
    print("No issues found!")

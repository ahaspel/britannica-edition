#!/usr/bin/env python3
"""Scan exported articles for rendering trouble spots."""
import json, re, glob, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")

issues = Counter()
examples: dict[str, list[str]] = {}

def flag(category: str, article_title: str, detail: str):
    issues[category] += 1
    if category not in examples:
        examples[category] = []
    if len(examples[category]) < 3:
        examples[category].append(f"  [{article_title}] {detail[:80]}")

files = sorted(
    f for f in glob.glob("data/derived/articles/*.json")
    if "index.json" not in f and "contributors.json" not in f
)

for f in files:
    with open(f, encoding="utf-8") as fh:
        a = json.load(fh)
    title = a["title"]
    body = a.get("body", "")
    if not body:
        continue

    # Stray wiki markup
    if "{{" in body and not any(m in body for m in ["{{IMG:", "{{TABLE", "{{FN:"]):
        flag("stray_braces", title, body[body.find("{{"):body.find("}}")+2])
    if "}}" in body and "TABLE}" not in body and "IMG:" not in body:
        idx = body.find("}}")
        flag("stray_close_braces", title, body[max(0,idx-20):idx+10])
    if "[[" in body or "]]" in body:
        idx = body.find("[[") if "[[" in body else body.find("]]")
        flag("stray_wikilink", title, body[max(0,idx-10):idx+30])
    if "''" in body:
        flag("stray_wiki_italic", title, body[body.find("''"):body.find("''")+20])

    # Bare HTML tags
    if re.search(r"<[a-z]+[^>]*>", body, re.I):
        m = re.search(r"<[a-z]+[^>]*>", body, re.I)
        flag("html_tag", title, m.group(0))

    # Unclosed markers
    if body.count("{{IMG:") != body.count("}}"):
        pass  # IMG uses }} which appears elsewhere
    if body.count("\u00abFN:") != body.count("\u00ab/FN\u00bb"):
        flag("unclosed_footnote", title, f"opens={body.count(chr(171)+'FN:')} closes={body.count(chr(171)+'/FN'+chr(187))}")
    if body.count("{{TABLE") != body.count("}TABLE}"):
        flag("unclosed_table", title, "mismatched {{TABLE and }TABLE}")

    # Very short body (might be a fragment)
    words = len(body.split())
    if words < 5 and a.get("article_type") == "article":
        flag("tiny_article", title, f"{words} words: {body[:50]}")

    # Body starts with lowercase (possible merge artifact)
    if body and body[0].islower():
        flag("lowercase_start", title, body[:50])

    # Raw marker text visible (rendering failure)
    if "\u00abLN:" in body:
        pass  # expected — link markers
    if "\u00abMATH:" in body:
        pass  # expected — math markers

    # Pipe characters in body (possible table leak)
    bare_body = re.sub(r"\{\{TABLE.*?\}TABLE\}", "", body, flags=re.DOTALL)
    if " | " in bare_body and bare_body.count(" | ") > 3:
        flag("pipe_leak", title, f"{bare_body.count(' | ')} bare pipes")

print(f"Scanned {len(files)} articles\n")
for category, count in issues.most_common():
    print(f"{category}: {count}")
    for ex in examples.get(category, []):
        print(ex)
    print()

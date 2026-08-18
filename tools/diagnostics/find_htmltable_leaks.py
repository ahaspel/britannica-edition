"""List articles flagged by the unhandled_marker_in_htmltable check."""

from britannica.export.corpus import load_corpus
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

# Read through the corpus loader, which is TOTAL: it applies NON_ARTICLE
# itself and RAISES on a file it cannot read, instead of skipping it.  A
# leak finder that skips an article reports it clean — the one failure a
# leak oracle must never have ([[feedback_honesty_surface_failures]]).
for _path, a in sorted(load_corpus()[0].items()):
    f = str(_path)
    body = a.get("body", "")
    for ht in re.findall(
        r"\u00abTABLE:(.*?)\u00ab/TABLE\u00bb",
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

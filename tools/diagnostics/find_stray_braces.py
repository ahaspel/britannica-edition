
from britannica.export.corpus import load_corpus
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

open_hits = 0
close_hits = 0
# Read through the corpus loader, which is TOTAL: it applies NON_ARTICLE
# itself and RAISES on a file it cannot read, instead of skipping it.  A
# leak finder that skips an article reports it clean — the one failure a
# leak oracle must never have ([[feedback_honesty_surface_failures]]).
for _path, a in sorted(load_corpus()[0].items()):
    f = str(_path)
    body = a.get("body", "")
    clean = re.sub(
        r"\u00abTABLE:.*?\u00ab/TABLE\u00bb", "",
        body, flags=re.DOTALL)
    clean = re.sub(
        r"\u00abMATH:.*?\u00ab/MATH\u00bb", "", clean, flags=re.DOTALL)

    has_close = "}}" in clean and "TABLE}" not in clean and "IMG:" not in clean and "VERSE}" not in clean
    has_open = "{{" in clean and not any(
        m in clean for m in ["{{IMG:", "{{TABLE", "{{FN:", "{{VERSE:"])

    if has_close:
        close_hits += 1
        i = clean.rfind("}}")
        print(f"CLOSE: {a.get('stable_id')} — {a.get('title')}")
        print(f"  ctx: {clean[max(0, i-80):i+80]!r}")
    if has_open:
        open_hits += 1
        i = clean.rfind("{{")
        print(f"OPEN: {a.get('stable_id')} — {a.get('title')}")
        print(f"  ctx: {clean[max(0, i-80):i+80]!r}")

print(f"\nTotals — close: {close_hits}, open: {open_hits}")

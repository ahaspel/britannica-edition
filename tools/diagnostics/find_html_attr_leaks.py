
from britannica.export.corpus import load_corpus
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ATTR_RE = re.compile(r"nowrap|colspan|rowspan|cellpadding")

# Read through the corpus loader, which is TOTAL: it applies NON_ARTICLE
# itself and RAISES on a file it cannot read, instead of skipping it.  A
# leak finder that skips an article reports it clean — the one failure a
# leak oracle must never have ([[feedback_honesty_surface_failures]]).
for _path, a in sorted(load_corpus()[0].items()):
    f = str(_path)
    body = a.get("body", "")
    check = re.sub(
        r"\u00abTABLE:.*?\u00ab/TABLE\u00bb", "",
        body, flags=re.DOTALL)
    if ATTR_RE.search(check):
        occs = list(ATTR_RE.finditer(check))
        print(f"\n{a.get('stable_id')} — {a.get('title')} ({len(occs)} matches)")
        for m in occs[:2]:
            i = m.start()
            print(f"  {check[max(0, i-100):i+100]!r}")

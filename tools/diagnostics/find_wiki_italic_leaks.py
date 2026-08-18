"""List articles with stray '' wiki italic markers."""

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
    clean = re.sub(
        r"\u00abTABLE:.*?\u00ab/TABLE\u00bb", "",
        body, flags=re.DOTALL)
    clean = re.sub(
        r"\u00abMATH:.*?\u00ab/MATH\u00bb", "", clean, flags=re.DOTALL)
    if "''" not in clean:
        continue

    occs = [m.start() for m in re.finditer(r"''", clean)]
    print(f"\n{a.get('stable_id')} — {a.get('title')} ({len(occs)} occurrences)")
    for i in occs[:3]:
        lo = max(0, i - 60)
        hi = min(len(clean), i + 80)
        print(f"  ...{clean[lo:hi]!r}...")

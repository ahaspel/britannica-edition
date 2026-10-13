"""merged.json for the filter: the word patches (words.json, kind word)
and the prose-placed formula patches (formulas.json); a word patch
inside a formula patch's span is dropped (the formula patch carries ours
there).  Counts in = out + dropped, or it stops.
Usage: merge.py  (book root)"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from paths import WORK

sys.stdout.reconfigure(encoding="utf-8")
words = json.loads((WORK / "words.json").read_text(encoding="utf-8"))
forms = json.loads((WORK / "formulas.json").read_text(encoding="utf-8"))
out, n_in, n_out, dropped = {}, 0, 0, 0
for stem in sorted(set(words) | set(forms)):
    fs = forms.get(stem, [])
    ws = [x for x in words.get(stem, []) if x["kind"] == "word"]
    n_in += len(fs) + len(ws)
    keep = [x for x in ws if not any(f["start"] <= x["end"] and x["start"] <= f["end"] for f in fs)]
    dropped += len(ws) - len(keep)
    page = sorted(fs + keep, key=lambda x: (x["start"], x["end"]))
    n_out += len(page)
    if page:
        out[stem] = page
assert n_in == n_out + dropped, (n_in, n_out, dropped)
(WORK / "merged.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"{n_in} in, {n_out} out, {dropped} word patches inside a formula patch; {len(out)} pages")

"""merged.json for the filter: the word patches (words.json, kind word),
the prose-placed formula patches (formulas.json) and the table patches
(tables.json, build_tables.py); a word patch inside a formula patch's span,
and a word or formula patch inside a table patch's span, is dropped (the
wider patch carries ours there); a table patch cutting across another is
dropped itself.  Counts in = out + dropped, or it stops.
Usage: merge.py  (book root)"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from paths import WORK

sys.stdout.reconfigure(encoding="utf-8")
words = json.loads((WORK / "words.json").read_text(encoding="utf-8"))
forms = json.loads((WORK / "formulas.json").read_text(encoding="utf-8"))
tables = json.loads((WORK / "tables.json").read_text(encoding="utf-8"))
out, n_in, n_out, dropped = {}, 0, 0, 0
for stem in sorted(set(words) | set(forms) | set(tables)):
    fs = forms.get(stem, [])
    ws = [x for x in words.get(stem, []) if x["kind"] == "word"]
    ts = tables.get(stem, [])
    n_in += len(fs) + len(ws) + len(ts)
    keep = [x for x in ws if not any(f["start"] <= x["end"] and x["start"] <= f["end"] for f in fs)]
    small = fs + keep

    def cuts(t):
        return any(x["start"] < t["end"] and t["start"] < x["end"]
                   and not (t["start"] <= x["start"] and x["end"] <= t["end"]) for x in small)
    ts_keep = [t for t in ts if not cuts(t)]
    small = [x for x in small if not any(t["start"] <= x["start"] and x["end"] <= t["end"] for t in ts_keep)]
    dropped += len(fs) + len(ws) + len(ts) - len(small) - len(ts_keep)
    page = sorted(small + ts_keep, key=lambda x: (x["start"], x["end"]))
    n_out += len(page)
    if page:
        out[stem] = page
assert n_in == n_out + dropped, (n_in, n_out, dropped)
(WORK / "merged.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"{n_in} in, {n_out} out, {dropped} dropped inside a wider patch (or a cutting table); {len(out)} pages")

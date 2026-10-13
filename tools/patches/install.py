"""Install the patch scheme (2026-10-13): Wikisource's page is the base, our
words and formulas laid on it, nothing else.  For every judged page
(judged.txt):

  its validated patches (kept.json, less those in data/readings/drop.json:
  [stem, old text — or its first 60 characters, as the validator quotes it])
  go into data/patches.json, keyed "vol:page"; its supplied page leaves
  data/supplied

The pages the gate holds (not judged) are not touched.  Refuses before
changing anything if a patch fails `wikikit.scan.patches.check` on the
fetched page, or a corrections.json entry falls inside a patched span (it
would stop applying, silently).  Counts in = installed + dropped, or stops.
--dry: install nothing; say whether the result equals data/patches.json.
Usage: install.py [--dry]  (book root)"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from wikikit.corrections import load_corrections
from wikikit.scan.patches import apply_patches, check
from wikikit.source_pages import fetched_text
sys.path.insert(0, str(Path(__file__).parent))
from paths import DROP, PAGES, WORK, reading

judged = PAGES.read_text().split()
ok = json.loads((WORK / "kept.json").read_text(encoding="utf-8"))
drop = set()
if DROP.exists():
    drop = {tuple(x) for x in json.loads(DROP.read_text(encoding="utf-8"))}
corr = load_corrections()
out, problems, t = {}, [], Counter()
for stem in sorted(judged):
    ps_all = ok.get(stem, [])
    ps = [{k: x[k] for k in ("start", "end", "old", "new", "kind")} for x in ps_all
          if not any(stem == s and (x["old"] == pre or (len(pre) >= 60 and x["old"].startswith(pre))) for s, pre in drop)]
    t["dropped"] += len(ps_all) - len(ps)
    t["in"] += len(ps_all)
    if not ps:
        t["pages: Wikisource's as it is"] += 1
        continue
    v, p = int(stem[3:5]), int(stem[-4:])
    raw = fetched_text(v, p) or ""
    bad = check(raw, ps)
    if bad:
        problems.append((stem, bad))
        continue
    patched = apply_patches(raw, ps)
    for c in corr.get(f"{v}:{p}", []):
        if isinstance(c, dict) and c.get("from") in raw and c["from"] not in patched:
            problems.append((stem, [f"correction {c['from'][:40]!r} falls inside a patch"]))
    out[f"{v}:{p}"] = ps
    t["pages: patched"] += 1
    t["installed"] += len(ps)
    t["installed formulas"] += sum(x["kind"] == "formula" for x in ps)
assert t["in"] == t["installed"] + t["dropped"] or problems, dict(t)
print(dict(t))
if problems:
    for x in problems:
        print("PROBLEM", x[0], x[1][:3])
    sys.exit(1)
# the leak check (check_leaks.py) must have run on this kept set, after it was
# made, and flagged nothing unreviewed: no patch changes anything beyond its
# own text (2026-10-13: italics cut by formula patches had shipped)
leaks, kept = WORK / "leaks.json", WORK / "kept.json"
leak_problem = ("leak check not run on the current kept.json" if not leaks.exists()
                or leaks.stat().st_mtime < kept.stat().st_mtime
                else "leak check flags " + ", ".join(sorted(json.loads(leaks.read_text(encoding="utf-8"))))
                if json.loads(leaks.read_text(encoding="utf-8")) else None)
print("leaks:", leak_problem or "none")
if "--dry" in sys.argv:
    # what would be installed, against what is: equal, or the pages that differ
    have = {k: v for k, v in json.loads(Path("data/patches.json").read_text(encoding="utf-8")).items()
            if not k.startswith("_")} if Path("data/patches.json").exists() else {}
    differ = sorted(k for k in set(have) | set(out) if have.get(k) != out.get(k))
    print("equals data/patches.json" if not differ else f"differs from data/patches.json on {len(differ)} "
          f"pages: {differ[:10]}")
    sys.exit(0)
if leak_problem:
    print("REFUSED:", leak_problem)
    sys.exit(1)
doc = {"_doc": "Corrections of WORDS and FORMULAS laid on fetched Wikisource pages, and nothing else "
               "(wikikit.scan.patches): our judged transcription's words where the judge ruled ours, and our "
               "formulas, placed by the prose both pages share; validated (Wikisource's structure unchanged; "
               "creates no disagreement with our reading; no real word made a non-word; every formula renders "
               "in KaTeX).  Built 2026-10-13."}
Path("data/patches.json").write_text(json.dumps({**doc, **out}, ensure_ascii=False, indent=1) + "\n",
                                     encoding="utf-8")
gone = 0
for stem in judged:
    f = Path(f"data/supplied/vol_{stem[3:5]}/{stem}.json")
    if f.exists():
        f.unlink()
        gone += 1
print("data/patches.json:", len(out), "pages;", gone, "supplied pages stepped aside")

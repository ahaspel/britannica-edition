"""Install the patch scheme (2026-10-13): Wikisource's page is the base, our
words and formulas laid on it, nothing else.  For every judged page
(judged.txt):

  its validated patches (kept.json, less those in data/readings/drop.json:
  [stem, old text — or its first 60 characters, as the validator quotes it])
  go into data/patches.json, keyed "vol:page" — unless our own whole page
  ENTERS for it (proofread at the desk, `supplied_replaces_text_at`): then
  Wikisource's page is not read and its patches are not installed.

A supplied page is never deleted here: one the door holds waits in
data/supplied for the desk (2026-10-15), and Wikisource's patched page
stands meanwhile.  (Until then this script deleted every judged page's
supplied page — the 43 waiting for the desk among them.)  Refuses before
changing anything if a patch fails `wikikit.scan.patches.check` on the
fetched page, or a corrections.json entry falls inside a patched span (it
would stop applying, silently).  Counts in = installed + dropped, or stops.
Refuses too — --dry as well, so build.sh fails — if a patch installed now
would be lost with no reason: every one is installed again, or dropped
(drop.json, a person's ruling, the filter's refusal — each printed with its
reason), or its page's own text enters (2026-10-20: 32 installed patches
lost to a reassembly of our pages, silently).  A patch the filter doubts
(`filter_patches.doubt`) waits for a person's ruling at the desk's patch
screen, and Wikisource's text stands meanwhile.
--dry: install nothing; say whether the result equals data/patches.json.
Usage: install.py [--dry]  (book root)"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
from wikikit.corrections import load_corrections
from wikikit.scan.patches import apply_patches, check
from wikikit.scan import supplied
from wikikit.source_pages import fetched_text, prefer
sys.path.insert(0, str(Path(__file__).parent))
from paths import DROP, PAGES, PATCH_RULINGS, WORK, label, reading
from patterns import LEAK_TOGETHER

NOT_READ = "not read (ours enters)"
INSTALLED = Path("data/patches.json")

judged = PAGES.read_text().split()
have = {k: v for k, v in json.loads(INSTALLED.read_text(encoding="utf-8")).items()
        if not k.startswith("_")} if INSTALLED.exists() else {}
ok = json.loads((WORK / "kept.json").read_text(encoding="utf-8"))
# the filter's refusals, as filter_report.json quotes them (80 characters)
refused = {(s, r["old"], r["new"]): r["why"]
           for s, rs in json.loads((WORK / "filter_report.json").read_text(encoding="utf-8")).items() for r in rs}
drop = set()
if DROP.exists():
    drop = {tuple(x) for x in json.loads(DROP.read_text(encoding="utf-8"))}
# a person's ruling at the desk's patch screen is final over every check:
# "drop" is never installed, "keep" is though drop.json or the leak check
# names it, "edit" is installed with the person's own text (tools/desk.py,
# 2026-10-21)
ruled = {(r["stem"], r["old"], r["new"]): r
         for r in json.loads(PATCH_RULINGS.read_text(encoding="utf-8"))} if PATCH_RULINGS.exists() else {}
corr = load_corrections()


def dropped(stem: str, x: dict) -> bool:
    r = ruled.get((stem, x["old"], x["new"]))
    if r:
        return r["ruling"] == "drop"
    return any(stem == s and (x["old"] == pre or (len(pre) >= 60 and x["old"].startswith(pre))) for s, pre in drop)


def waiting(stem: str, x: dict) -> bool:
    """A patch the filter doubts (`filter_patches.doubt`: clean text replaced
    by text unlike it, or many words added) is laid only on a person's ruling
    to keep or edit it; until then Wikisource's text stands."""
    r = ruled.get((stem, x["old"], x["new"]))
    return bool(x.get("doubt")) and not (r and r["ruling"] in ("keep", "edit"))


def laid(stem: str, x: dict) -> dict:
    """The patch as installed: a person's edit in its place, if they made one
    (its own span: the patch's, or wider)."""
    r = ruled.get((stem, x["old"], x["new"]))
    p = {k: x[k] for k in ("start", "end", "old", "new", "kind")}
    return {**p, **r["edit"]} if r and r["ruling"] == "edit" else p


def ours_enters(v: int, p: int) -> bool:
    """Our whole page replaces Wikisource's for this page (`prefer`)."""
    if not supplied.path_for(v, p).exists():
        return False
    ws = fetched_text(v, p)
    d = supplied.read(v, p)
    return prefer({"raw_text": ws} if ws is not None else None, d) is d


out, problems, t, entered = {}, [], Counter(), set()
for stem in sorted(judged):
    ps_all = ok.get(stem, [])
    held = [x for x in ps_all if not dropped(stem, x) and waiting(stem, x)]
    ps = [laid(stem, x) for x in ps_all if not dropped(stem, x) and not waiting(stem, x)]
    t["waiting for a ruling"] += len(held)
    t["dropped"] += len(ps_all) - len(ps) - len(held)
    t["ruled at the desk"] += sum(1 for x in ps_all if (stem, x["old"], x["new"]) in ruled)
    t["edited at the desk"] += sum(1 for x in ps_all if ruled.get((stem, x["old"], x["new"]), {}).get("ruling") == "edit")
    t["in"] += len(ps_all)
    v, p = int(stem[3:5]), int(stem[-4:])
    if ours_enters(v, p):
        entered.add(stem)
        t["pages: ours, proofread"] += 1
        t[NOT_READ] += len(ps)
        continue
    if not ps:
        t["pages: Wikisource's as it is"] += 1
        continue
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
assert t["in"] == t["installed"] + t["dropped"] + t["waiting for a ruling"] + t[NOT_READ] or problems, dict(t)
doubted = {(s, x["old"], x["new"]): x["doubt"] for s, xs in ok.items() for x in xs if x.get("doubt")}
# every installed patch is installed again or has its reason
sig = lambda x: (x["kind"], x["old"], x["new"])
for k, ps in have.items():
    v, p = map(int, k.split(":"))
    stem = f"vol{v:02d}-page{p:04d}"
    again = {sig(x) for x in out.get(k, [])}
    for x in ps:
        if sig(x) in again or dropped(stem, x) or stem in entered:
            continue
        what = f"{x['old'][:50]!r} -> {x['new'][:50]!r}"
        if why := refused.get((stem, x["old"][:80], x["new"][:80])):
            t["installed patches the filter now refuses"] += 1
            print(f"{label(stem)}: installed patch dropped, the filter: {why[:80]} — {what}")
        elif why := doubted.get((stem, x["old"], x["new"])):
            t["installed patches now waiting for a ruling"] += 1
            print(f"{label(stem)}: installed patch held for a ruling, the filter doubts it: {why} — {what}")
        else:
            t["installed patches lost"] += 1
            problems.append((stem, [f"{label(stem)}: an installed patch would be lost, no reason: {what}"]))
print(dict(t))
if problems:
    for x in problems:
        print("PROBLEM", x[0], x[1][:3])
    sys.exit(1)
# the leak check (check_leaks.py) must have run on this kept set, after it was
# made, and flagged nothing unreviewed: no patch changes anything beyond its
# own text (2026-10-13: italics cut by formula patches had shipped)
leaks, kept = WORK / "leaks.json", WORK / "kept.json"


def unruled(stem: str, flagged: list[dict]) -> list[dict]:
    """A page's leak flags no ruling answers: a flagged patch a person ruled
    (leaks.json quotes 200 characters) — and, once each of the page's
    flagged patches is ruled, the flag on its patches together."""
    def ruling(l):
        return next((r for (s, o, n), r in ruled.items() if s == stem and o[:200] == l["old"] and n[:200] == l["new"]),
                    None)
    alone = [l for l in flagged if l["old"] != LEAK_TOGETHER]
    left = [l for l in alone if not ruling(l)]
    return left + ([l for l in flagged if l not in alone] if left or not alone else [])


if not leaks.exists() or leaks.stat().st_mtime < kept.stat().st_mtime:
    leak_problem = "leak check not run on the current kept.json"
else:
    flagged = {s: u for s, ls in json.loads(leaks.read_text(encoding="utf-8")).items() if (u := unruled(s, ls))}
    leak_problem = "leak check flags " + ", ".join(sorted(flagged)) if flagged else None
print("leaks:", leak_problem or "none")
if "--dry" in sys.argv:
    # what would be installed, against what is: equal, or the pages that differ
    differ = sorted(k for k in set(have) | set(out) if have.get(k) != out.get(k))
    print("equals data/patches.json" if not differ else f"differs from data/patches.json on {len(differ)} "
          f"pages: {differ}")
    sys.exit(0)
if leak_problem:
    print("REFUSED:", leak_problem)
    sys.exit(1)
doc = {"_doc": "Corrections of WORDS and FORMULAS laid on fetched Wikisource pages, and nothing else "
               "(wikikit.scan.patches): our judged transcription's words where the judge ruled ours, and our "
               "formulas, placed by the prose both pages share; validated (Wikisource's structure unchanged; "
               "creates no disagreement with our reading; no real word made a non-word; every formula renders "
               "in KaTeX).  Built 2026-10-13."}
INSTALLED.write_text(json.dumps({**doc, **out}, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
print("data/patches.json:", len(out), "pages")

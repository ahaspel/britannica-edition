"""Apply patches.json to Wikisource's pages (in memory) and prove the one
guarantee: every piece of Wikisource's structure — each template, link,
footnote, table, tag and the page header (patch_build.regions' barriers) —
stands in the patched page character for character, in the same order;
only words and formulas changed.  Also: each patch's `old` is found at its
place.  Writes patched_pages.json {stem: patched raw}.
Usage: apply.py [FILE in data/staging/patches, default kept.json]  (book root)"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from paths import WORK
from raw_tokens import regions

from wikikit.source_pages import fetched_text


def structure(text):
    return [text[a:b] for a, b, k in regions(text) if k == "barrier"]


def apply(raw, patches):
    out, pos = [], 0
    for p in sorted(patches, key=lambda x: x["start"]):
        if raw[p["start"]:p["end"]] != p["old"]:
            raise ValueError(f"patch old text not at {p['start']}")
        out.append(raw[pos:p["start"]])
        out.append(p["new"])
        pos = p["end"]
    out.append(raw[pos:])
    return "".join(out)


def main():
    patches = json.loads((WORK / (sys.argv[1] if len(sys.argv) > 1 else "kept.json")).read_text(encoding="utf-8"))
    patched, t = {}, Counter()
    for stem, ps in patches.items():
        v, p = int(stem[3:5]), int(stem[-4:])
        raw = fetched_text(v, p) or ""
        try:
            new = apply(raw, ps)
        except ValueError as e:
            t["pages failed: " + str(e)[:30]] += 1
            continue
        if structure(raw) != structure(new):
            t["pages FAILED: structure changed"] += 1
            print(stem, "structure changed")
            continue
        patched[stem] = new
        t["pages pass"] += 1
        t["patches applied"] += len(ps)
    (WORK / "patched_pages.json").write_text(json.dumps(patched, ensure_ascii=False), encoding="utf-8")
    print(dict(t))


if __name__ == "__main__":
    main()

"""drop.json: the patches the validator faulted for removing a real word
(validate.json, by the old text it quotes), and those named on the
command line as STEM:INDEX (kept.json order) — a combination's fault.
Usage: drop_faulted.py [STEM:INDEX ...]  (book root)"""
import ast
import json
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from paths import DROP, WORK

sys.stdout.reconfigure(encoding="utf-8")
val = json.loads((WORK / "validate.json").read_text(encoding="utf-8"))
ok = json.loads((WORK / "kept.json").read_text(encoding="utf-8"))
lines = []
for stem, probs in val.items():
    for pr in probs:
        m = re.match(r"removes word\(s\) \[[^\]]*\]: (.*)$", pr, re.S)
        if m:
            old = ast.literal_eval(m.group(1))
            hits = [x for x in ok[stem] if x["old"] == old or (len(old) >= 60 and x["old"].startswith(old))]
            assert hits, (stem, old)
            lines.append([stem, old])
for arg in sys.argv[1:]:
    stem, i = arg.split(":")
    lines.append([stem, ok[stem][int(i)]["old"]])
(DROP).write_text(json.dumps(lines, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(lines), "to drop")

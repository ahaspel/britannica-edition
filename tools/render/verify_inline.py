"""Diff the Python inline engine against the viewer reference (inline_ref.json).

    python tools/render/verify_inline.py

Reports each mismatch at its first diverging character.  The render-to-Python port is
green when all cases match (UNEXPECTED=0 for the inline layer).
"""
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))

from britannica.render.inline import decode_inline  # noqa: E402

ref = json.load(open(os.path.join(ROOT, "tools", "render", "inline_ref.json"), encoding="utf-8"))

fails = 0
for r in ref:
    got = decode_inline(r["input"], escape=True)
    exp = r["output"]
    if got == exp:
        continue
    fails += 1
    i = 0
    while i < min(len(got), len(exp)) and got[i] == exp[i]:
        i += 1
    print(f"FAIL  {r['input'][:56]!r}")
    print(f"  exp @{i}: ...{exp[max(0, i - 12):i + 40]!r}")
    print(f"  got @{i}: ...{got[max(0, i - 12):i + 40]!r}")

print(f"\n{len(ref) - fails}/{len(ref)} match" + ("  ✓ UNEXPECTED=0" if not fails else ""))
sys.exit(1 if fails else 0)

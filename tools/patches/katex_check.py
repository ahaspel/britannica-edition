"""Every formula the patched pages hand KaTeX (tex.json, as the
pipeline's walker gives them), rendered by KaTeX 0.16.0 — the version the
site loads — with throwOnError, in a headless browser (playwright, as
measure_math_widths does).  Writes katex_errors.json {tex: error}.
Usage: katex_check.py  (book root)"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
import re
sys.path.insert(0, str(Path(__file__).parent))
from paths import WORK
# as the site hands it to KaTeX: \mbox read as \text (render/article.py, viewer.html)
tex = sorted({re.sub(r"\\mbox\b", r"\\text", t) for ts in json.loads((WORK / "tex.json").read_text(encoding="utf-8")).values() for t in ts})
PAGE = """<!doctype html><html><head>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.0/dist/katex.min.js"></script></head><body></body></html>"""
errors = {}
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page()
    pg.set_content(PAGE)
    pg.wait_for_function("typeof katex !== 'undefined'")
    for k in range(0, len(tex), 500):
        chunk = tex[k:k + 500]
        res = pg.evaluate("""(xs) => xs.map(t => { try { katex.renderToString(t, {throwOnError: true});
                               return null } catch (e) { return String(e.message || e) } })""", chunk)
        for t, e in zip(chunk, res):
            if e:
                errors[t] = e
    b.close()
(WORK / "katex_errors.json").write_text(json.dumps(errors, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(tex), "formulas;", len(errors), "fail in KaTeX")
for t, e in list(errors.items())[:12]:
    print(" ", repr(t[:80]), "->", e[:100])

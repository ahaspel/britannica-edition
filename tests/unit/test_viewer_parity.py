"""Rules duplicated across the Python/JS boundary must be RUN against each other.

Inside Python a shared rule can have one owner and be imported.  Across the
runtime boundary it cannot, so the copy in ``viewer.html`` is the one kind of
duplicate this codebase cannot delete — only bind.  The slug is the one that
matters: Python bakes ``id="section-<slug>"`` into ``rendered_html`` and the
viewer computes the same slug for its TOC links, so a divergence is a dead
in-page link, silently.

The binding is EXECUTION, not textual comparison: the JS function is extracted
from viewer.html and run in node against the Python owner on the same inputs.
A test that merely compared the two regex literals would pass while `.trim()`
moved, or `.strip("-")` became `re.sub("^-|-$")` on one side only.

(`export.sections.section_key` claimed a viewer mirror too; there is no
`sectionKey` in the viewer, so there is nothing to bind — the claim was the
drift, and it is gone from that docstring.)
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from britannica.util.strings import section_slug

VIEWER = Path(__file__).resolve().parents[2] / "tools" / "viewer" / "viewer.html"
_FN_RE = re.compile(r"function sectionSlug\(name\)\s*\{.*?\n    \}", re.DOTALL)

# Real section titles and the shapes that break a slug: punctuation runs, leading
# and trailing junk, accents, en-dashes, digits, markup residue, emptiness.
CASES = [
    "History of Astronomy",
    "  Leading and trailing  ",
    "Ordinary of the Mass",
    "I. Aberration of Light",
    "Wars with the Mullah Mohammed Abdullah.",
    "§ 44 — the case of m ≡ 2 (mod 4)",
    "Café Life & Société",
    "1801–1900",
    "---already-hyphenated---",
    "!!!",
    "",
    "ALL CAPS TITLE",
    "Fig. 2.—CUP-BEARER, CNOSSUS",
]


def _js_source():
    m = _FN_RE.search(VIEWER.read_text(encoding="utf-8"))
    assert m, "sectionSlug not found in viewer.html — was it renamed?"
    return m.group(0)


def test_the_viewer_still_defines_the_rule():
    """A vacuous pass is the failure mode: if the function is gone, say so."""
    src = _js_source()
    assert "replace(" in src and "toLowerCase" in src


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_slug_agrees_across_the_runtime_boundary():
    script = (
        _js_source()
        + "\nconst out = JSON.parse(process.argv[1]).map(sectionSlug);"
        + "\nprocess.stdout.write(JSON.stringify(out));"
    )
    proc = subprocess.run(
        ["node", "-e", script, json.dumps(CASES)],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    js = json.loads(proc.stdout)
    py = [section_slug(c) for c in CASES]
    mismatched = [(c, p, j) for c, p, j in zip(CASES, py, js) if p != j]
    assert not mismatched, (
        "viewer.html's sectionSlug and britannica.util.strings.section_slug "
        "disagree: " + "; ".join(f"{c!r} → py {p!r} vs js {j!r}"
                                 for c, p, j in mismatched))

#!/usr/bin/env python3
"""Fingerprint the CURRENT export so a rebuild's change set is adjudicable.

    uv run python tools/diagnostics/export_fingerprint.py <out.tsv>
    uv run python tools/diagnostics/export_fingerprint.py --diff <old.tsv> <new.tsv>

A structural rebuild clears `data/derived/articles` and writes it fresh
([[feedback_snapshot_before_rebuild]]).  Copying ~36k JSONs is slow and huge;
what the after-diff actually needs is per-article identity, so this records a
hash of the two fields that matter — the marker `body` and the `rendered_html` —
plus their sizes.  Diffing two fingerprints then names every article whose output
moved, which is what makes a rebuild a TAGGED DIFF rather than a wholesale
rebaseline ([[feedback_no_wholesale_rebaseline]]).
"""
import glob
import hashlib
import html
import json
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
ART = "data/derived/articles"
SKIP = {"index.json", "contributors.json"}

# The TEXT-content signature.  Reduce rendered HTML to its visible word sequence —
# strip every tag whole (so attribute text, hrefs, styles all go), strip any
# residual «marker», decode entities, keep word/number tokens in order.  Two
# renders with the SAME words in the SAME order share a content_sha even if their
# markup differs completely; a render that GAINS or LOSES words does not.
#
# This is the one distinction the byte-hash nets can't draw, and the exact one the
# sweeper removals need: a styling relocation (bdo→span, dropping a wrapper the
# browser would drop anyway) is content-identical, while the failure each removal
# risks — the `{|`/`|}` swallow eating intervening prose, a dropped table cell — is
# a content change and shows up as words LOST.  Sequence, not a bag: a swallow
# removes a run of words in place, and comparing order catches a reordering too.
_TAG = re.compile(r"<[^>]+>")
_MARK = re.compile(r"«[^«»]*»")
_WORD = re.compile(r"[0-9A-Za-zÀ-ÖØ-öø-ÿ]+")


def content_tokens(rendered_html):
    txt = _MARK.sub(" ", _TAG.sub(" ", rendered_html or ""))
    return _WORD.findall(html.unescape(txt))


def _h(s):
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:16]


def _one(path):
    try:
        d = json.loads(open(path, encoding="utf-8").read())
    except Exception:
        return None
    body, rh = d.get("body") or "", d.get("rendered_html") or ""
    toks = content_tokens(rh)
    return (os.path.basename(path)[:-5], _h(body), _h(rh),
            _h("\x1f".join(toks)), str(len(toks)),
            str(len(rh)), str(d.get("title") or ""))


def capture(out):
    files = [f for f in glob.glob(f"{ART}/*.json")
             if os.path.basename(f) not in SKIP]
_COLS = ("body_sha", "render_sha", "content_sha", "content_len",
         "render_len", "title")


def capture(out):
    files = [f for f in glob.glob(f"{ART}/*.json")
             if os.path.basename(f) not in SKIP]
    with ProcessPoolExecutor() as ex, open(out, "w", encoding="utf-8") as fh:
        fh.write("stem\t" + "\t".join(_COLS) + "\n")
        n = 0
        for row in ex.map(_one, files, chunksize=200):
            if row:
                fh.write("\t".join(row) + "\n")
                n += 1
    print(f"fingerprinted {n} articles -> {out}")


def _read(p):
    rows = {}
    with open(p, encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            f = line.rstrip("\n").split("\t")
            rows[f[0]] = dict(zip(_COLS, f[1:]))
    return rows


def diff(old, new):
    a, b = _read(old), _read(new)
    gone = sorted(set(a) - set(b))
    added = sorted(set(b) - set(a))
    common = sorted(set(a) & set(b))
    moved = [k for k in common if a[k]["render_sha"] != b[k]["render_sha"]]
    # The signal that matters: TEXT content changed, not just markup.  A benign
    # styling relocation moves render_sha but not content_sha; a swallow / dropped
    # cell moves content_sha, with content_len shrinking.
    content = [k for k in common if a[k]["content_sha"] != b[k]["content_sha"]]
    lost = [k for k in content
            if int(b[k]["content_len"]) < int(a[k]["content_len"])]
    print(f"old={len(a)}  new={len(b)}")
    print(f"  disappeared      : {len(gone)}")
    print(f"  new              : {len(added)}")
    print(f"  render changed   : {len(moved)}")
    print(f"  CONTENT changed  : {len(content)}   "
          f"(of which words LOST: {len(lost)})")
    for k in gone[:20]:
        print(f"    GONE  {k}  {a[k]['title']}")
    for k in sorted(content,
                    key=lambda k: int(b[k]["content_len"]) - int(a[k]["content_len"]))[:30]:
        d = int(b[k]["content_len"]) - int(a[k]["content_len"])
        print(f"    CONTENT {k}  words {a[k]['content_len']}->{b[k]['content_len']} "
              f"({d:+})  {b[k]['title']}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--diff"]:
        diff(sys.argv[2], sys.argv[3])
    else:
        capture(sys.argv[1])

"""One-time migration: re-key the resolution disambiguation caches to the hashed stable_id scheme.

Two LLM-populated caches carry article identity in their keys/values, so the id-scheme change
(`{vol}-{page}-{section-slug}` → `{vol}-{page}-{sha1(slug)[:6]}`, the URL arc) staled both — their
cached picks all missed at the next resolve, dropping ~1,900 xrefs to unresolved and silently
mis-picking every ambiguous topic entry (ABEL/FANTI/…) back to the first candidate:

  * xref_disambiguation_cache.json — key `{SOURCE stable_id}::surface::target`; value `chosen` is a stable_id.
  * toc_disambiguation_cache.json  — key `{target}|{path}|{sorted candidate FILENAMES}`; value is a chosen filename.

This applies the SAME deterministic transform the CloudFront forwarder uses — hash the section-slug
tail — to every id/filename in both, preserving the LLM decisions with no re-disambiguation.  Run
once, then rebuild so both resolvers bake the recovered/correct links.  Idempotent: already-hashed
ids/filenames pass through untouched.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

XREF_CACHE = Path("data/derived/xref_disambiguation_cache.json")
TOC_CACHE = Path("data/derived/toc_disambiguation_cache.json")
_OLD_ID = re.compile(r"^(\d{2})-(\d{4})-(.+)$")
_HEX6 = re.compile(r"^\d{2}-\d{4}-[0-9a-f]{6}(-\d+)?$")
_FNAME = re.compile(r"^(\d{2}-\d{4}-[a-z0-9][a-z0-9-]*?)-([^a-z0-9-].*)$")  # {stable_id}-{TITLE}


def new_id(old: str) -> str:
    """`{vol}-{page}-{section-slug}` → `{vol}-{page}-{sha1(slug)[:6]}`; pass through if already
    hashed or unparseable."""
    if not old or _HEX6.match(old):
        return old
    m = _OLD_ID.match(old)
    if not m:
        return old
    vol, page, slug = m.groups()
    return f"{vol}-{page}-" + hashlib.sha1(slug.encode("utf-8")).hexdigest()[:6]


def new_filename(fn: str) -> str:
    """`{vol}-{page}-{slug}-{TITLE}.json` → `{vol}-{page}-{hash}.json` (pass through if hashed)."""
    base = fn[:-5] if fn.endswith(".json") else fn
    if _HEX6.match(base):
        return fn
    m = _FNAME.match(base)
    return (new_id(m.group(1)) + ".json") if m else fn


def _write(path: Path, new: dict) -> None:
    bak = path.with_suffix(".json.pre-hash-id.bak")
    if not bak.exists():
        shutil.copy2(path, bak)
    path.write_text(json.dumps(new, ensure_ascii=False), encoding="utf-8")
    print(f"re-keyed {len(new)} entries → {path.name}  (backup: {bak.name})")


def _rekey_xref() -> None:
    c = json.loads(XREF_CACHE.read_text(encoding="utf-8"))
    out = {}
    for k, v in c.items():
        src, _, rest = k.partition("::")
        nv = dict(v)
        if v.get("chosen"):
            nv["chosen"] = new_id(v["chosen"])
        out[f"{new_id(src)}::{rest}"] = nv
    _write(XREF_CACHE, out)


def _rekey_toc() -> None:
    c = json.loads(TOC_CACHE.read_text(encoding="utf-8"))
    out = {}
    for k, v in c.items():
        target, path, fns = k.split("|", 2)   # candidate filenames are the last field
        new_fns = ",".join(sorted(new_filename(f) for f in fns.split(",")))
        out[f"{target}|{path}|{new_fns}"] = new_filename(v) if v else v  # value is a chosen filename or null
    _write(TOC_CACHE, out)


if __name__ == "__main__":
    _rekey_xref()
    _rekey_toc()

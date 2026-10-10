"""Which corpus a derivative was built from, and is it still that corpus?

    uv run python tools/diagnostics/derivative_stamp.py record NAME FILE [FILE …]
    uv run python tools/diagnostics/derivative_stamp.py check NAME

The corpus is the product; the site and every download are derivatives of it,
each built and published on its own (`tools/derivatives.sh`, user 2026-10-09:
"The site is just the principal derivative").  Separating them opens one gap
the single deploy never had: a download built from one rebuild, published next
to a site from the next.  That is not hypothetical — the sampler once shipped
four days behind the corpus beside it on the download page, under a freshly
computed sha256 that made it look current.

`record` runs after a derivative builds: it refuses unless the corpus passes
`corpus_stamp.py --check`, then writes `derivatives/NAME.json` — the stamp's
corpus signature, when that rebuild finished, and each file's size and sha256.
`check` runs before a derivative publishes: it refuses unless the corpus still
passes, still carries the signature the derivative was built from, and every
recorded file is byte-identical.  So a published download demonstrably
describes the same book as the stamp — and the same book as a site deployed
from that stamp.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from wikikit.corpora import current_corpus

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / current_corpus().derived()
STAMP = DERIVED / "rebuild_stamp.json"
MANIFESTS = DERIVED / "derivatives"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _corpus_ok() -> bool:
    """The rebuild stamp's own check, run as the deploy runs it."""
    return subprocess.run([sys.executable, str(ROOT / "tools/diagnostics/corpus_stamp.py"), "--check"]).returncode == 0


def record(name: str, files: list[str]) -> int:
    if not _corpus_ok():
        print(f"  REFUSING to record {name}: the corpus does not pass its stamp.", file=sys.stderr)
        return 1
    stamp = json.loads(STAMP.read_text(encoding="utf-8"))
    entries = {}
    for f in files:
        p = (ROOT / f).resolve() if not Path(f).is_absolute() else Path(f)
        if not p.is_file():
            print(f"  REFUSING to record {name}: {f} was not built.", file=sys.stderr)
            return 1
        entries[p.relative_to(ROOT).as_posix()] = {"bytes": p.stat().st_size, "sha256": _sha256(p)}
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    (MANIFESTS / f"{name}.json").write_text(json.dumps({
        "derivative": name,
        "corpus_signature": stamp["signature"],
        "corpus_finished": stamp.get("finished"),
        "built": datetime.now().isoformat(timespec="seconds"),
        "files": entries,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"  {name}: {len(entries)} file(s) recorded against the rebuild of {stamp.get('finished')}")
    return 0


def check(name: str) -> int:
    path = MANIFESTS / f"{name}.json"
    if not path.is_file():
        print(f"  REFUSING to publish {name}: it has not been built (no {path.relative_to(ROOT).as_posix()}).",
              file=sys.stderr)
        return 1
    if not _corpus_ok():
        print(f"  REFUSING to publish {name}: the corpus does not pass its stamp.", file=sys.stderr)
        return 1
    m = json.loads(path.read_text(encoding="utf-8"))
    stamp = json.loads(STAMP.read_text(encoding="utf-8"))
    if m["corpus_signature"] != stamp["signature"]:
        print(f"  REFUSING to publish {name}: built from the rebuild of {m.get('corpus_finished')}, "
              f"but the corpus is now the rebuild of {stamp.get('finished')}.  Build it again.", file=sys.stderr)
        return 1
    for rel, want in m["files"].items():
        p = ROOT / rel
        if not p.is_file() or p.stat().st_size != want["bytes"] or _sha256(p) != want["sha256"]:
            print(f"  REFUSING to publish {name}: {rel} has changed or gone since it was built.", file=sys.stderr)
            return 1
    print(f"  {name}: built from the rebuild of {stamp.get('finished')}, {len(m['files'])} file(s) intact")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("name")
    r.add_argument("files", nargs="+")
    c = sub.add_parser("check")
    c.add_argument("name")
    a = ap.parse_args()
    return record(a.name, a.files) if a.cmd == "record" else check(a.name)


if __name__ == "__main__":
    sys.exit(main())

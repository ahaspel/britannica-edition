"""Which published artifacts are behind the current corpus or code?

    uv run python tools/diagnostics/artifact_sync.py

THE QUESTION A CHECKSUM CANNOT ANSWER.  A `.sha256` beside an artifact says
"these are its bytes".  It cannot say whether those bytes came from the corpus
and the code we have now — and that is the failure this project keeps having:

  * 2026-08-19  the vol-1 sampler shipped four days behind the corpus it sat
    beside on the download page, "under a freshly computed sha256 that made it
    look current" (tools/deploy.sh).  Fixed by building the sampler inside the
    deploy.
  * 2026-09-18  the same sampler shipped a build behind again — this time on an
    UNCHANGED corpus, differing only in code, because the topic fix landed after
    the deploy built it.  `corpus_stamp.py` passes that case: the corpus really
    was current.  Only the code half catches it.

So each artifact records both halves (britannica.provenance), and this reports
which ones no longer match the working tree.  It does NOT rebuild anything: the
point is to make drift visible in seconds, because a check that is expensive to
run stops being run.

Exit status is 0 even when artifacts are stale — staleness is a fact to report,
not a build failure.  Use `--gate` to make it non-zero for scripting.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from britannica import provenance as prov                      # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

# Artifact -> where its recorded provenance lives.  The site is absent on
# purpose: deploy.sh gates it with corpus_stamp.py, which is the same signature.
ARTIFACTS = [
    ("full EPUB",       ROOT / "epub/eb1911.epub",        "sidecar"),
    ("vol-1 sampler",   ROOT / "epub/eb1911-vol01.epub",  "sidecar"),
    ("MDX standard",    ROOT / "mdx/standard",            "manifest"),
    ("MDX complete",    ROOT / "mdx/complete",            "manifest"),
    ("MDX enhanced",    ROOT / "mdx/complete-enhanced",   "manifest"),
]


def recorded(path: Path, kind: str) -> dict | None:
    try:
        if kind == "sidecar":
            p = path.with_suffix(path.suffix + ".provenance.json")
            if not p.is_file():
                return None
            return json.loads(p.read_text(encoding="utf-8"))
        m = path / "manifest.json"
        if not m.is_file():
            return None
        d = json.loads(m.read_text(encoding="utf-8"))
        if "provenance" in d:
            return d["provenance"]
        # Older MDX manifests carry the per-file map but no rollup; derive it so
        # an artifact built before this tool still answers the question.
        code = d.get("export_code_sha256")
        return {"code_rollup": prov._rollup(code), "code_file_count": len(code),
                "rebuild_stamp": {}} if code else {}
    except Exception as exc:                       # a malformed record is a finding
        return {"_error": str(exc)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true",
                    help="exit non-zero if any artifact is behind")
    args = ap.parse_args()

    now = prov.fingerprint()
    print(f"current code   : {now['code_rollup'][:16]}…  ({now['code_file_count']} files)")
    stamp = now.get("rebuild_stamp") or {}
    print(f"current corpus : {(stamp.get('signature') or '?')[:16]}…  "
          f"({stamp.get('articles', '?')} articles, rebuilt {stamp.get('finished', '?')})\n")

    rows, behind = [], 0
    for name, path, kind in ARTIFACTS:
        if not (path.exists()):
            rows.append((name, "absent", ""))
            continue
        rec = recorded(path, kind)
        if rec is None:
            rows.append((name, "NO RECORD", "built before provenance existed"))
            behind += 1
            continue
        if "_error" in rec:
            rows.append((name, "UNREADABLE", rec["_error"][:40]))
            behind += 1
            continue
        code_ok = rec.get("code_rollup") == now["code_rollup"]
        rec_sig = (rec.get("rebuild_stamp") or {}).get("signature")
        corpus_ok = (rec_sig == stamp.get("signature")) if rec_sig else None
        why = []
        if not code_ok:
            why.append("code")
        if corpus_ok is False:
            why.append("corpus")
        if corpus_ok is None:
            why.append("(corpus unrecorded)")
        state = "current" if code_ok and corpus_ok is not False else "BEHIND"
        if state == "BEHIND":
            behind += 1
        rows.append((name, state, " ".join(why)))

    w = max(len(r[0]) for r in rows)
    for name, state, why in rows:
        print(f"  {name:<{w}}  {state:<10} {why}")
    print(f"\n{behind} artifact(s) not built from the current corpus and code")
    return 1 if (args.gate and behind) else 0


if __name__ == "__main__":
    sys.exit(main())

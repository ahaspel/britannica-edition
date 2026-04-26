"""Download the deployed S3 version of each fixture article into a
local baseline directory, so we can render + scan what's live in
production. Pair with ``scan_article.py --baseline-dir`` to get a
true before-state for diff.

Usage:
    uv run python tools/qa/fetch_s3_baseline.py \\
        --from-file tools/qa/fixtures/default.txt \\
        --out-dir data/qa_baseline/articles

Downloads via the public britannica11.org URL; no AWS credentials
needed. Refreshes every file on every run so the baseline always
matches what's currently live; pass ``--keep-existing`` to skip
files that already exist locally.
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

S3_BASE = "https://britannica11.org/data/articles"


def _fetch(filename: str, out: Path, refresh: bool) -> bool:
    if out.exists() and not refresh:
        return False
    url = f"{S3_BASE}/{filename}"
    req = urllib.request.Request(
        url, headers={"User-Agent": "britannica11-qa/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-file", type=Path, required=True,
                    help="Fixture file with one article name per line.")
    ap.add_argument("--out-dir", type=Path,
                    default=Path("data/qa_baseline/articles"),
                    help="Where to save the S3 versions (default: "
                         "data/qa_baseline/articles).")
    ap.add_argument("--keep-existing", action="store_true",
                    help="Skip files that already exist locally instead "
                         "of re-downloading them. Default is to refresh "
                         "every file so the baseline matches live S3.")
    args = ap.parse_args()
    refresh = not args.keep_existing

    names: list[str] = []
    for line in args.from_file.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if not s.endswith(".json"):
            s += ".json"
        names.append(s)

    downloaded = 0
    skipped = 0
    failed = 0
    for n in names:
        out = args.out_dir / n
        try:
            if _fetch(n, out, refresh):
                downloaded += 1
                print(f"  fetched {n}")
            else:
                skipped += 1
        except Exception as e:
            failed += 1
            print(f"  FAILED {n}: {e}", file=sys.stderr)

    print()
    print(f"Downloaded: {downloaded}  skipped: {skipped}  failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

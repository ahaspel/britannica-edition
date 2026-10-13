#!/usr/bin/env bash
# The patch chain, from the judged readings to data/patches.json.
# No model calls: disputes, the judge and the rulings (judge.py, rulings.py)
# are already in data/readings/judge.  Run from the book root.
#
#   build.sh            build, filter, validate, KaTeX; install --dry
#   build.sh --install  ... and install (writes data/patches.json and steps
#                       the judged pages' supplied files aside)
#
# Heavy: the filter tests every patch alone (~25 min).  Never during a rebuild
# that reads data/patches.json — install only between rebuilds.
set -euo pipefail
cd "$(dirname "$0")/../.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
P=tools/patches

nice uv run python $P/build_words.py --loose      # -> words.json
nice uv run python $P/build_formulas.py           # -> formulas.json
uv run python $P/merge.py                         # -> merged.json
nice uv run python $P/filter_patches.py           # -> kept.json
nice uv run python $P/validate_patches.py         # -> validate.json, tex.json
uv run python $P/katex_check.py                   # -> katex_errors.json
if [ "${1:-}" = "--install" ]; then
  uv run python $P/install.py
else
  uv run python $P/install.py --dry
fi

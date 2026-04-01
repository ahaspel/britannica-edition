#!/bin/bash
# Fetch all 29 volumes from Wikisource.
# Designed for unattended overnight runs.
# Fetches 350 pages, cooldown 15 min, repeat — across volume boundaries.

set -uo pipefail

PAGE_COUNTS=(0 1029 1027 1015 1031 1002 1017 1008 1027 997 967 968 985 985 953 994 1016 1039 1000 1034 1054 1019 993 1069 1100 1090 1104 1092 1091 982)

BATCH_LIMIT=350
COOLDOWN=900  # 15 minutes
BUDGET=$BATCH_LIMIT

for VOL in $(seq 1 29); do
  END=${PAGE_COUNTS[$VOL]}
  PADDED=$(printf "%02d" "$VOL")
  OUTDIR="data/raw/wikisource/vol_${PADDED}"
  mkdir -p "$OUTDIR"

  while true; do
    EXISTING=$(ls "$OUTDIR"/*.json 2>/dev/null | wc -l)
    [ "$EXISTING" -ge "$END" ] && break

    # Cooldown when budget is exhausted
    if [ "$BUDGET" -le 0 ]; then
      echo "  Cooldown (15 min)..."
      sleep "$COOLDOWN"
      BUDGET=$BATCH_LIMIT
    fi

    BEFORE=$EXISTING
    uv run python tools/fetch/fetch_wikisource_pages.py \
      --volume "$VOL" \
      --start 1 \
      --end "$END" \
      --outdir "$OUTDIR" \
      --limit "$BUDGET" || true

    AFTER=$(ls "$OUTDIR"/*.json 2>/dev/null | wc -l)
    FETCHED=$((AFTER - BEFORE))
    BUDGET=$((BUDGET - FETCHED))

    # No progress — likely rate-limited; exhaust budget to trigger cooldown
    if [ "$FETCHED" -eq 0 ]; then
      echo "  No progress on volume $VOL — forcing cooldown..."
      BUDGET=0
    fi
  done
done

echo "All volumes fetched."

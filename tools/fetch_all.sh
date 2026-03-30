#!/bin/bash
# Fetch all 29 volumes from Wikisource.
# Designed for unattended overnight runs.
# Skips already-fetched pages, so safe to re-run.

set -uo pipefail

PAGE_COUNTS=(0 1029 1027 1015 1031 1002 1017 1008 1027 997 967 968 985 985 953 994 1016 1039 1000 1034 1054 1019 993 1069 1100 1090 1104 1092 1091 982)

for VOL in $(seq 1 29); do
  END=${PAGE_COUNTS[$VOL]}
  PADDED=$(printf "%02d" "$VOL")
  OUTDIR="data/raw/wikisource/vol_${PADDED}"

  mkdir -p "$OUTDIR"

  EXISTING=$(ls "$OUTDIR"/*.json 2>/dev/null | wc -l)

  if [ "$EXISTING" -ge "$END" ]; then
    echo "Volume $VOL: already complete ($EXISTING/$END pages)"
    continue
  fi

  echo "Volume $VOL: fetching pages 1-$END ($EXISTING already cached)"

  uv run python tools/fetch/fetch_wikisource_pages.py \
    --volume "$VOL" \
    --start 1 \
    --end "$END" \
    --outdir "$OUTDIR"

  echo "Volume $VOL: fetch complete"
  echo
done

echo "All volumes fetched."

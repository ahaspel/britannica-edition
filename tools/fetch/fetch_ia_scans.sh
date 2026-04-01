#!/bin/bash
# Download page scans from Internet Archive for all 29 volumes.
# Downloads JP2 zip files (~1.2GB each). Safe to re-run — skips existing.
# Polite: 30s delay between volumes, retries on failure.

set -uo pipefail

OUTDIR="data/raw/ia_scans"
DELAY=120  # 2 minutes between volume downloads
RETRY_DELAY=1800  # 30 minutes on 503/failure

mkdir -p "$OUTDIR"

for VOL in $(seq 1 29); do
  PADDED=$(printf "%02d" "$VOL")
  IDENTIFIER="encyclopaediabri${PADDED}chisrich"
  FILENAME="${IDENTIFIER}_jp2.zip"
  URL="https://archive.org/download/${IDENTIFIER}/${FILENAME}"
  OUTFILE="${OUTDIR}/${FILENAME}"

  if [ -f "$OUTFILE" ]; then
    echo "Volume $VOL: already downloaded ($OUTFILE)"
    continue
  fi

  echo "Volume $VOL: downloading $FILENAME..."
  ATTEMPT=0
  while true; do
    ATTEMPT=$((ATTEMPT + 1))
    if curl -L -f -o "${OUTFILE}.part" \
         -H "User-Agent: britannica-edition/0.1 (scholarly edition project)" \
         --retry 3 --retry-delay 60 \
         --connect-timeout 30 \
         "$URL"; then
      mv "${OUTFILE}.part" "$OUTFILE"
      echo "Volume $VOL: done ($(du -h "$OUTFILE" | cut -f1))"
      break
    else
      rm -f "${OUTFILE}.part"
      if [ "$ATTEMPT" -ge 5 ]; then
        echo "Volume $VOL: failed after $ATTEMPT attempts, skipping."
        break
      fi
      echo "Volume $VOL: attempt $ATTEMPT failed, waiting ${RETRY_DELAY}s..."
      sleep "$RETRY_DELAY"
    fi
  done

  sleep "$DELAY"
done

echo "All downloads complete."
echo "Total size: $(du -sh "$OUTDIR" | cut -f1)"

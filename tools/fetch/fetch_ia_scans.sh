#!/bin/bash
# Download page scans from Internet Archive for all 29 volumes.
# Downloads JP2 zip files (~1.2GB each). Safe to re-run — skips existing.
# Polite: 30s delay between volumes, retries on failure.

set -uo pipefail

OUTDIR="data/raw/ia_scans"
DELAY=3600  # 1 hour between volume downloads
RETRY_DELAY=3600  # 1 hour on 503/failure

mkdir -p "$OUTDIR"

# IA identifiers vary per volume — some use "brit", vol 20 uses a different suffix
ia_identifier() {
  local vol=$1
  case $vol in
    3|5|6|7|8|9|11|12|13) echo "encyclopaediabrit$(printf '%02d' $vol)chisrich" ;;
    20) echo "encyclopaediabri20univ" ;;
    *) echo "encyclopaediabri$(printf '%02d' $vol)chisrich" ;;
  esac
}

for VOL in $(seq 1 29); do
  PADDED=$(printf "%02d" "$VOL")
  IDENTIFIER=$(ia_identifier "$VOL")
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

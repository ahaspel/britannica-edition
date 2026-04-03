#!/usr/bin/env bash
# Quick rebuild of a single article by title or page range.
#
# Usage:
#   tools/rebuild_article.sh <volume> <title>
#   tools/rebuild_article.sh <volume> <start_page> <end_page>
#
# Examples:
#   tools/rebuild_article.sh 2 AUSTRALIA
#   tools/rebuild_article.sh 9 33 147
#
# What it does:
#   1. Looks up the article's page range (if given by title)
#   2. Re-converts raw wikitext -> cleaned_preview for those pages
#   3. Re-imports those pages into the DB (overwrite)
#   4. Re-cleans those pages
#   5. Re-builds article body from segments
#   6. Re-exports just that article's JSON
#   7. Optionally uploads to S3 with --deploy flag

set -euo pipefail
cd "$(dirname "$0")/.."

DEPLOY=false
for arg in "$@"; do
    if [[ "$arg" == "--deploy" ]]; then
        DEPLOY=true
    fi
done

# Strip --deploy from args
ARGS=()
for arg in "$@"; do
    [[ "$arg" != "--deploy" ]] && ARGS+=("$arg")
done
set -- "${ARGS[@]}"

if [[ $# -lt 2 ]]; then
    echo "Usage: tools/rebuild_article.sh <volume> <title> [--deploy]"
    echo "       tools/rebuild_article.sh <volume> <start_page> <end_page> [--deploy]"
    exit 1
fi

VOL=$1
shift

uv run python tools/rebuild_article.py "$VOL" "$@"

if $DEPLOY; then
    OUTFILE=$(uv run python tools/rebuild_article.py "$VOL" "$@" --output-filename-only)
    if [[ -n "$OUTFILE" && -f "data/derived/articles/$OUTFILE" ]]; then
        echo ""
        echo "Deploying $OUTFILE to S3..."
        aws s3 cp "data/derived/articles/$OUTFILE" "s3://britannica11.org/data/$OUTFILE"
        aws cloudfront create-invalidation --distribution-id E24BJKH0IB4I6 --paths "/*" > /dev/null
        echo "Deployed and invalidated."
    else
        echo "Could not determine output file for deploy."
    fi
fi

#!/usr/bin/env bash
# Upload one or more HTML files to the britannica11.org S3 bucket and invalidate
# them on CloudFront. Works around Git Bash path-mangling by using a batch JSON
# for the invalidation.
#
# Usage:
#   tools/deploy_html.sh tools/viewer/about.html
#   tools/deploy_html.sh tools/viewer/about.html tools/viewer/ancillary.html
#
# Each file is uploaded to the bucket root at its basename (e.g. about.html).

set -euo pipefail

BUCKET="britannica11.org"
DIST_ID="E24BJKH0IB4I6"

if [[ $# -eq 0 ]]; then
  echo "usage: $0 <file.html> [file2.html ...]" >&2
  exit 1
fi

paths_json=""
for f in "$@"; do
  if [[ ! -f "$f" ]]; then
    echo "not a file: $f" >&2
    exit 1
  fi
  base="$(basename "$f")"
  aws s3 cp "$f" "s3://${BUCKET}/${base}" \
    --content-type "text/html; charset=utf-8" \
    --cache-control "public, max-age=300"
  if [[ -z "$paths_json" ]]; then
    paths_json="\"/${base}\""
  else
    paths_json="${paths_json},\"/${base}\""
  fi
done

count=$#
caller_ref="deploy-html-$(date +%s)-$$"
# Write the batch JSON next to this script — /tmp confuses the native Windows
# aws.exe, and mktemp in Git Bash lives there by default.
batch_file=".cf-invalidation.$$.json"
cat > "$batch_file" <<EOF
{
  "Paths": { "Quantity": ${count}, "Items": [${paths_json}] },
  "CallerReference": "${caller_ref}"
}
EOF

inv_id=$(aws cloudfront create-invalidation \
  --distribution-id "$DIST_ID" \
  --invalidation-batch "file://${batch_file}" \
  --query 'Invalidation.Id' --output text)
rm -f "$batch_file"

echo "invalidation: $inv_id  (paths: ${paths_json//\"/})"

#!/bin/bash
# Validate an EPUB with EPUBCheck — the external conformance check the build's
# own gates (id census, href resolution) deliberately do NOT replace: ours prove
# the book is internally consistent, this proves it is a legal EPUB.
#
# The jar is 32 MB of third-party code, so it is installed rather than committed
# (see .gitignore).  This script is the committed half: it records WHERE the jar
# lives and where to get it.  Both halves matter — the validator once existed
# only inside a session scratchpad, with no reference to it anywhere in the repo,
# and was effectively unfindable a week later.
#
# Usage: ./tools/check_epub.sh epub/eb1911.epub [epub/eb1911-vol01.epub …]
#        ./tools/check_epub.sh            # both shipped books
set -e

JAR="$(dirname "$0")/epubcheck/epubcheck.jar"
VERSION="5.1.0"
URL="https://github.com/w3c/epubcheck/releases/download/v${VERSION}/epubcheck-${VERSION}.zip"

if [ ! -f "$JAR" ]; then
  echo "EPUBCheck not installed at $JAR" >&2
  echo "  curl -L -o epubcheck.zip $URL" >&2
  echo "  unzip epubcheck.zip && mv epubcheck-${VERSION} $(dirname "$0")/epubcheck" >&2
  exit 1
fi

# 6 GB: the full book is 579 MB and 37,226 documents.  The default heap dies on it.
HEAP="${EPUBCHECK_HEAP:-6g}"

FILES=("$@")
if [ ${#FILES[@]} -eq 0 ]; then
  FILES=(epub/eb1911.epub epub/eb1911-vol01.epub)
fi

status=0
for f in "${FILES[@]}"; do
  if [ ! -f "$f" ]; then
    echo "  $f — NOT BUILT, skipped" >&2
    status=1
    continue
  fi
  echo "=== $f ($(du -h "$f" | cut -f1)) ==="
  java -Xmx"$HEAP" -jar "$JAR" "$f" || status=1
done
exit $status

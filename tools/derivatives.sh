#!/bin/bash
# Build, or publish, the book's DERIVATIVES from a finished rebuild.
#
# The corpus is the product.  The site (tools/deploy.sh) is its principal
# derivative; everything else is here (user, 2026-10-09: "The site is just the
# principal derivative").  A rebuild produces the corpus and nothing else; a
# deploy ships the site and nothing else; each derivative below is built and
# published on its own, and re-runnable alone, because derivatives fail for
# their own reasons (math SVGs, an epubcheck finding, an expired HF token) and a
# retry must not re-run the rest.
#
#   ./tools/derivatives.sh build   [NAME …]    # default: every derivative
#   ./tools/derivatives.sh publish [NAME …]
#
#   corpus   articles.jsonl + graphs bundle and download/ (the HF dataset card) ~23 min
#   maps     colour plates + Stieler originals bundle
#   tei      the TEI-P5 edition: every article validated against TEI P5, then bundled
#   sampler  the one-volume sampler EPUB
#   epub     the complete EPUB, then EPUBCheck              (publish: by hand, Payhip)
#   mdx      standard + enhanced MDX editions, then release (publish: by hand)
#   hf       the HuggingFace dataset mirror of download/    (publish only; needs corpus)
#
# THE STAMP.  `build` refuses a corpus that fails its rebuild stamp, and records
# which rebuild each derivative came from (tools/diagnostics/derivative_stamp.py).
# `publish` refuses a derivative built from any other rebuild, or whose files have
# changed since — so the site and every download demonstrably describe the same
# book.  That check is what used to require building the sampler at deploy time.
set -euo pipefail
export PYTHONIOENCODING=utf-8

ALL="corpus maps tei sampler epub mdx hf"
MODE="${1:-}"
case "$MODE" in build|publish) shift ;; *)
  echo "Usage: $0 build|publish [$ALL]" >&2; exit 2 ;;
esac
NAMES="${*:-$ALL}"
for n in $NAMES; do
  case " $ALL " in *" $n "*) ;; *) echo "Unknown derivative: $n (known: $ALL)" >&2; exit 2 ;; esac
done

# The book's roots and names, asked of the book — never spelled here.
DERIVED=$(uv run python -m wikikit.corpora derived)
SLUG=$(uv run python -m wikikit.corpora brand slug)
CORPUS_TGZ=$(uv run python -m wikikit.export.download name corpus)
MAPS_TGZ=$(uv run python -m wikikit.export.download name maps)
TEI_TGZ=$(uv run python -m wikikit.export.download name tei)
SAMPLER_VOL=$(uv run python -m wikikit.corpora brand sampler_volume)
: "${DERIVED:?no output root}" "${SLUG:?no slug}" "${CORPUS_TGZ:?}" "${MAPS_TGZ:?}" "${TEI_TGZ:?}"
: "${SAMPLER_VOL:?the book names no sampler volume}"
SAMPLER="epub/${SLUG}-vol$(printf '%02d' "$SAMPLER_VOL").epub"
COMPLETE="epub/${SLUG}.epub"
S3="s3://britannica11.org/download"
STAMP="uv run python tools/diagnostics/derivative_stamp.py"
START=$(date +%s)
elapsed() { local s=$(( $(date +%s) - START )); printf "%d:%02d" $((s/60)) $((s%60)); }

build() {
  local n=$1
  echo
  echo "=== build $n [$(elapsed)] ==="
  uv run python tools/diagnostics/corpus_stamp.py --check
  case $n in
    corpus)
      uv run python -m wikikit.export.download
      $STAMP record corpus "$DERIVED/$CORPUS_TGZ" "$DERIVED/$CORPUS_TGZ.sha256" "$DERIVED"/download/* ;;
    maps)
      uv run python -m wikikit.export.download maps
      $STAMP record maps "$DERIVED/$MAPS_TGZ" "$DERIVED/$MAPS_TGZ.sha256" ;;
    tei)
      # Validity first, against the TEI Consortium's OWN schema (tei_all.rng,
      # vendored so a build never depends on tei-c.org): an invalid article stops
      # the bundle.  An independent net — a leak scan finds markers we failed to
      # convert, validation finds structure converted WRONGLY (a <cell> outside a
      # <row>, a <p> inside an inline, a duplicate @xml:id); it found nine defect
      # classes the day it first ran.  lxml on demand, as the HF publish does. ~90s.
      uv run --with lxml python -m wikikit.diagnostics.tei_validate
      uv run python -m wikikit.export.download tei
      $STAMP record tei "$DERIVED/$TEI_TGZ" "$DERIVED/$TEI_TGZ.sha256" ;;
    sampler)
      mkdir -p epub   # gitignored, so absent on a fresh clone
      # The build's own hard gates (every article anchored once, no duplicate
      # ids, every href resolves, per-chunk text preservation) stop it here.
      uv run python -m wikikit.epub.build --volume "$SAMPLER_VOL" --out "$SAMPLER"
      ./tools/check_epub.sh "$SAMPLER"
      sha256sum "$SAMPLER" | awk '{print $1}' > "$SAMPLER.sha256"
      $STAMP record sampler "$SAMPLER" "$SAMPLER.sha256" ;;
    epub)
      mkdir -p epub
      uv run python -m wikikit.epub.build --all --out "$COMPLETE"
      ./tools/check_epub.sh "$COMPLETE"
      $STAMP record epub "$COMPLETE" ;;
    mdx)
      uv run python -m wikikit.mdx.build --all --output mdx/complete
      uv run python -m wikikit.mdx.build --all --native-search --output mdx/complete-enhanced
      uv run python -m wikikit.mdx.release
      $STAMP record mdx mdx/releases/* ;;
    hf)
      echo "  (nothing to build: hf publishes the corpus derivative's download/)" ;;
  esac
}

publish() {
  local n=$1
  echo
  echo "=== publish $n [$(elapsed)] ==="
  case $n in
    corpus)
      $STAMP check corpus
      aws s3 cp "$DERIVED/$CORPUS_TGZ" "$S3/$CORPUS_TGZ"
      aws s3 cp "$DERIVED/$CORPUS_TGZ.sha256" "$S3/$CORPUS_TGZ.sha256"
      aws s3 cp "$DERIVED/download/manifest.json" "$S3/manifest.json"
      aws s3 cp "$DERIVED/download/README.md" "$S3/README.md" ;;
    maps)
      $STAMP check maps
      aws s3 cp "$DERIVED/$MAPS_TGZ" "$S3/$MAPS_TGZ"
      aws s3 cp "$DERIVED/$MAPS_TGZ.sha256" "$S3/$MAPS_TGZ.sha256" ;;
    tei)
      $STAMP check tei
      aws s3 cp "$DERIVED/$TEI_TGZ" "$S3/$TEI_TGZ"
      aws s3 cp "$DERIVED/$TEI_TGZ.sha256" "$S3/$TEI_TGZ.sha256" ;;
    sampler)
      $STAMP check sampler
      aws s3 cp "$SAMPLER" "$S3/$(basename "$SAMPLER")"
      aws s3 cp "$SAMPLER.sha256" "$S3/$(basename "$SAMPLER").sha256" ;;
    epub)
      $STAMP check epub
      # The Payhip complete edition is FOUR files: this EPUB and the mdx step's
      # two archives + README.  Uploaded by hand.
      echo "  Payhip, by hand: $COMPLETE" ;;
    mdx)
      $STAMP check mdx
      echo "  Payhip, by hand: mdx/releases/Britannica11-MDX.zip, mdx/releases/Britannica11-Enhanced-Windows.zip, mdx/releases/README.md" ;;
    hf)
      # The dataset card and files ARE the corpus derivative's download/.
      $STAMP check corpus
      uv run --with huggingface_hub python tools/publish_hf.py britannica11/eb1911 || {
        echo "  HuggingFace publish failed.  Auth once with a WRITE token, then rerun just this:" >&2
        echo "    uv run --with huggingface_hub hf auth login   # --force to replace a read-only token" >&2
        echo "    ./tools/derivatives.sh publish hf" >&2
        exit 1
      } ;;
  esac
}

echo "============================================"
echo "  Derivatives: $MODE $NAMES"
echo "  Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
for n in $NAMES; do
  "$MODE" "$n"
done
if [ "$MODE" = publish ] && [[ " $NAMES " =~ \ (corpus|maps|tei|sampler)\  ]]; then
  echo
  echo "  Invalidating CloudFront /download/* ..."
  aws cloudfront create-invalidation --distribution-id E24BJKH0IB4I6 --paths "/download/*" > /dev/null
fi
echo
echo "============================================"
echo "  Derivatives $MODE finished: $NAMES  [$(elapsed)]"
echo "============================================"

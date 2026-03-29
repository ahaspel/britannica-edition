#!/bin/bash

VOLUME=$1

./tools/db/wipe_volume.sh $VOLUME

uv run python tools/fetch/import_wikisource_pages.py \
  --indir data/raw/wikisource \
  --volume $VOLUME

uv run britannica clean-pages $VOLUME
uv run britannica detect-boundaries $VOLUME
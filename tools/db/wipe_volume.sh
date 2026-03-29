#!/bin/bash

VOLUME=$1

if [ -z "$VOLUME" ]; then
  echo "Usage: ./wipe_volume.sh <volume>"
  exit 1
fi

echo "Wiping volume $VOLUME..."

docker exec -i britannica-edition-postgres-1 psql -U postgres -d britannica <<EOF
DELETE FROM cross_references
WHERE article_id IN (
  SELECT id FROM articles WHERE volume = $VOLUME
)
OR target_article_id IN (
  SELECT id FROM articles WHERE volume = $VOLUME
);

DELETE FROM article_segments
WHERE article_id IN (
  SELECT id FROM articles WHERE volume = $VOLUME
)
OR source_page_id IN (
  SELECT id FROM source_pages WHERE volume = $VOLUME
);

DELETE FROM articles
WHERE volume = $VOLUME;

DELETE FROM source_pages
WHERE volume = $VOLUME;
EOF

echo "Done."
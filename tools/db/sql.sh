#!/bin/bash

docker exec -it britannica-edition-postgres-1 \
  psql -U postgres -d britannica -c "$1"
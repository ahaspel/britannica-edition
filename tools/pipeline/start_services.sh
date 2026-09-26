#!/bin/bash
# Start all services needed to run the Britannica edition locally.
#
# Usage: ./tools/start_services.sh
#
# Services:
#   1. PostgreSQL (Docker) — article database
#   2. Meilisearch (Docker) — full-text search
#   3. The site server — tools/serve.py on http://localhost:8000, owned by the
#      scheduled task `britannica-webserver` (runs at logon, no console)
#
# To stop: ./tools/start_services.sh stop
#
# THE WEB SERVER HAS ONE OWNER: the task.  This script used to launch its own
# `python -m http.server 8000` whenever `.webserver.pid` did not name a live
# process — a second way to start a server, next to the task, with no check of
# what was already on :8000.  Windows lets two processes bind 0.0.0.0:8000, so
# which one answered was undefined: on 2026-09-26 two copies of serve.py were
# found listening, one 17 days old.  Now: if :8000 answers, leave it alone; if
# not, ask the task to start it.
WEB_TASK="britannica-webserver"

set -euo pipefail

if [ "${1:-}" = "stop" ]; then
  echo "Stopping services..."
  docker compose down
  schtasks //end //tn "$WEB_TASK" > /dev/null 2>&1 || true
  echo "All services stopped."
  exit 0
fi

echo "============================================"
echo "  Starting Britannica edition services"
echo "============================================"
echo

# --- Docker services ---
echo "=== Starting PostgreSQL and Meilisearch ==="
docker compose up -d
echo "  Waiting for PostgreSQL to accept connections..."
for i in $(seq 1 30); do
  if docker exec britannica-edition-postgres-1 pg_isready -U postgres > /dev/null 2>&1; then
    echo "  PostgreSQL ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "  ERROR: PostgreSQL did not become ready in time."
    exit 1
  fi
  sleep 1
done

echo "  Waiting for Meilisearch to respond..."
for i in $(seq 1 30); do
  if curl -s http://localhost:7700/health > /dev/null 2>&1; then
    echo "  Meilisearch ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "  ERROR: Meilisearch did not become ready in time."
    exit 1
  fi
  sleep 1
done

# --- Web server ---
echo
echo "=== Starting web server on http://localhost:8000 ==="
if curl -s -o /dev/null --max-time 3 http://localhost:8000/; then
  echo "  Web server already answering on :8000 — left alone."
else
  schtasks //run //tn "$WEB_TASK" > /dev/null
  for i in $(seq 1 15); do
    curl -s -o /dev/null --max-time 2 http://localhost:8000/ && break
    if [ "$i" -eq 15 ]; then
      echo "  ERROR: task $WEB_TASK did not bring up :8000."
      exit 1
    fi
    sleep 1
  done
  echo "  Started by task $WEB_TASK."
fi

echo
echo "============================================"
echo "  All services running."
echo
echo "  Viewer:  http://localhost:8000/tools/viewer/index.html"
echo "  Search:  http://localhost:8000/tools/viewer/search.html"
echo "============================================"

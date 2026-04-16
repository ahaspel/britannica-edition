#!/bin/bash
# Start all services needed to run the Britannica edition locally.
#
# Usage: ./tools/start_services.sh
#
# Services:
#   1. PostgreSQL (Docker) — article database
#   2. Meilisearch (Docker) — full-text search
#   3. Python HTTP server — viewer on http://localhost:8000
#
# To stop: ./tools/start_services.sh stop

set -euo pipefail

if [ "${1:-}" = "stop" ]; then
  echo "Stopping services..."
  docker compose down
  # Kill the web server if running
  if [ -f .webserver.pid ]; then
    kill "$(cat .webserver.pid)" 2>/dev/null || true
    rm -f .webserver.pid
  fi
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
if [ -f .webserver.pid ] && kill -0 "$(cat .webserver.pid)" 2>/dev/null; then
  echo "  Web server already running (PID $(cat .webserver.pid))."
else
  python -m http.server 8000 > /dev/null 2>&1 &
  echo $! > .webserver.pid
  echo "  Started (PID $!)."
fi

echo
echo "============================================"
echo "  All services running."
echo
echo "  Viewer:  http://localhost:8000/tools/viewer/index.html"
echo "  Search:  http://localhost:8000/tools/viewer/search.html"
echo "============================================"

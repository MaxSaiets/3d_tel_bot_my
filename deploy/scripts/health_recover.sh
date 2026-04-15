#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/telegram-shop}"
cd "$APP_DIR"

if ! docker compose -f docker-compose.full.yml ps --status running | grep -q 'tg-shop-app'; then
  echo "App container is not running. Restarting stack..."
  docker compose -f docker-compose.full.yml up -d
fi

if ! curl -fsS "http://127.0.0.1/health" >/dev/null; then
  echo "Health endpoint failed. Restarting app..."
  docker compose -f docker-compose.full.yml restart app nginx
fi

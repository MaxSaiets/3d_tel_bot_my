#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/telegram-shop}"
REPO_ARCHIVE="${1:-}"

if [[ -n "$REPO_ARCHIVE" ]]; then
  sudo mkdir -p "$APP_DIR"
  sudo tar -xzf "$REPO_ARCHIVE" -C "$APP_DIR"
fi

cd "$APP_DIR"

if [[ ! -f ".env" ]]; then
  echo "Missing .env in $APP_DIR"
  exit 1
fi

if [[ ! -f "deploy/espocrm/.env" ]]; then
  echo "Missing deploy/espocrm/.env in $APP_DIR"
  exit 1
fi

docker compose -f docker-compose.full.yml up -d --build

echo "Stack is up. Next: bash deploy/scripts/set_webhook.sh"

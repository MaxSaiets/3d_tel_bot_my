#!/usr/bin/env bash
set -euo pipefail

if [[ -f ".env" ]]; then
  set -a
  source .env
  set +a
fi

if [[ -z "${BOT_TOKEN:-}" || -z "${WEBHOOK_BASE_URL:-}" || -z "${WEBHOOK_SECRET:-}" ]]; then
  echo "BOT_TOKEN, WEBHOOK_BASE_URL, and WEBHOOK_SECRET are required"
  exit 1
fi

WEBHOOK_PATH="${WEBHOOK_PATH:-/telegram/webhook}"
URL="${WEBHOOK_BASE_URL%/}${WEBHOOK_PATH}"

curl -sS -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H 'Content-Type: application/json' \
  -d "{\"url\":\"${URL}\",\"secret_token\":\"${WEBHOOK_SECRET}\"}"

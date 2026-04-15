#!/usr/bin/env bash
set -euo pipefail

STAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p backups

docker compose exec -T db pg_dump -U postgres telegram_shop > "backups/telegram_shop_${STAMP}.sql"
echo "Backup saved: backups/telegram_shop_${STAMP}.sql"

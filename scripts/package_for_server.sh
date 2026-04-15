#!/usr/bin/env bash
set -euo pipefail

ARCHIVE_NAME="${1:-telegram_stack_$(date +%Y%m%d_%H%M%S).tar.gz}"

# Exclude local artifacts and secrets.
tar --exclude='.git' \
    --exclude='.venv*' \
    --exclude='webapp/node_modules' \
    --exclude='webapp/dist' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='deploy/espocrm/.env' \
    -czf "$ARCHIVE_NAME" .

echo "Created archive: $ARCHIVE_NAME"

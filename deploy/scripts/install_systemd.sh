#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/telegram-shop}"
SYSTEMD_DIR="/etc/systemd/system"

sudo cp "$APP_DIR/deploy/systemd/telegram-shop-stack.service" "$SYSTEMD_DIR/"
sudo cp "$APP_DIR/deploy/systemd/telegram-shop-health.service" "$SYSTEMD_DIR/"
sudo cp "$APP_DIR/deploy/systemd/telegram-shop-health.timer" "$SYSTEMD_DIR/"

sudo chmod +x "$APP_DIR/deploy/scripts/health_recover.sh"
sudo chmod +x "$APP_DIR/deploy/scripts/quick_deploy.sh"
sudo chmod +x "$APP_DIR/deploy/scripts/set_webhook.sh"

sudo systemctl daemon-reload
sudo systemctl enable telegram-shop-stack.service
sudo systemctl start telegram-shop-stack.service
sudo systemctl enable --now telegram-shop-health.timer

sudo systemctl status telegram-shop-stack.service --no-pager
sudo systemctl status telegram-shop-health.timer --no-pager

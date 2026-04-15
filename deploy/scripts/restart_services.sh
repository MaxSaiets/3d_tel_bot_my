#!/usr/bin/env bash
set -euo pipefail

docker compose restart app nginx

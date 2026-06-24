#!/bin/bash
# Скрипт обновления на сервере (вызывается вручную или из GitHub Actions)
set -euo pipefail

APP_DIR="${DEPLOY_PATH:-/opt/dream_to}"
BRANCH="${DEPLOY_BRANCH:-main}"

cd "$APP_DIR"
echo "=== Dream To deploy: $(pwd) ==="

git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

docker compose pull --ignore-buildable 2>/dev/null || true
docker compose build --pull
docker compose up -d

echo "=== Deploy complete ==="
docker compose ps

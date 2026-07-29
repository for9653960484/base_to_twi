#!/bin/bash
# Ручное обновление на сервере после того, как образы уже в GHCR
set -euo pipefail

APP_DIR="${DEPLOY_PATH:-/opt/base_to_twi}"
BRANCH="${DEPLOY_BRANCH:-main}"
IMAGE_BACKEND="${IMAGE_BACKEND:-ghcr.io/for9653960484/base_to_twi-backend:latest}"
IMAGE_AI="${IMAGE_AI:-ghcr.io/for9653960484/base_to_twi-ai:latest}"
IMAGE_FRONTEND="${IMAGE_FRONTEND:-ghcr.io/for9653960484/base_to_twi-frontend:latest}"

cd "$APP_DIR"
echo "=== Base To deploy: $(pwd) ==="

git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

export IMAGE_BACKEND IMAGE_AI IMAGE_FRONTEND
docker compose -f docker-compose.prod.yml down --remove-orphans || true
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans

echo "=== Deploy complete ==="
docker compose -f docker-compose.prod.yml ps

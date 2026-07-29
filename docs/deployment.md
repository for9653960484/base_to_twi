# Развёртывание на сервере и автообновление

Репозиторий: [github.com/for9653960484/base_to_twi](https://github.com/for9653960484/base_to_twi)

Схема как в `vmeste` / `portfolio`: **сборка образов в GitHub Actions** → push в GHCR → на сервере только `docker pull` + `up`.  
Так `pip`/`npm` не выполняются на VPS (там часто недоступен PyPI).

## Первичная установка на сервере

```bash
# 1. Клонировать (нужны compose, database/init, .env)
sudo mkdir -p /opt/base_to_twi
sudo chown $USER:$USER /opt/base_to_twi
git clone https://github.com/for9653960484/base_to_twi.git /opt/base_to_twi
cd /opt/base_to_twi

# 2. Настроить окружение
cp .env.example .env
nano .env   # продакшен-секреты, AI-ключи, пароли БД

# 3. Первый запуск — после того как Actions уже запушил образы в GHCR
#    (или вручную: docker login ghcr.io && docker compose -f docker-compose.prod.yml pull)
docker login ghcr.io -u YOUR_GITHUB_USER
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# 4. Проверка
docker compose -f docker-compose.prod.yml ps
curl http://localhost:8000/health
curl http://localhost:8002/health   # AI (хост-порт; не путать с vmeste на 8001)
```

Локальная разработка по-прежнему через `docker-compose.yml` или `scripts/dev-all.ps1` (без GHCR).

## Автообновление через GitHub Actions

При каждом `push` в `main` workflow `.github/workflows/deploy.yml`:

1. Собирает образы `backend`, `ai-service`, `frontend` на runner GitHub
2. Пушит их в `ghcr.io/for9653960484/base_to_twi-*`
3. По SSH на сервере: `git reset` → `docker login` → `compose pull` → `up -d`

### Настройка секретов в GitHub

**Repository → Settings → Secrets and variables → Actions**

| Secret | Пример | Описание |
|--------|--------|----------|
| `DEPLOY_HOST` | `203.0.113.10` | IP или домен сервера |
| `DEPLOY_USER` | `deploy` | SSH-пользователь |
| `DEPLOY_SSH_KEY` | `-----BEGIN OPENSSH...` | Приватный ключ (без passphrase) |
| `DEPLOY_PATH` | `/opt/base_to_twi` | Путь к проекту на сервере (только `/`) |
| `DEPLOY_PORT` | `22` | SSH-порт (опционально) |
| `GHCR_USERNAME` | `for9653960484` | Логин GitHub для `docker login` на сервере |
| `GHCR_TOKEN` | `ghp_...` | PAT с правом `read:packages` (для pull приватных образов) |

`GITHUB_TOKEN` для push образов из Actions выдаётся автоматически (`packages: write`).

### Подготовка SSH на сервере

```bash
sudo adduser deploy
sudo usermod -aG docker deploy

ssh-keygen -t ed25519 -C "github-deploy-base_to_twi" -f ~/.ssh/base_to_twi_deploy
ssh-copy-id -i ~/.ssh/base_to_twi_deploy.pub deploy@YOUR_SERVER
cat ~/.ssh/base_to_twi_deploy   # → Secret DEPLOY_SSH_KEY
```

```bash
cd /opt/base_to_twi
git config --global --add safe.directory /opt/base_to_twi
```

## Ручное обновление на сервере

```bash
cd /opt/base_to_twi
# нужен предварительный docker login ghcr.io
bash scripts/deploy-server.sh
```

## Альтернатива: cron на сервере

```cron
0 */6 * * * cd /opt/base_to_twi && git fetch origin main && git reset --hard origin/main && docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d >> /var/log/base_to_twi_deploy.log 2>&1
```

## Локальная разработка → GitHub

```powershell
git add .
git commit -m "..."
git push origin main
# Actions соберёт образы и задеплоит на сервер
```

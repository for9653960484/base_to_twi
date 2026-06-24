# Развёртывание на сервере и автообновление

Репозиторий: [github.com/for9653960484/dream_to](https://github.com/for9653960484/dream_to)

## Первичная установка на сервере

```bash
# 1. Клонировать
sudo mkdir -p /opt/dream_to
sudo chown $USER:$USER /opt/dream_to
git clone https://github.com/for9653960484/dream_to.git /opt/dream_to
cd /opt/dream_to

# 2. Настроить окружение
cp .env.example .env
nano .env   # продакшен-секреты, AI-ключи, пароли БД

# 3. Запустить
docker compose up -d

# 4. Проверка
docker compose ps
curl http://localhost:8000/health
```

## Автообновление через GitHub Actions

При каждом `push` в ветку `main` workflow `.github/workflows/deploy.yml` подключается по SSH к серверу и выполняет:

1. `git pull` (hard reset на `origin/main`)
2. `docker compose build`
3. `docker compose up -d`

### Настройка секретов в GitHub

Откройте: **Repository → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Пример | Описание |
|--------|--------|----------|
| `DEPLOY_HOST` | `203.0.113.10` | IP или домен сервера |
| `DEPLOY_USER` | `deploy` | SSH-пользователь |
| `DEPLOY_SSH_KEY` | `-----BEGIN OPENSSH...` | Приватный ключ (без passphrase) |
| `DEPLOY_PATH` | `/opt/dream_to` | Путь к проекту на сервере |
| `DEPLOY_PORT` | `22` | SSH-порт (опционально) |

### Подготовка SSH на сервере

```bash
# На сервере — пользователь deploy
sudo adduser deploy
sudo usermod -aG docker deploy

# На своей машине — ключ только для деплоя
ssh-keygen -t ed25519 -C "github-deploy-dream_to" -f ~/.ssh/dream_to_deploy

# Публичный ключ на сервер
ssh-copy-id -i ~/.ssh/dream_to_deploy.pub deploy@YOUR_SERVER

# Приватный ключ → GitHub Secret DEPLOY_SSH_KEY
cat ~/.ssh/dream_to_deploy
```

На сервере для пользователя `deploy`:

```bash
cd /opt/dream_to
git config --global --add safe.directory /opt/dream_to
```

## Ручное обновление на сервере

```bash
cd /opt/dream_to
bash scripts/deploy-server.sh
```

## Альтернатива: cron на сервере

Если GitHub Actions недоступен, обновление по расписанию:

```cron
# crontab -e
0 */6 * * * cd /opt/dream_to && git fetch origin main && git reset --hard origin/main && docker compose up -d --build >> /var/log/dream_to_deploy.log 2>&1
```

## Локальная разработка → GitHub

```powershell
# Из корня проекта
git add .
git commit -m "описание изменений"
git push origin main
```

После `push` в `main` сервер обновится автоматически (если настроены Secrets).

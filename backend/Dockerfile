FROM python:3.12-slim-bookworm

WORKDIR /app

# С некоторых VPS pypi.org недоступен (pip: "from versions: none").
# Переопределение: docker compose build --build-arg PIP_INDEX_URL=https://mirror.yandex.ru/mirrors/pypi/simple/
ARG PIP_INDEX_URL=https://pypi.org/simple
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_INDEX_URL=${PIP_INDEX_URL} \
    PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org pypi.python.org mirror.yandex.ru"

# asyncpg поставляет manylinux-wheels — системные build-essential/libpq-dev не нужны
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

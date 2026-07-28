FROM python:3.12-slim-bookworm

WORKDIR /app

# psycopg2-binary — готовые wheels, apt/libpq-dev не нужны
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

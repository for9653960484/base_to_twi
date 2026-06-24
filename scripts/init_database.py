#!/usr/bin/env python3
"""Применить database/init/*.sql к локальному PostgreSQL. Запуск из корня репозитория."""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

INIT_DIR = ROOT / "database" / "init"


def main() -> int:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    db = os.getenv("POSTGRES_DB", "dream_to")
    user = os.getenv("POSTGRES_USER", "dream_to")
    password = os.getenv("POSTGRES_PASSWORD", "dream_to_secret")

    sql_files = sorted(INIT_DIR.glob("*.sql"))
    if not sql_files:
        print(f"Нет SQL-файлов в {INIT_DIR}", file=sys.stderr)
        return 1

    print(f"Подключение к {user}@{host}:{port}/{db} ...")
    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname=db, user=user, password=password
        )
    except psycopg2.OperationalError as exc:
        print(
            f"Ошибка подключения: {exc}\n"
            "Создайте БД и пользователя (см. docs/local-development.md) или проверьте .env",
            file=sys.stderr,
        )
        return 1

    conn.autocommit = True
    cur = conn.cursor()

    for path in sql_files:
        print(f"  → {path.name}")
        sql = path.read_text(encoding="utf-8")
        try:
            cur.execute(sql)
        except psycopg2.Error as exc:
            print(f"  ⚠ {path.name}: {exc.pgerror or exc}")
            # Повторный запуск на существующей схеме — ожидаемы ошибки «already exists»

    cur.close()
    conn.close()
    print("Готово.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

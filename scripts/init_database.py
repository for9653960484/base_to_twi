#!/usr/bin/env python3
"""Применить database/init/*.sql к локальному PostgreSQL. Запуск из корня репозитория."""

import argparse
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)

INIT_DIR = ROOT / "database" / "init"
NO_VECTOR_SCHEMA = ROOT / "database" / "schemas" / "01_schema_no_vector.sql"


def pgvector_available(cur) -> bool:
    cur.execute(
        "SELECT 1 FROM pg_available_extensions WHERE name = 'vector' LIMIT 1"
    )
    return cur.fetchone() is not None


def schema_files(use_no_vector: bool) -> list[Path]:
    files: list[Path] = []
    for path in sorted(INIT_DIR.glob("*.sql")):
        if path.name == "01_schema.sql" and use_no_vector:
            if not NO_VECTOR_SCHEMA.is_file():
                print(f"Не найден файл {NO_VECTOR_SCHEMA}", file=sys.stderr)
                return []
            files.append(NO_VECTOR_SCHEMA)
        else:
            files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Инициализация схемы БД base_to")
    parser.add_argument(
        "--no-vector",
        action="store_true",
        help="Схема без pgvector (векторный поиск и AI Q&A недоступны)",
    )
    args = parser.parse_args()

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    db = os.getenv("POSTGRES_DB", "base_to")
    user = os.getenv("POSTGRES_USER", "base_to")
    password = os.getenv("POSTGRES_PASSWORD", "base_to_secret")

    os.environ.setdefault("PGCLIENTENCODING", "UTF8")

    print(f"Подключение к {user}@{host}:{port}/{db} ...")
    try:
        conn = psycopg2.connect(
            host=host, port=port, dbname=db, user=user, password=password
        )
    except UnicodeDecodeError:
        print(
            "Ошибка подключения: PostgreSQL отклонил вход (часто — неверный пароль "
            "или БД ещё не создана).\n"
            "Сначала выполните:\n"
            "  .\\.venv\\Scripts\\python.exe scripts\\create_database.py --recreate",
            file=sys.stderr,
        )
        return 1
    except psycopg2.OperationalError as exc:
        print(
            f"Ошибка подключения: {exc}\n"
            "Создайте БД и пользователя (см. docs/local-development.md) или проверьте .env",
            file=sys.stderr,
        )
        return 1

    conn.autocommit = True
    cur = conn.cursor()

    use_no_vector = args.no_vector
    if not use_no_vector and not pgvector_available(cur):
        use_no_vector = True
        print("  [info] pgvector not found, using database/schemas/01_schema_no_vector.sql")
        print("         equipment/documents OK; AI Q&A needs pgvector later")

    sql_files = schema_files(use_no_vector)
    if not sql_files:
        print(f"Нет SQL-файлов в {INIT_DIR}", file=sys.stderr)
        return 1

    had_errors = False
    for path in sql_files:
        print(f"  -> {path.relative_to(ROOT)}")
        sql = path.read_text(encoding="utf-8")
        try:
            cur.execute(sql)
        except psycopg2.Error as exc:
            had_errors = True
            print(f"  WARN {path.name}: {exc.pgerror or exc}")

    cur.close()
    conn.close()
    print("Готово.")
    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

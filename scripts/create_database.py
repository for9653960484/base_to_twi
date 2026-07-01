#!/usr/bin/env python3
"""Создать (или пересоздать) пользователя и БД PostgreSQL из .env. Требует суперпользователя postgres."""

import argparse
import getpass
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

ROOT = Path(__file__).resolve().parents[1]
# override=True: .env важнее устаревших POSTGRES_* в сессии PowerShell
load_dotenv(ROOT / ".env", override=True)


def connect_postgres(password: str):
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname="postgres",
        user="postgres",
        password=password,
    )


def recreate_database(password: str) -> None:
    db = os.getenv("POSTGRES_DB", "base_to")
    user = os.getenv("POSTGRES_USER", "base_to")
    user_password = os.getenv("POSTGRES_PASSWORD", "base_to_secret")

    env_path = ROOT / ".env"
    print(f"  [config] {env_path} -> {user}@{db}")

    conn = connect_postgres(password)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    print(f"Пересоздание {user}@{db} ...")

    cur.execute(
        """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = %s AND pid <> pg_backend_pid()
        """,
        (db,),
    )
    cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(db)))

    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (user,))
    if cur.fetchone():
        cur.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(user)))
        cur.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(user)))

    cur.execute(
        sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(user)),
        (user_password,),
    )
    cur.execute(
        sql.SQL("CREATE DATABASE {} OWNER {}").format(
            sql.Identifier(db), sql.Identifier(user)
        )
    )
    cur.execute(
        sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
            sql.Identifier(db), sql.Identifier(user)
        )
    )

    cur.close()
    conn.close()

    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=db,
        user="postgres",
        password=password,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(
        sql.SQL("GRANT ALL ON SCHEMA public TO {}").format(sql.Identifier(user))
    )

    cur.execute("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
    if cur.fetchone():
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        print("  -> extension vector")
    else:
        print("  [info] pgvector not installed — init_database.py выберет схему без vector")

    cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    print('  -> extension "uuid-ossp"')

    cur.close()
    conn.close()
    print(f"Готово: база {db} создана, пользователь {user}.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Создать или пересоздать PostgreSQL БД и пользователя из .env"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Удалить существующую БД и пользователя перед созданием",
    )
    parser.add_argument(
        "--postgres-password",
        default="",
        help="Пароль суперпользователя postgres (или POSTGRES_SUPERUSER_PASSWORD)",
    )
    args = parser.parse_args()

    if not args.recreate:
        print("Укажите --recreate для пересоздания БД.", file=sys.stderr)
        return 1

    password = (
        args.postgres_password
        or os.getenv("POSTGRES_SUPERUSER_PASSWORD")
        or ""
    )
    if not password:
        password = getpass.getpass("Пароль postgres (суперпользователь): ")

    try:
        recreate_database(password)
    except psycopg2.OperationalError as exc:
        print(
            f"Ошибка подключения: {exc}\n"
            "Нужен пароль суперпользователя postgres (не base_to).",
            file=sys.stderr,
        )
        return 1
    except psycopg2.Error as exc:
        print(f"Ошибка: {exc.pgerror or exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

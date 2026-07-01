#!/usr/bin/env python3
"""Enable pgvector in base_to DB and migrate embedding REAL[] -> vector(1536)."""

import getpass
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

VECTOR_DIM = int(os.getenv("VECTOR_DIMENSION", "1536"))


def find_psql() -> Path:
    for candidate in (
        Path(r"C:\Program Files\PostgreSQL\16\bin\psql.exe"),
        Path(r"C:\Program Files\PostgreSQL\18\bin\psql.exe"),
    ):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "psql.exe not found. Install PostgreSQL or add psql to PATH."
    )


def run_psql(psql: Path, password: str, sql: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    env["PGCLIENTENCODING"] = "UTF8"
    return subprocess.run(
        [
            str(psql),
            "-h",
            "127.0.0.1",
            "-p",
            os.getenv("POSTGRES_PORT", "5432"),
            "-U",
            "postgres",
            "-d",
            os.getenv("POSTGRES_DB", "base_to"),
            "-v",
            "ON_ERROR_STOP=1",
            "-t",
            "-A",
            "-c",
            sql,
        ],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def main() -> int:
    password = os.getenv("POSTGRES_SUPERUSER_PASSWORD") or ""
    if not password:
        password = getpass.getpass("postgres password: ")

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "base_to")

    print(f"Connecting postgres@{host}:{port}/{db} ...")

    try:
        psql = find_psql()
    except FileNotFoundError as exc:
        print(exc)
        return 1

    probe = run_psql(psql, password, "SELECT 1")
    if probe.returncode != 0:
        print("Connection failed.")
        if probe.stderr.strip():
            print(probe.stderr.strip())
        print("Use postgres superuser password (not base_to).")
        return 1

    ext_check = run_psql(
        psql,
        password,
        "SELECT 1 FROM pg_available_extensions WHERE name = 'vector'",
    )
    if ext_check.returncode != 0 or not ext_check.stdout.strip():
        print("Extension vector is not available in pg_available_extensions.")
        print("Run install_pgvector_windows.ps1 as administrator first.")
        return 1

    step = run_psql(psql, password, "CREATE EXTENSION IF NOT EXISTS vector")
    if step.returncode != 0:
        print("CREATE EXTENSION failed:")
        print(step.stderr.strip() or step.stdout.strip())
        return 1
    print("  -> CREATE EXTENSION vector")

    col_type = run_psql(
        psql,
        password,
        "SELECT data_type FROM information_schema.columns "
        "WHERE table_name = 'knowledge_chunks' AND column_name = 'embedding'",
    )
    dtype = col_type.stdout.strip() if col_type.returncode == 0 else ""

    if dtype == "ARRAY":
        print(f"  -> Migrating knowledge_chunks.embedding to vector({VECTOR_DIM})")
        migrate = run_psql(
            psql,
            password,
            f"""
            ALTER TABLE knowledge_chunks
            ALTER COLUMN embedding TYPE vector({VECTOR_DIM})
            USING CASE
                WHEN embedding IS NULL THEN NULL
                ELSE ('[' || array_to_string(embedding, ',') || ']')::vector({VECTOR_DIM})
            END
            """,
        )
        if migrate.returncode != 0:
            print("Migration failed:")
            print(migrate.stderr.strip() or migrate.stdout.strip())
            return 1
        print("  -> Migration done")
    elif dtype:
        print(f"  -> embedding column type: {dtype} (migration skipped)")
    else:
        print("  -> knowledge_chunks table not found (migration skipped)")

    version = run_psql(
        psql,
        password,
        "SELECT extversion FROM pg_extension WHERE extname = 'vector'",
    )
    if version.returncode == 0 and version.stdout.strip():
        print(f"pgvector version: {version.stdout.strip()}")

    chunks = run_psql(
        psql,
        password,
        "SELECT COUNT(*) FROM knowledge_chunks WHERE embedding IS NOT NULL",
    )
    if chunks.returncode == 0 and chunks.stdout.strip():
        print(f"Chunks with embeddings: {chunks.stdout.strip()}")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

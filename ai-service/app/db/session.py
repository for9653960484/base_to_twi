from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

_pgvector_available: bool | None = None


@contextmanager
def get_db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def vector_to_pg(vec: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def pgvector_available() -> bool:
    """Проверяет, установлен ли тип vector (pgvector) в текущей БД."""
    global _pgvector_available
    if _pgvector_available is not None:
        return _pgvector_available
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT 1 FROM pg_type WHERE typname = 'vector' LIMIT 1")
        ).fetchone()
        _pgvector_available = row is not None
    return _pgvector_available

from pathlib import Path

# backend/app/core/paths.py → корень репозитория
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

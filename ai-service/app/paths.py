from pathlib import Path

# ai-service/app/paths.py → корень репозитория
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

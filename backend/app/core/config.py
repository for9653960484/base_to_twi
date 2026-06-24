from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.paths import ENV_FILE, PROJECT_ROOT


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        extra="ignore",
    )

    APP_NAME: str = "Dream To"
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "dream_to"
    POSTGRES_USER: str = "dream_to"
    POSTGRES_PASSWORD: str = "dream_to_secret"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_VERSION: str = "v1"
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str = "http://localhost:5173"

    JWT_SECRET_KEY: str = "change-me-jwt"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    STORAGE_TYPE: str = "local"
    STORAGE_LOCAL_PATH: str = "./storage"

    AI_SERVICE_URL: str = "http://localhost:8001"
    AI_CALLBACK_SECRET: str = "change-me-callback-secret"
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI models (shared with ai-service via .env)
    AI_PROVIDER: str = "hybrid"
    AI_EXTERNAL_API_KEY: str = ""
    AI_EXTERNAL_BASE_URL: str = "https://api.openai.com/v1"
    AI_EXTERNAL_MODEL: str = "gpt-4o"
    AI_LIGHT_MODEL: str = "gpt-4o-mini"
    AI_LOCAL_BASE_URL: str = "http://localhost:11434"
    AI_LOCAL_HEAVY_MODEL: str = "llama3.1:70b"
    AI_LOCAL_LIGHT_MODEL: str = "llama3:8b"
    AI_EMBEDDING_PROVIDER: str = "external"
    AI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    AI_EMBEDDING_BASE_URL: str = ""
    AI_EMBEDDING_API_KEY: str = ""
    AI_EMBEDDING_LOCAL_MODEL: str = "nomic-embed-text"
    AI_QA_MODEL: str = ""
    VECTOR_DIMENSION: int = 1536

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def qa_model(self) -> str:
        return self.AI_QA_MODEL or self.AI_EXTERNAL_MODEL

    @property
    def storage_local_path_resolved(self) -> str:
        path = Path(self.STORAGE_LOCAL_PATH)
        if path.is_absolute():
            return str(path)
        return str((PROJECT_ROOT / path).resolve())


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

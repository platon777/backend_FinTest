from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration unique du core; les secrets viennent de l'environnement."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    APP_NAME: str = "ProFin Core Investment Platform"
    APP_VERSION: str = "2.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str = "postgresql+psycopg2://profin:profin_dev@db:5432/profin_core"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    SECRET_KEY: str = "change-me-in-a-real-environment"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    ALLOW_CREDENTIALS: bool = True

    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    PROTOTYPE_AUTO_APPROVE_SUBSCRIPTIONS: bool = True

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.ALLOWED_ORIGINS.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

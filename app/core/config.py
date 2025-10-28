from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "FinTest API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # Database Configuration - SQL Server Azure
    DB_SERVER: str = "finance777.database.windows.net"
    DB_NAME: str = "Db_test"
    DB_USER: str = "sqladmin"
    DB_PASSWORD: str = "Tsukuyomi777*"
    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"
    DATABASE_URL: str = "mssql+pyodbc://sqladmin:Tsukuyomi777*@finance777.database.windows.net/Db_test?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Settings
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    ALLOWED_METHODS: str = "GET,POST,PUT,DELETE,PATCH,OPTIONS"
    ALLOWED_HEADERS: str = "*"
    ALLOW_CREDENTIALS: bool = True

    # Redis Configuration
    REDIS_URL: Optional[str] = None
    REDIS_CACHE_EXPIRE: int = 3600

    # Email Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_FOLDER: str = "uploads"
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,pdf,doc,docx,xls,xlsx"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "logs/app.log"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def parse_origins(cls, v: str) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ALLOWED_METHODS")
    @classmethod
    def parse_methods(cls, v: str) -> List[str]:
        if isinstance(v, str):
            return [method.strip() for method in v.split(",")]
        return v

    @field_validator("ALLOWED_EXTENSIONS")
    @classmethod
    def parse_extensions(cls, v: str) -> List[str]:
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


settings = Settings()

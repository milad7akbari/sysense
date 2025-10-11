from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, AnyHttpUrl, field_validator, ValidationInfo
from typing import List, Optional, Any
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra='ignore')

    ENV: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "project_name"
    API_V1_STR: str

    # DB
    DATABASE_URL: Optional[PostgresDsn] = None
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    REDIS_URL: str

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 5
    ALGORITHM: str = "HS256"

    # CORS & hosts
    CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]
    TRUSTED_HOSTS: List[str] = ["*"]

    # Rate limiting
    RATE_LIMIT: int = 120  # per minute

    # DB pool tuning
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    @field_validator("SQLALCHEMY_DATABASE_URI", mode='before')
    @classmethod
    def assemble_db_uri(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v

        env_db = info.data.get("DATABASE_URL") or os.getenv("DATABASE_URL")
        if env_db:
            uri = str(env_db)
            return uri.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
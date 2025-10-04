from pydantic import BaseSettings, PostgresDsn, AnyHttpUrl, validator
from typing import List, Optional
import os

class Settings(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "project_name"

    # DB
    DATABASE_URL: Optional[PostgresDsn] = None
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("SQLALCHEMY_DATABASE_URI", pre=True, always=True)
    def assemble_db_uri(cls, v, values):
        env_db = values.get("DATABASE_URL") or os.getenv("DATABASE_URL")
        if v:
            return v
        if env_db:
            uri = str(env_db)
            if uri.startswith("postgres://"):
                uri = uri.replace("postgres://", "postgresql+asyncpg://", 1)
            if uri.startswith("postgresql://"):
                uri = uri.replace("postgresql://", "postgresql+asyncpg://", 1)
            return uri
        return v

settings = Settings()

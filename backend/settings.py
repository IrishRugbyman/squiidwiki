from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    user: str = "postgres"
    password: str = "postgres"
    host: str = "localhost"
    port: str = "5432"
    database: str = "squiidwiki_db"
    max_connections: int = 20
    connection_timeout: int = 60
    pool_recycle: int = 3600


class AuthSettings(BaseModel):
    enabled: bool = True
    jwt_secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24h
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    default_admin_username: str = "admin"
    default_admin_password: str = "F$SquiidWiki@Admin2025"


class ServerSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8002


class LoggingSettings(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class APISettings(BaseModel):
    default_page_size: int = 50
    max_page_size: int = 200
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "https://squiidwiki.onrender.com"]
    )


class BusinessSettings(BaseModel):
    max_name_length: int = 100
    max_description_length: int = 1000


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    database_url: Optional[str] = None

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    api: APISettings = Field(default_factory=APISettings)
    business: BusinessSettings = Field(default_factory=BusinessSettings)

    @property
    def env(self) -> str:
        return self.app_env

    def get_database_url(self) -> str:
        """Sync URL (psycopg2) — used by Alembic."""
        if self.database_url:
            return self.database_url
        db = self.database
        return f"postgresql://{db.user}:{db.password}@{db.host}:{db.port}/{db.database}"

    def get_async_database_url(self) -> str:
        """Async URL (asyncpg) — used by the application."""
        sync = self.get_database_url()
        return sync.replace("postgresql://", "postgresql+asyncpg://", 1)

    def is_development(self) -> bool:
        return self.app_env == "development"

    def is_production(self) -> bool:
        return self.app_env == "production"

    def is_test(self) -> bool:
        return self.app_env == "test"


settings = Settings()

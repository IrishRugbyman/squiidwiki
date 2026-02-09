"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    DATABASE_URL: str = "sqlite:///./squiidwiki.db"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ADMIN_PASSWORD: str = "admin"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()

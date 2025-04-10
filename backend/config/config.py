import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

# Get the application root directory
ROOT_DIR = Path(__file__).parent.parent.parent


class AppSettings(BaseSettings):
    """Central application settings using Pydantic for validation"""
    
    # Environment
    APP_ENV: str = os.environ.get("APP_ENV", "development")
    TEST_MODE: bool = os.environ.get("TEST_MODE", "0") == "1"
    DEBUG: bool = os.environ.get("DEBUG", "1") == "1"
    
    # Database
    DB_NAME: str = "squiidvault_test.db" if os.environ.get("TEST_MODE", "0") == "1" else "squiidvault.db"
    
    @property
    def DB_PATH(self) -> Path:
        """Return the database path, using persistent storage in production"""
        if self.is_production():
            # Use persistent storage on Render
            return Path("/data") / self.DB_NAME
        return ROOT_DIR / self.DB_NAME
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """Returns the SQLAlchemy database URL"""
        return f"sqlite:///{self.DB_PATH}"
    
    # JWT Authentication
    JWT_SECRET_KEY: str = os.environ.get(
        "JWT_SECRET_KEY", 
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Default dev key
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = int(os.environ.get("PORT", "8002"))
    
    # Backup settings
    BACKUP_DIR: Path = ROOT_DIR / "backups"
    
    # Other settings
    AUTH_BYPASS_ENABLED: bool = APP_ENV == "development"
    AUTH_BYPASS_CODE: str = "dev_mode_1234"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def get_db_path(self) -> str:
        """Returns the absolute path to the database file"""
        return str(self.DB_PATH)
    
    def get_sqlalchemy_url(self) -> str:
        """Returns the SQLAlchemy database URL"""
        return self.SQLALCHEMY_DATABASE_URI
    
    def is_production(self) -> bool:
        """Checks if the application is running in production mode"""
        return self.APP_ENV.lower() == "production"
    
    def is_test(self) -> bool:
        """Checks if the application is running in test mode"""
        return self.TEST_MODE


# Create a singleton instance
settings = AppSettings() 
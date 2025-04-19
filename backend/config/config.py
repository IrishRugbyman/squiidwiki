import os
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Répertoire racine de l'application
ROOT_DIR = Path(__file__).parent.parent.parent

# Configuration principale - toutes les valeurs sont définies ici
class Config:
    """Configuration centrale de l'application SquiidWiki"""
    
    #######################
    # PARAMÈTRES GÉNÉRAUX #
    #######################
    
    # Environnement et mode
    APP_ENV = os.environ.get("APP_ENV", "development")  # 'development', 'testing', 'production'
    DEBUG = APP_ENV != "production"                     # Active les fonctionnalités de débogage en dev
    TEST_MODE = os.environ.get("TEST_MODE", "0") == "1" # Si True, utilise la base de données de test
    
    # Serveur
    HOST = "0.0.0.0"                  # Adresse d'écoute du serveur
    PORT = 8002                       # Port d'écoute du serveur
    WORKERS = 4                       # Nombre de workers pour le serveur ASGI
    REQUEST_TIMEOUT = 60              # Timeout des requêtes (secondes)
    
    ########################
    # PARAMÈTRES DE BASE DE DONNÉES #
    ########################
    
    # Configuration PostgreSQL
    PG_CONFIG = {
        "user": os.environ.get("POSTGRES_USER", "postgres"),
        "password": os.environ.get("POSTGRES_PASSWORD", "F$Stagiaire42"),
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
        "database": os.environ.get("POSTGRES_DB", "squiidvault"),
        "min_connections": 1,
        "max_connections": 10,
        "connection_timeout": 30
    }
    
    # Default Admin User - Will be created if no admin exists
    DEFAULT_ADMIN = {
        "username": os.environ.get("DEFAULT_ADMIN_USER", "admin"),
        "password": os.environ.get("DEFAULT_ADMIN_PASSWORD", "F$SquiidWiki@Admin2025"),
        "is_admin": True
    }
    
    # Chemins pour les sauvegardes et exports
    BACKUP_DIR = ROOT_DIR / "backups"
    EXPORT_DIR = ROOT_DIR / "exports"
    
    # Nombre maximal de backups à conserver
    MAX_BACKUPS = 10
    
    ########################
    # PARAMÈTRES DE SÉCURITÉ #
    ########################
    
    # JWT Authentication
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 heures
    REFRESH_TOKEN_EXPIRE_DAYS = 7          # 7 jours pour les refresh tokens
    
    # Protection CSRF
    CSRF_ENABLED = True                    # Active la protection CSRF
    CSRF_SECRET = os.environ.get("CSRF_SECRET", "csrfsecret123456789")    # Secret pour les tokens CSRF
    
    # Paramètres de mot de passe
    PASSWORD_MIN_LENGTH = 8                # Longueur minimale du mot de passe
    BCRYPT_ROUNDS = 12                     # Rounds de hachage bcrypt
    
    # Développement/débogage
    AUTH_BYPASS_ENABLED = APP_ENV == "development"  # Active le contournement d'auth en dev
    AUTH_BYPASS_CODE = "dev_mode_1234"              # Code de contournement
    
    ########################
    # PARAMÈTRES DE LOGGING #
    ########################
    
    LOG_LEVEL = "INFO"                     # Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR = ROOT_DIR / "logs"
    LOG_FILE = LOG_DIR / "squiidwiki.log"
    LOG_MAX_SIZE = 10 * 1024 * 1024        # 10 MB
    LOG_BACKUP_COUNT = 5                   # Nombre de fichiers de backup à conserver
    
    ########################
    # PARAMÈTRES API #
    ########################
    
    # Pagination
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 200
    
    # Rate limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT = {
        "default": "100/minute",
        "auth": "10/minute",
        "admin": "200/minute"
    }
    
    # CORS
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://squiidwiki.onrender.com"
    ]
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_HEADERS = ["*"]
    
    ########################
    # PARAMÈTRES MÉTIER #
    ########################
    
    # Types d'éléments spéciaux qui ne peuvent pas être supprimés
    SPECIAL_SET_TYPES = ["system"]
    
    # Limites de caractères
    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 1000
    
    # Autres paramètres métier
    AUTO_ARCHIVE_DAYS = 365               # Nombre de jours avant d'archiver automatiquement


class Settings:
    """Classe d'accès à la configuration centrale de l'application"""
    
    def __init__(self):
        """Initialise les paramètres et applique les ajustements nécessaires"""
        
        # Créer les répertoires requis s'ils n'existent pas
        os.makedirs(Config.BACKUP_DIR, exist_ok=True)
        os.makedirs(Config.EXPORT_DIR, exist_ok=True)
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        
        # Ajuster les paramètres pour le mode test
        if Config.TEST_MODE:
            Config.LOG_FILE = Config.LOG_DIR / "squiidwiki_test.log"
            Config.JWT_SECRET_KEY = "test_secret_key_not_for_production"
            
            # Ajuster la configuration PostgreSQL pour les tests
            Config.PG_CONFIG["database"] = "squiidvault_test"
    
    # Direct access to JWT settings
    @property
    def JWT_SECRET_KEY(self) -> str:
        return Config.JWT_SECRET_KEY
        
    @property
    def JWT_ALGORITHM(self) -> str:
        return Config.JWT_ALGORITHM
        
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return Config.ACCESS_TOKEN_EXPIRE_MINUTES
    
    @property
    def AUTH_BYPASS_ENABLED(self) -> bool:
        return Config.AUTH_BYPASS_ENABLED
        
    @property
    def AUTH_BYPASS_CODE(self) -> str:
        return Config.AUTH_BYPASS_CODE
    
    @property
    def DEBUG(self) -> bool:
        return Config.DEBUG
        
    @property
    def APP_ENV(self) -> str:
        return Config.APP_ENV
    
    @property
    def PORT(self) -> int:
        return Config.PORT
        
    @property
    def HOST(self) -> str:
        return Config.HOST
        
    @property
    def DB_PATH(self) -> str:
        """Get database connection path"""
        return self.get_sqlalchemy_url()
    
    #############################
    # Méthodes d'environnement #
    #############################
    
    def is_test(self) -> bool:
        """Vérifie si l'application est en mode test"""
        return Config.TEST_MODE
    
    def is_production(self) -> bool:
        """Vérifie si l'application est en mode production"""
        return Config.APP_ENV.lower() == "production"
    
    def is_development(self) -> bool:
        """Vérifie si l'application est en mode développement"""
        return Config.APP_ENV.lower() == "development"
    
    def get_environment(self) -> str:
        """Retourne l'environnement actuel"""
        return Config.APP_ENV
    
    #############################
    # Méthodes de base de données #
    #############################
    
    def get_pg_config(self) -> dict:
        """Retourne la configuration PostgreSQL"""
        return Config.PG_CONFIG
    
    def get_sqlalchemy_url(self) -> str:
        """Retourne l'URL de la base de données SQLAlchemy pour PostgreSQL"""
        pg = Config.PG_CONFIG
        return f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['database']}"
    
    #############################
    # Méthodes de chemins/fichiers #
    #############################
    
    def get_base_dir(self) -> Path:
        """Retourne le répertoire de base de l'application"""
        return ROOT_DIR
    
    def get_backup_dir(self) -> Path:
        """Retourne le répertoire des sauvegardes"""
        return Config.BACKUP_DIR
    
    def get_export_dir(self) -> Path:
        """Retourne le répertoire des exports"""
        return Config.EXPORT_DIR
    
    def get_log_file(self) -> Path:
        """Retourne le chemin du fichier de log"""
        return Config.LOG_FILE
    
    #############################
    # Méthodes de sécurité #
    #############################
    
    def get_jwt_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres JWT"""
        return {
            "secret_key": Config.JWT_SECRET_KEY,
            "algorithm": Config.JWT_ALGORITHM,
            "access_token_expire_minutes": Config.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": Config.REFRESH_TOKEN_EXPIRE_DAYS
        }
    
    def get_default_admin(self) -> Dict[str, Any]:
        """Retourne les informations du compte admin par défaut"""
        return Config.DEFAULT_ADMIN
    
    def get_cors_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres CORS"""
        return {
            "allow_origins": Config.CORS_ORIGINS,
            "allow_methods": Config.CORS_METHODS,
            "allow_headers": Config.CORS_HEADERS,
            "allow_credentials": True
        }
    
    def get_rate_limit(self, endpoint_type: str = "default") -> str:
        """Retourne la limite de débit pour un type d'endpoint donné"""
        return Config.RATE_LIMIT.get(endpoint_type, Config.RATE_LIMIT["default"])
    
    #############################
    # Méthodes API/Pagination #
    #############################
    
    def get_pagination_settings(self) -> Dict[str, int]:
        """Retourne les paramètres de pagination"""
        return {
            "default_page_size": Config.DEFAULT_PAGE_SIZE,
            "max_page_size": Config.MAX_PAGE_SIZE
        }
    
    def get_server_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres du serveur"""
        return {
            "host": Config.HOST,
            "port": Config.PORT,
            "workers": Config.WORKERS,
            "timeout": Config.REQUEST_TIMEOUT
        }


# Créer une instance singleton
settings = Settings() 
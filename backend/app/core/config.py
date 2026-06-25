from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Private Converter"
    DEBUG: bool = Field(default=False, env="DEBUG")
    SECRET_KEY: str = Field(env="SECRET_KEY", default="change-me-in-production")
    ENVIRONMENT: str = Field(env="ENVIRONMENT", default="development")
    
    # CORS
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:8000"],
        env="CORS_ALLOWED_ORIGINS"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./db.sqlite3",
        env="DATABASE_URL"
    )
    DB_ENGINE: str = Field(default="", env="DB_ENGINE")
    DB_NAME: str = Field(default="", env="DB_NAME")
    DB_USER: str = Field(default="", env="DB_USER")
    DB_PASSWORD: str = Field(default="", env="DB_PASSWORD")
    DB_HOST: str = Field(default="", env="DB_HOST")
    DB_PORT: str = Field(default="", env="DB_PORT")
    
    # JWT Authentication
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_SECRET_KEY: Optional[str] = Field(default=None, env="JWT_SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=24 * 60,  # 24 hours
        env="JWT_EXPIRATION_HOURS"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="JWT_REFRESH_EXPIRE_DAYS")
    
    # File Storage
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    UPLOAD_DIR: Path = Field(default="data/uploads", env="UPLOAD_DIR")
    RESULTS_DIR: Path = Field(default="data/results", env="RESULTS_DIR")
    TEMP_DIR: Path = Field(default="data/temp", env="TEMP_DIR")
    MAX_FILE_SIZE: int = Field(
        default=1073741824,  # 1GB
        env="MAX_FILE_SIZE"
    )
    
    # Conversion Settings
    MAX_CONCURRENT_PROCESSES: int = Field(
        default=4,
        env="MAX_CONCURRENT_PROCESSES"
    )
    PROCESS_TIMEOUT: int = Field(default=300, env="PROCESS_TIMEOUT")
    MAX_RETRIES: int = Field(default=2, env="MAX_RETRIES")
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        env="RATE_LIMIT_PER_MINUTE"
    )
    DAILY_CONVERSIONS_PER_USER: int = Field(
        default=50,
        env="DAILY_CONVERSIONS_PER_USER"
    )
    MAX_CONCURRENT_PER_USER: int = Field(
        default=3,
        env="MAX_CONCURRENT_PER_USER"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_DIR: Path = Field(default="logs")

    # API / Auth
    API_V1_STR: str = Field(default="/api", env="API_V1_STR")
    FIRST_SUPERUSER: str = Field(default="admin@example.com", env="FIRST_SUPERUSER")
    FIRST_SUPERUSER_PASSWORD: str = Field(default="changeme", env="FIRST_SUPERUSER_PASSWORD")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._setup_paths()
    
    def _setup_paths(self):
        # Convert relative paths to absolute
        self.UPLOAD_DIR = self.BASE_DIR / self.UPLOAD_DIR
        self.RESULTS_DIR = self.BASE_DIR / self.RESULTS_DIR
        self.TEMP_DIR = self.BASE_DIR / self.TEMP_DIR
        self.LOG_DIR = self.BASE_DIR / self.LOG_DIR
        
        # Create directories
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Handle JWT secret key fallback
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = self.SECRET_KEY
    
    @property
    def sqlite_db_path(self) -> Path:
        if self.DATABASE_URL.startswith("sqlite:///"):
            db_path = self.DATABASE_URL.replace("sqlite:///", "")
            return self.BASE_DIR / db_path
        return self.BASE_DIR / "db.sqlite3"
    
    @property
    def alembic_config_path(self) -> Path:
        return self.BASE_DIR / "alembic.ini"
    
    @property
    def media_root(self) -> Path:
        return self.BASE_DIR / "media"
    
    @property
    def static_root(self) -> Path:
        return self.BASE_DIR / "staticfiles"


# Create settings instance
settings = Settings()
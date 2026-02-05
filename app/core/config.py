import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bug Reporting System"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    @field_validator("ALLOWED_HOSTS", mode="before")
    def assemble_allowed_hosts(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "bugtracker"
    POSTGRES_PORT: int = 5432
    SQLALCHEMY_DATABASE_URI: str = ""

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_connection(cls, v: str | None, info) -> str:
        if isinstance(v, str) and v:
            return v
        vals = info.data
        return f"postgresql+asyncpg://{vals.get('POSTGRES_USER')}:{vals.get('POSTGRES_PASSWORD')}@{vals.get('POSTGRES_SERVER')}:{vals.get('POSTGRES_PORT')}/{vals.get('POSTGRES_DB')}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Security
    SECRET_KEY: str = "supersecretkey" # Change in production
    ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    PRIVATE_KEY_PATH: str = "keys/private.pem"
    PUBLIC_KEY_PATH: str = "keys/public.pem"
    
    PRIVATE_KEY: str = ""
    PUBLIC_KEY: str = ""

    def load_keys(self):
        """
        Loads keys using the robust key_management module.
        Generates keys if they don't exist.
        """
        from app.core.key_management import ensure_keys_exist, load_keys
        
        # Ensure keys exist or generate them
        ensure_keys_exist(self.PRIVATE_KEY_PATH, self.PUBLIC_KEY_PATH)
        
        # Load keys into memory
        loaded = load_keys(self.PRIVATE_KEY_PATH, self.PUBLIC_KEY_PATH)
        self.PRIVATE_KEY = loaded["private_key"]
        self.PUBLIC_KEY = loaded["public_key"]
        
        print(f"Securely loaded RSA keys from {self.PRIVATE_KEY_PATH} and {self.PUBLIC_KEY_PATH}")

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
# Attempt to load keys on startup
try:
    settings.load_keys()
except Exception as e:
    print(f"CRITICAL: Failed to load authentication keys: {e}")
    # We do not exit here to allow import, but app startup should fail if keys are missing.
    # main.py will handle the hard crash on startup.

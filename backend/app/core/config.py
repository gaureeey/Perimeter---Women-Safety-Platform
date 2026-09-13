"""
PERIMETER Backend Core Configuration
"""
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "PERIMETER Safety Platform API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security / JWT
    SECRET_KEY: str = "perimeter_super_secret_jwt_key_2026_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'perimeter.db')}"
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:5500",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5500",
        "*"
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )

settings = Settings()


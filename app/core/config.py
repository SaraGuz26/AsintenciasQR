# app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import field_validator
import json

class Settings(BaseSettings):
    ENV: str = "dev"
    SECRET_KEY: str = "change_me"
    SECRET_QR: str = "cambia_esto_por_un_secreto_largo"
    DATABASE_URL: str = "mysql+pymysql://asistencias_user:asistencias_pass@db:3306/asistencias_db?charset=utf8mb4"
    CORS_ORIGINS: list[str] = ["http://localhost:8000", "http://localhost", "http://127.0.0.1"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                return json.loads(v)
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()

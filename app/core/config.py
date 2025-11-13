import os
from functools import lru_cache
from pydantic import BaseModel

class Settings(BaseModel):
    ENV: str = os.getenv("ENV", "dev")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_me")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://asistencias_user:asistencias_pass@db:3306/asistencias_db?charset=utf8mb4",
    )
    # Dev: agrega los puertos que uses (vite/parcel/streamlit/etc.)
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ]

@lru_cache
def get_settings() -> Settings:
    return Settings()
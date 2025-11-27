# app/core/config.py
import os, json
from functools import lru_cache
from pydantic import BaseModel

def _parse_origins(raw: str | None) -> list[str]:
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith("["):
        try:
            return json.loads(raw)
        except Exception:
            pass
    return [o.strip() for o in raw.split(",") if o.strip()]

class Settings(BaseModel):
    ENV: str = os.getenv("ENV", "dev")

    # claves
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_me")
    SECRET_QR: str  = os.getenv("SECRET_QR",  "dev_qr_secret_largo_y_unico")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 horas

    # DB
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://asistencias_user:asistencias_pass@db:3306/asistencias_db?charset=utf8mb4",
    )

    # CORS
    CORS_ORIGINS: list[str] = _parse_origins(os.getenv("CORS_ORIGINS")) or [
        "http://localhost:8000","http://localhost","http://127.0.0.1",
        "http://localhost:5173","http://127.0.0.1:5173","http://localhost:3000","http://127.0.0.1:3000",
    ]

@lru_cache
def get_settings() -> Settings:
    return Settings()

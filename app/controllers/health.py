# app/controllers/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.web.deps import get_db

router = APIRouter(prefix="", tags=["health"])

@router.get("/healthz")  # liveness: ¿está vivo el proceso?
def healthz():
    s = get_settings()
    return {"ok": True, "env": s.ENV}

@router.get("/readyz")   # readiness: ¿puede atender tráfico (DB ok)?
def readyz(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"ok": True}

@router.get("/")         # raíz simple
def root():
    return {"name": "Asistencias QR UTN", "status": "running"}

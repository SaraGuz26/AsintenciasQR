# app/controllers/scan.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.services.scan_service import validar_y_registrar

router = APIRouter(prefix="/scan", tags=["scan"])

class ScanIn(BaseModel):
    qr_text: str
    punto_id: int

@router.post("/validar")
def scan_validar(data: ScanIn, db: Session = Depends(get_db)):
    """
    Valida el QR (HMAC, exp, credencial) y registra asistencia si corresponde.
    Devuelve datos para mostrar en pantalla (profesor, materia, estado, horario).
    """
    return validar_y_registrar(db, data.qr_text, data.punto_id)

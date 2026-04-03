from app.controllers.asistencia import generar_instancias_del_dia
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from app.web.deps import get_db

router = APIRouter(prefix="/test", tags=["test"])

@router.get("/generar-instancias")
def test_generar(db: Session = Depends(get_db)):
    generar_instancias_del_dia()
    return {"ok": True}
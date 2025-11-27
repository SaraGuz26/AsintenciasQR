from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.services.credencial_service import credencial_service
from app.repositories.credencial_repo import credencial_repo
from app.schemas.credencial import CredencialOut

router = APIRouter(prefix="/credenciales", tags=["credenciales"])

@router.post("/emitir/{docente_id}", response_model=CredencialOut)
def emitir(docente_id: int, db: Session = Depends(get_db)):
    return credencial_service.emitir(db, docente_id)

@router.post("/{credencial_id}/revocar", response_model=CredencialOut)
def revocar(credencial_id: int, db: Session = Depends(get_db), motivo: str | None = Body(default=None)):
    obj = credencial_service.revocar(db, credencial_id, motivo)
    if not obj: raise HTTPException(404, "No existe")
    return obj

@router.get("/activa/{docente_id}", response_model=CredencialOut | None)
def activa(docente_id: int, db: Session = Depends(get_db)):
    return credencial_repo.activa_de_docente(db, docente_id)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.services.turno_excepcion_service import turno_excepcion_service
from app.schemas.turno_excepcion import TurnoExcepcionOut, TurnoExcepcionCreate, TurnoExcepcionUpdate

router = APIRouter(prefix="/turno-excepciones", tags=["turno-excepcion"])

@router.get("", response_model=list[TurnoExcepcionOut])
def listar(db: Session = Depends(get_db)): return turno_excepcion_service.list(db)

@router.post("", response_model=TurnoExcepcionOut)
def crear(data: TurnoExcepcionCreate, db: Session = Depends(get_db)):
    return turno_excepcion_service.create(db, data)

@router.put("/{exc_id}", response_model=TurnoExcepcionOut)
def actualizar(exc_id: int, data: TurnoExcepcionUpdate, db: Session = Depends(get_db)):
    obj = turno_excepcion_service.update(db, exc_id, data)
    if not obj: raise HTTPException(404, "No existe")
    return obj

@router.delete("/{exc_id}")
def eliminar(exc_id: int, db: Session = Depends(get_db)):
    turno_excepcion_service.remove(db, exc_id); return {"ok": True}

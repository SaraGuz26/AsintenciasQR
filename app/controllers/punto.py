from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.services.punto_service import punto_service
from app.schemas.punto import PuntoOut, PuntoCreate, PuntoUpdate

router = APIRouter(prefix="/puntos", tags=["puntos"])

@router.get("", response_model=list[PuntoOut])
def listar(db: Session = Depends(get_db)): return punto_service.list(db)

@router.post("", response_model=PuntoOut)
def crear(data: PuntoCreate, db: Session = Depends(get_db)): return punto_service.create(db, data)

@router.put("/{punto_id}", response_model=PuntoOut)
def actualizar(punto_id: int, data: PuntoUpdate, db: Session = Depends(get_db)):
    obj = punto_service.update(db, punto_id, data)
    if not obj: from fastapi import HTTPException; raise HTTPException(404, "No existe")
    return obj

@router.delete("/{punto_id}")
def eliminar(punto_id: int, db: Session = Depends(get_db)):
    punto_service.remove(db, punto_id); return {"ok": True}

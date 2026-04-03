from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.services.materia_service import materia_service
from app.schemas.materia import MateriaOut, MateriaCreate, MateriaUpdate

router = APIRouter(prefix="/materias", tags=["materias"])

@router.get("", response_model=list[MateriaOut])
def listar(db: Session = Depends(get_db)):
    return materia_service.list(db)

@router.post("", response_model=MateriaOut)
def crear(data: MateriaCreate, db: Session = Depends(get_db)):
    return materia_service.create(db, data)

@router.put("/{materia_id}", response_model=MateriaOut)
def actualizar(materia_id: int, data: MateriaUpdate, db: Session = Depends(get_db)):
    obj = materia_service.update(db, materia_id, data)
    if not obj:
        raise HTTPException(404, "No existe")
    return obj

@router.delete("/{materia_id}")
def eliminar(materia_id: int, db: Session = Depends(get_db)):
    materia_service.remove(db, materia_id)
    return {"ok": True}

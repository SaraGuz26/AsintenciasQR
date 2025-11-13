from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.web.deps import get_db, get_docente_service
from app.schemas.docente import DocenteCreate, DocenteUpdate, DocenteOut
from app.services.docente_service import DocenteService

router = APIRouter(prefix="/docentes", tags=["docentes"])

@router.get("", response_model=list[DocenteOut])
def listar(limit: int = 50, offset: int = 0,
           db: Session = Depends(get_db),
           svc: DocenteService = Depends(get_docente_service)):
    return svc.listar(db, limit, offset)

@router.get("/{docente_id}", response_model=DocenteOut)
def obtener(docente_id: int,
            db: Session = Depends(get_db),
            svc: DocenteService = Depends(get_docente_service)):
    return svc.obtener(db, docente_id)

@router.post("", response_model=DocenteOut, status_code=201)
def crear(data: DocenteCreate,
          db: Session = Depends(get_db),
          svc: DocenteService = Depends(get_docente_service)):
    return svc.crear(db, data)

@router.put("/{docente_id}", response_model=DocenteOut)
def actualizar(docente_id: int, data: DocenteUpdate,
               db: Session = Depends(get_db),
               svc: DocenteService = Depends(get_docente_service)):
    return svc.actualizar(db, docente_id, data)

@router.delete("/{docente_id}", status_code=204)
def borrar(docente_id: int,
           db: Session = Depends(get_db),
           svc: DocenteService = Depends(get_docente_service)):
    svc.borrar(db, docente_id)
    return

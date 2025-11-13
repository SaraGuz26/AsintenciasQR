from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.repositories.docente_repo import DocenteRepository
from app.schemas.docente import DocenteCreate, DocenteUpdate
from app.models.docente import Docente

class DocenteService:
    def __init__(self, repo: DocenteRepository):
        self.repo = repo

    def listar(self, db: Session, limit=50, offset=0):
        return self.repo.list(db, limit, offset)

    def obtener(self, db: Session, docente_id: int) -> Docente:
        obj = self.repo.get(db, docente_id)
        if not obj:
            raise HTTPException(404, "Docente no encontrado")
        return obj

    def crear(self, db: Session, data: DocenteCreate) -> Docente:
        if self.repo.get_by_legajo(db, data.legajo):
            raise HTTPException(400, "Legajo ya registrado")
        if self.repo.get_by_email(db, data.email):
            raise HTTPException(400, "Email ya registrado")
        return self.repo.create(db, data)

    def actualizar(self, db: Session, docente_id: int, data: DocenteUpdate) -> Docente:
        obj = self.obtener(db, docente_id)
        # Reglas extra si cambian email/legajo (opcional)
        return self.repo.update(db, obj, data)

    def borrar(self, db: Session, docente_id: int) -> None:
        obj = self.obtener(db, docente_id)
        self.repo.remove(db, obj.id)

docente_service = DocenteService(repo=DocenteRepository(Docente))

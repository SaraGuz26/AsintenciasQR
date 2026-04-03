from sqlalchemy.orm import Session
from app.repositories.docente_repo import docente_repo
from app.schemas.docente import DocenteCreate, DocenteUpdate
from app.models.docente import Docente

class DocenteService:
    def list(self, db: Session): return docente_repo.list(db)
    def get(self, db: Session, id: int): return docente_repo.get(db, id)
    def create(self, db: Session, data: DocenteCreate): return docente_repo.create(db, data)
    def update(self, db: Session, id: int, data: DocenteUpdate):
        obj = docente_repo.get(db, id)
        return docente_repo.update(db, obj, data) if obj else None
    def remove(self, db: Session, id:int): return docente_repo.remove(db, id)

docente_service = DocenteService()

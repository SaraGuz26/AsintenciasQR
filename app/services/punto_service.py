from sqlalchemy.orm import Session
from app.repositories.punto_repo import punto_repo
from app.schemas.punto import PuntoCreate, PuntoUpdate

class PuntoService:
    def list(self, db: Session): return punto_repo.list(db)
    def create(self, db: Session, data: PuntoCreate): return punto_repo.create(db, data)
    def update(self, db: Session, id: int, data: PuntoUpdate):
        obj = punto_repo.get(db, id)
        return punto_repo.update(db, obj, data) if obj else None
    def remove(self, db: Session, id:int): return punto_repo.remove(db, id)

punto_service = PuntoService()

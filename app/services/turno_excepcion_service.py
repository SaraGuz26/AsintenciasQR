from sqlalchemy.orm import Session
from app.repositories.turno_excepcion_repo import turno_exc_repo
from app.schemas.turno_excepcion import TurnoExcepcionCreate, TurnoExcepcionUpdate

class TurnoExcepcionService:
    def list(self, db: Session): return turno_exc_repo.list(db)
    def create(self, db: Session, data: TurnoExcepcionCreate): return turno_exc_repo.create(db, data)
    def update(self, db: Session, id: int, data: TurnoExcepcionUpdate):
        obj = turno_exc_repo.get(db, id)
        return turno_exc_repo.update(db, obj, data) if obj else None
    def remove(self, db: Session, id:int): return turno_exc_repo.remove(db, id)

turno_excepcion_service = TurnoExcepcionService()

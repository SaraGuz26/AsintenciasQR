from sqlalchemy.orm import Session
from app.repositories.base import CRUDBase
from app.models.docente import Docente
from app.schemas.docente import DocenteCreate, DocenteUpdate

class DocenteRepository(CRUDBase[Docente, DocenteCreate, DocenteUpdate]):
    def get_by_legajo(self, db: Session, legajo: str) -> Docente | None:
        return db.query(Docente).filter(Docente.legajo == legajo).first()

    def get_by_email(self, db: Session, email: str) -> Docente | None:
        return db.query(Docente).filter(Docente.email == email).first()

docente_repo = DocenteRepository(Docente)

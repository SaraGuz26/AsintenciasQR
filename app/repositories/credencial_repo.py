from sqlalchemy.orm import Session
from sqlalchemy import select
from app.repositories.base import Base
from app.models.credencial import Credencial

class CredencialRepository(Base[Credencial, object, object]):
    def activa_de_docente(self, db: Session, docente_id: int) -> Credencial | None:
        return db.scalars(select(Credencial).where(Credencial.docente_id==docente_id, Credencial.revocado == False
)).first()

credencial_repo = CredencialRepository(Credencial)

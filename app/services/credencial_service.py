import secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.credencial_repo import credencial_repo
from app.schemas.credencial import CredencialCreate
from app.models.credencial import Credencial

class CredencialService:
    def emitir(self, db: Session, docente_id: int) -> Credencial:
        # revoca activa si existe
        activa = credencial_repo.activa_de_docente(db, docente_id)
        if activa:
            activa.activo = False
            activa.revocado_en = datetime.now(timezone.utc)
            db.commit()

        # crea nueva
        nonce = secrets.token_urlsafe(24)
        c = Credencial(docente_id=docente_id, nonce_actual=nonce, emitido_en=datetime.now(timezone.utc), activo=True)
        db.add(c); db.commit(); db.refresh(c)
        return c

    def revocar(self, db: Session, credencial_id: int, motivo: str | None = None) -> Credencial | None:
        c = credencial_repo.get(db, credencial_id)
        if not c: return None
        c.activo = False
        c.motivo_revoc = motivo
        c.revocado_en = datetime.now(timezone.utc)
        db.commit(); db.refresh(c)
        return c

credencial_service = CredencialService()

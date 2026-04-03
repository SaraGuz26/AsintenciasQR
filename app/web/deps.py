from contextlib import contextmanager
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.services import docente_service
from app.db.session import SessionLocal
from app.models.usuario import Usuario
from app.models.docente import Docente
from app.security.auth import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:  # noqa
        db.rollback()
        raise
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_docente_service():
    return docente_service

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    try:
        payload = decode_token(token)
        email: Optional[str] = payload.get("sub")
        if not email:
            raise ValueError("Token sin 'sub'")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user = db.query(Usuario).filter(Usuario.email == email, Usuario.activo == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado o inactivo")
    return user

def get_current_docente(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db) ) -> Docente:

    """Solo permite acceso si el usuario logueado es docente y tiene registro en la tabla docente."""
    if user.rol != "DOCENTE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso solo para docentes")

    docente = db.query(Docente).filter(Docente.usuario_id == user.id).first()
    if not docente or not docente.activo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Docente no encontrado o inactivo")

    return docente

def require_role(*roles: str):
    def dep(user: Usuario = Depends(get_current_user)) -> Usuario:
        if user.rol not in roles:
            raise HTTPException(status_code=403, detail="Permisos insuficientes")
        return user
    return dep
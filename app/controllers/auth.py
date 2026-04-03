from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.web.deps import get_db, get_current_user
from app.models.usuario import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, UsuarioRead
from app.security.auth import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == body.email).first()
    if not user or not user.activo or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    token = create_access_token(subject=user.email, extra={"rol": user.rol})
    return TokenResponse(access_token=token, rol=user.rol)

@router.get("/me", response_model=UsuarioRead)
def me(user: Usuario = Depends(get_current_user)):
    return UsuarioRead(id=user.id, email=user.email, rol=user.rol, activo=user.activo)

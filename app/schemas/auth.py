from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    rol: str

class UsuarioRead(BaseModel):
    id: int
    email: EmailStr
    rol: str
    activo: bool
from pydantic import BaseModel, EmailStr
from typing import Optional

class DocenteBase(BaseModel):
    legajo: str
    apellido: str
    nombre: str
    email: Optional[EmailStr] = None
    depto: Optional[str] = None
    activo: bool = True

class DocenteCreate(DocenteBase):
    pass

class DocenteUpdate(BaseModel):
    apellido: Optional[str] = None
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    depto: Optional[str] = None
    activo: Optional[bool] = None

class DocenteOut(DocenteBase):
    id: int
    class Config:
        from_attributes = True

class DocenteQR(BaseModel):
    credencial_id: int
    nonce: str
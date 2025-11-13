from pydantic import BaseModel, EmailStr
from typing import Optional

class DocenteCreate(BaseModel):
    legajo: str
    apellido: str
    nombre: str
    email: EmailStr
    depto: Optional[str] = None
    activo: bool = True

class DocenteUpdate(BaseModel):
    apellido: Optional[str] = None
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    depto: Optional[str] = None
    activo: Optional[bool] = None

class DocenteOut(DocenteCreate):
    id: int
    class Config:
        from_attributes = True
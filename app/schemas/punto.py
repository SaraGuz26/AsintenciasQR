from pydantic import BaseModel
from typing import Optional

class PuntoBase(BaseModel):
    codigo: str
    etiqueta: str
    aula: Optional[str] = None
    activo: bool = True

class PuntoCreate(PuntoBase): pass

class PuntoUpdate(BaseModel):
    etiqueta: Optional[str] = None
    aula: Optional[str] = None
    activo: Optional[bool] = None

class PuntoOut(PuntoBase):
    id: int
    class Config: from_attributes = True

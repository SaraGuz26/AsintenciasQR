from pydantic import BaseModel

class MateriaBase(BaseModel):
    codigo: str
    nombre: str
    activo: bool = True

class MateriaCreate(MateriaBase): pass
class MateriaUpdate(BaseModel):
    nombre: str | None = None
    activo: bool | None = None

class MateriaOut(MateriaBase):
    id: int
    class Config: from_attributes = True

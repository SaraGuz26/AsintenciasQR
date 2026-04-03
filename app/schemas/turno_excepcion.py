from pydantic import BaseModel
from datetime import date, time

class TurnoExcepcionBase(BaseModel):
    turno_id: int
    fecha: date
    punto_id_alt: int | None = None
    hora_inicio_alt: time | None = None
    hora_fin_alt: time | None = None
    motivo: str | None = None
    activo: bool = True

class TurnoExcepcionCreate(TurnoExcepcionBase): pass

class TurnoExcepcionUpdate(BaseModel):
    punto_id_alt: int | None = None
    hora_inicio_alt: time | None = None
    hora_fin_alt: time | None = None
    motivo: str | None = None
    activo: bool | None = None

class TurnoExcepcionOut(TurnoExcepcionBase):
    id: int
    class Config: from_attributes = True

from pydantic import BaseModel, conint
from datetime import time
from app.models.turno import EstadoTurno


class TurnoBase(BaseModel):
    docente_id: int
    materia_id: int
    punto_id_plan: int              # <-- clave correcta
    dia_semana: int  # o 1..7 si así lo definiste en toda la app
    hora_inicio: time
    hora_fin: time
    tolerancia_min: int = 10
    activo: bool = True

class TurnoCreate(TurnoBase):
    pass

class TurnoUpdate(BaseModel):
    materia_id: int | None = None
    punto_id_plan: int | None = None
    dia_semana: int | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    tolerancia_min: int | None = None
    activo: bool | None = None

class TurnoOut(TurnoBase):
    id: int
    estado : EstadoTurno
    class Config:
        from_attributes = True

class TurnoOutFull(BaseModel):
    id: int
    dia_semana: int
    hora_inicio: time
    hora_fin: time
    tolerancia_min: int
    activo: bool

    materia_id: int
    materia_nombre: str

    punto_id_plan: int
    punto_nombre: str

    class Config:
        from_attributes = True


class TurnoOutEditable(BaseModel):
    id: int
    dia_semana: int
    hora_inicio: time
    hora_fin: time
    tolerancia_min: int
    activo: bool

    estado: str  # <-- solo acá lo agregamos

    materia_id: int
    materia_nombre: str

    punto_id_plan: int
    punto_nombre: str

    class Config:
        from_attributes = True

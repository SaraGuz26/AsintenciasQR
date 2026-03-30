from pydantic import BaseModel
from datetime import time, date
from app.models.turno_instancia import EstadoTurnoInstancia  # ✅ estado real

# Turno BASE (semanal fijo) - NO TIENE ESTADO
class TurnoBaseSchema(BaseModel):
    docente_id: int
    materia_id: int
    punto_id_plan: int
    dia_semana: int          # 1..7
    hora_inicio: time
    hora_fin: time
    tolerancia_min: int = 10
    activo: bool = True

class TurnoCreate(TurnoBaseSchema):
    pass

class TurnoUpdate(BaseModel):
    materia_id: int | None = None
    punto_id_plan: int | None = None
    dia_semana: int | None = None
    hora_inicio: time | None = None
    hora_fin: time | None = None
    tolerancia_min: int | None = None
    activo: bool | None = None

class TurnoOut(TurnoBaseSchema):
    id: int
    class Config:
        from_attributes = True


# Turno BASE + joins (para listar turnos del docente)

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


# Vista EDITABLE (base + estado de la instancia del día)
class TurnoOutEditable(BaseModel):
    id: int
    dia_semana: int
    hora_inicio: time
    hora_fin: time
    tolerancia_min: int
    activo: bool

    # estado real (proviene de TurnoInstancia o de cálculo)
    estado: EstadoTurnoInstancia

    materia_id: int
    materia_nombre: str

    punto_id_plan: int
    punto_nombre: str

    class Config:
        from_attributes = True

# Turno INSTANCIA (si querés exponer endpoints propios)
class TurnoInstanciaOut(BaseModel):
    id: int
    turno_base_id: int
    fecha: date
    estado: EstadoTurnoInstancia

    class Config:
        from_attributes = True

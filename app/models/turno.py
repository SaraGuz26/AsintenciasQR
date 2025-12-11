from sqlalchemy import Column, Integer, SmallInteger, Time, Boolean, ForeignKey
from sqlalchemy import Column, Integer, Boolean, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base
from enum import Enum

class EstadoTurno(str, Enum):
    PROGRAMADO = "PROGRAMADO"
    EN_CURSO = "EN_CURSO"
    FINALIZADO = "FINALIZADO"

class Turno(Base):
    __tablename__ = "turno"

    id = Column(Integer, primary_key=True, autoincrement=True)
    docente_id = Column(Integer, ForeignKey("docente.id"), nullable=False)
    materia_id = Column(Integer, ForeignKey("materia.id"), nullable=False)
    punto_id_plan = Column(Integer, ForeignKey("punto.id"), nullable=False)

    dia_semana = Column(SmallInteger, nullable=False)   # 1..7 (Lun..Dom)
    estado = Column(SAEnum(EstadoTurno), nullable=False, default=EstadoTurno.PROGRAMADO)
    hora_inicio = Column(Time, nullable=False)
    hora_fin = Column(Time, nullable=False)
    tolerancia_min = Column(SmallInteger, nullable=False, default=10)
    activo = Column(Boolean, nullable=False, default=True)

    docente = relationship("Docente", back_populates="turnos")
    materia = relationship("Materia", back_populates="turnos")
    punto_plan = relationship("Punto", back_populates="turnos_planificados")
    excepciones = relationship("TurnoExcepcion", back_populates="turno")
    asistencias = relationship("Asistencia", back_populates="turno")

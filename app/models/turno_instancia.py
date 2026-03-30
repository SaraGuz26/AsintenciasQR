from enum import Enum
from sqlalchemy import Column, Integer, Date, DateTime, Enum as SAEnum, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.models.base import Base

class EstadoTurnoInstancia(str, Enum):
    PROGRAMADO = "PROGRAMADO"
    EN_CURSO = "EN_CURSO"
    FINALIZADO = "FINALIZADO"

class TurnoInstancia(Base):
    __tablename__ = "turno_instancia"

    id = Column(Integer, primary_key=True)

    turno_base_id = Column(Integer, ForeignKey("turno_base.id"), nullable=False)
    fecha = Column(Date, nullable=False)

    estado = Column(
        SAEnum(EstadoTurnoInstancia),
        nullable=False,
        default=EstadoTurnoInstancia.PROGRAMADO
    )

    punto_id_real = Column(Integer, ForeignKey("punto.id"), nullable=False)

    inicio_real_utc = Column(DateTime)
    fin_real_utc = Column(DateTime)

    turno_base = relationship("TurnoBase", back_populates="instancias")
    punto_real = relationship("Punto")
    asistencias = relationship("Asistencia", back_populates="turno_instancia")
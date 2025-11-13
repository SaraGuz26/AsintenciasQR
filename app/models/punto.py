from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base

class Punto(Base):
    __tablename__ = "punto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(64), unique=True, nullable=False)
    etiqueta = Column(String(160), nullable=False)
    piso = Column(String(32))
    aula = Column(String(32))
    activo = Column(Boolean, nullable=False, default=True)

    turnos_planificados = relationship("Turno", back_populates="punto_plan")
    excepciones = relationship("TurnoExcepcion", back_populates="punto_alt")
    asistencias = relationship("Asistencia", back_populates="punto")
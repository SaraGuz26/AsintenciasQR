from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base

class Docente(Base):
    __tablename__ = "docente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    legajo = Column(String(32), unique=True)
    nombre = Column(String(120), nullable=False)
    apellido = Column(String(120), nullable=False)
    email = Column(String(160))
    depto = Column(String(120))
    activo = Column(Boolean, nullable=False, default=True)

    turnos = relationship("Turno", back_populates="docente")
    credenciales = relationship("Credencial", back_populates="docente")
    asistencias = relationship("Asistencia", back_populates="docente")

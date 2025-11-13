from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base

class Materia(Base):
    __tablename__ = "materia"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(32), unique=True)
    nombre = Column(String(160), nullable=False)
    activo = Column(Boolean, nullable=False, default=True)

    turnos = relationship("Turno", back_populates="materia")

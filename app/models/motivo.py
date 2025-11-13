from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base

class Motivo(Base):
    __tablename__ = "motivo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(32), unique=True)
    descripcion = Column(String(160), nullable=False)

    asistencias = relationship("Asistencia", back_populates="motivo")

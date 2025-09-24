from sqlalchemy import Column, Integer, Boolean, ForeignKey, String
from sqlalchemy.orm import relationship
from models.base import Base

class Turno(Base):
    __tablename__ = "turno"

    id = Column(Integer, primary_key=True)
    docente_id = Column(Integer, ForeignKey("docente.id"))
    materia_id = Column(Integer, ForeignKey("materia.id"))
    puesto_id = Column(Integer, ForeignKey("puesto.id"))
    planifica_en = Column(String)
    activo = Column(Boolean, default=True)

    docente = relationship("Docente")
    materia = relationship("Materia")
    puesto = relationship("Puesto")

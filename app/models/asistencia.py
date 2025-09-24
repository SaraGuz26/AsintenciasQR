from sqlalchemy import Column, Integer, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

class Asistencia(Base):
    __tablename__ = "asistencia"

    id = Column(Integer, primary_key=True)
    turno_id = Column(Integer, ForeignKey("turno.id"))
    fecha = Column(Date)
    credencial_id = Column(Integer, ForeignKey("credencial.id"))
    es_valida = Column(Boolean, default=True)

    turno = relationship("Turno")
    credencial = relationship("Credencial")

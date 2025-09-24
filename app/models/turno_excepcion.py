from sqlalchemy import Column, Integer, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

class TurnoExcepcion(Base):
    __tablename__ = "turno_excepcion"

    id = Column(Integer, primary_key=True)
    turno_id = Column(Integer, ForeignKey("turno.id"))
    fecha = Column(Date)
    motivo_id = Column(Integer, ForeignKey("motivo.id"))
    activo = Column(Boolean, default=True)

    turno = relationship("Turno")
    motivo = relationship("Motivo")

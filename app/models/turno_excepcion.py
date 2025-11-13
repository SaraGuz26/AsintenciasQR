from sqlalchemy import Column, Integer, Date, Time, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class TurnoExcepcion(Base):
    __tablename__ = "turno_excepcion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    turno_id = Column(Integer, ForeignKey("turno.id"), nullable=False)
    fecha = Column(Date, nullable=False)

    punto_id_alt = Column(Integer, ForeignKey("punto.id"))  # opcional (reubicación)
    hora_inicio_alt = Column(Time)                          # opcional (cambio horario)
    hora_fin_alt = Column(Time)
    motivo = Column(String(255))

    turno = relationship("Turno", back_populates="excepciones")
    punto_alt = relationship("Punto", back_populates="excepciones")

from enum import Enum
from sqlalchemy import Column, Integer, BigInteger, DateTime, String, Boolean, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class EstadoAsistencia(str, Enum):
    EN_CONSULTA = "EN_CONSULTA"
    TARDE = "TARDE"
    REUBICADO = "REUBICADO"
    FUERA_DE_HORARIO = "FUERA_DE_HORARIO"

class FuenteLectura(str, Enum):
    LECTOR = "LECTOR"
    CAMARA = "CAMARA"
    PEGA = "PEGA"

class Asistencia(Base):
    __tablename__ = "asistencia"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    docente_id = Column(Integer, ForeignKey("docente.id"), nullable=False)
    punto_id = Column(Integer, ForeignKey("punto.id"), nullable=False)
    turno_id = Column(Integer, ForeignKey("turno.id"))  # puede ser NULL si fuera de horario
    credencial_id = Column(Integer, ForeignKey("credencial.id"))

    ts_lectura_utc = Column(DateTime, nullable=False)
    estado = Column(SAEnum(EstadoAsistencia), nullable=False)
    motivo_id = Column(Integer, ForeignKey("motivo.id"))
    motivo_texto = Column(String(255))

    fuente = Column(SAEnum(FuenteLectura), nullable=False)
    qr_nonce = Column(String(16), nullable=False)
    valido = Column(Boolean, nullable=False, default=True)
    detalle_error = Column(String(255))

    docente = relationship("Docente", back_populates="asistencias")
    punto = relationship("Punto", back_populates="asistencias")
    turno = relationship("Turno", back_populates="asistencias")
    motivo = relationship("Motivo", back_populates="asistencias")
    credencial = relationship("Credencial", back_populates="asistencias")

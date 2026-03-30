from enum import Enum
from sqlalchemy import Column, Integer, BigInteger, DateTime, String, Boolean, Enum as SAEnum, ForeignKey, UniqueConstraint, Index, Date
from sqlalchemy.orm import relationship
from app.models.base import Base
from sqlalchemy import SmallInteger

class EstadoAsistencia(str, Enum):
    PRESENTE = "PRESENTE"
    TARDE = "TARDE"
    AUSENTE = "AUSENTE"  # solo automático si nadie asistió

class FuenteLectura(str, Enum):
    LECTOR = "LECTOR"
    CAMARA = "CAMARA"
    PEGA = "PEGA"

class Asistencia(Base):
    __tablename__ = "asistencia"
    __table_args__ = (
        # Evita duplicados del tipo "ausente automático" (solo uno por instancia)
        UniqueConstraint("turno_instancia_id"),
        Index("ix_asistencia_ts", "ts_lectura_utc"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    docente_id = Column(Integer, ForeignKey("docente.id"), nullable=False)
    punto_id = Column(Integer, ForeignKey("punto.id"), nullable=False)

    turno_instancia_id = Column(Integer, ForeignKey("turno_instancia.id"), nullable=True)
    credencial_id = Column(Integer, ForeignKey("credencial.id"), nullable=True)

    ts_lectura_utc = Column(DateTime, nullable=False)  # guardar UTC
    estado = Column(SAEnum(EstadoAsistencia), nullable=False)

    motivo_texto = Column(String(255))
    fuente = Column(SAEnum(FuenteLectura), nullable=False)

    qr_nonce = Column(String(16), nullable=False, default="-")
    valido = Column(SmallInteger, nullable=False, default=1)
    detalle_error = Column(String(255))

    docente = relationship("Docente", back_populates="asistencias")
    punto = relationship("Punto", back_populates="asistencias")
    turno_instancia = relationship("TurnoInstancia", back_populates="asistencias")
    credencial = relationship("Credencial", back_populates="asistencias")

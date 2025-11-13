from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class Credencial(Base):
    __tablename__ = "credencial"

    id = Column(Integer, primary_key=True, autoincrement=True)
    docente_id = Column(Integer, ForeignKey("docente.id"), nullable=False)
    nonce_actual = Column(String(16), nullable=False)
    emitido_en = Column(DateTime, nullable=False)
    revocado = Column(Boolean, nullable=False, default=False)
    revocado_en = Column(DateTime)
    motivo_revoc = Column(String(255))

    docente = relationship("Docente", back_populates="credenciales")
    asistencias = relationship("Asistencia", back_populates="credencial")

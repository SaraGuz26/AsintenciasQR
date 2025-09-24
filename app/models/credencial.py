from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

class Credencial(Base):
    __tablename__ = "credencial"

    id = Column(Integer, primary_key=True)
    docente_id = Column(Integer, ForeignKey("docente.id"))
    password_hash = Column(String)
    activo = Column(Boolean, default=True)

    docente = relationship("Docente")

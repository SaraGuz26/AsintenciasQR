from sqlalchemy import Column, Integer, String, Boolean
from models.base import Base

class Docente(Base):
    __tablename__ = "docente"

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    activo = Column(Boolean, default=True)

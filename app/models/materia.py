from sqlalchemy import Column, Integer, String, Boolean
from models.base import Base

class Materia(Base):
    __tablename__ = "materia"

    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    activo = Column(Boolean, default=True)

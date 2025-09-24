from sqlalchemy import Column, Integer, String, Boolean
from models.base import Base

class Puesto(Base):
    __tablename__ = "puesto"

    id = Column(Integer, primary_key=True)
    codigo = Column(String, nullable=False)
    planifica_en = Column(String)  # ¿Es una ubicación? Podés ajustar el tipo
    activo = Column(Boolean, default=True)

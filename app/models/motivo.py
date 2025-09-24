from sqlalchemy import Column, Integer, String
from models.base import Base

class Motivo(Base):
    __tablename__ = "motivo"

    id = Column(Integer, primary_key=True)
    descripcion = Column(String, nullable=False)

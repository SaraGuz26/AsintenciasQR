from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, Enum as SAEnum
from app.models.base import Base

class Rol(str, Enum):
    consulta = "consulta"  # solo visualización (Bedelía)

class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(SAEnum(Rol), nullable=False, default=Rol.consulta)
    activo = Column(Boolean, nullable=False, default=True)
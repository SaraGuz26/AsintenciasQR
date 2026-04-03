from app.repositories.base import Base
from app.models.punto import Punto

class PuntoRepository(Base[Punto, object, object]):
    pass

punto_repo = PuntoRepository(Punto)

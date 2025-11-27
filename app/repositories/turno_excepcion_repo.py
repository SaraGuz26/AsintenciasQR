from app.repositories.base import Base
from app.models.turno_excepcion import TurnoExcepcion

class TurnoExcepcionRepository(Base[TurnoExcepcion, object, object]): pass
turno_exc_repo = TurnoExcepcionRepository(TurnoExcepcion)

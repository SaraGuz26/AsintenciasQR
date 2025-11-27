from app.repositories.base import Base
from app.models.asistencia import Asistencia

class AsistenciaRepository(Base[Asistencia, object, object]): pass
asistencia_repo = AsistenciaRepository(Asistencia)

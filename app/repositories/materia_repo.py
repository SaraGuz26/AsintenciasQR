from app.repositories.base import Base
from app.models.materia import Materia

class MateriaRepository(Base[Materia, object, object]): pass
materia_repo = MateriaRepository(Materia)

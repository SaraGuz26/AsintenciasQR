from app.db.session import engine
from app.models.base import Base
from app.models import docente, materia, punto, motivo, turno_base, turno_excepcion, credencial, asistencia, turno_instancia

Base.metadata.create_all(bind=engine)
print("Tablas creadas exitosamente.")
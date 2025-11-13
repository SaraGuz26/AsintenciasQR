from app.db.session import engine
from app.models.base import Base
from app.models import docente, materia, punto, turno, motivo, turno_excepcion, credencial, asistencia

Base.metadata.create_all(bind=engine)
print("Tablas creadas exitosamente.")
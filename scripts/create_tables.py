from db.session import engine
from models.base import Base
from models import docente, materia, puesto, turno, motivo, turno_excepcion, credencial, asistencia

Base.metadata.create_all(bind=engine)
print("Tablas creadas exitosamente.")
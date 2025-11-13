from sqlalchemy.orm import declarative_base
Base = declarative_base()

# IMPORTANTE: estos imports traen los modelos a memoria,
# así SQLAlchemy conoce TODAS las clases antes de mapear.
from app.models import (
    docente, credencial, materia, punto, turno, turno_excepcion,
    asistencia, motivo, usuario
) 
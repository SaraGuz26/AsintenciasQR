from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date, datetime
from app.repositories.base import Base
from app.models.turno import Turno
from app.models.turno_excepcion import TurnoExcepcion

class TurnoRepository(Base[Turno, object, object]):
    def vigente_para(self, db: Session, docente_id: int, fecha_hora: datetime):
        dow = fecha_hora.weekday() + 1  # 1=lunes ... 7=domingo
        stmt = select(Turno).where(
            Turno.docente_id == docente_id,
            Turno.dia_semana == dow,
            Turno.activo == True
        )
        turno = db.scalars(stmt).first()
        if not turno:
            return None

        ex = db.scalars(
            select(TurnoExcepcion).where(
                TurnoExcepcion.turno_id == turno.id,
                TurnoExcepcion.fecha == date(fecha_hora.year, fecha_hora.month, fecha_hora.day),
                #TurnoExcepcion.activo == True
            )
        ).first()

        return (turno, ex)

turno_repo = TurnoRepository(Turno)

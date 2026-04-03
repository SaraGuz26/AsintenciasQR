from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date, datetime, time
from app.models.turno import Turno
from app.models.turno_excepcion import TurnoExcepcion
from app.repositories.base import Base

class TurnoRepository(Base[Turno, object, object]):

    def vigente_para(self, db: Session, docente_id: int, fecha_hora: datetime):
        dow = fecha_hora.weekday() + 1  # lunes = 1 ... domingo = 7
        ahora_min = fecha_hora.hour * 60 + fecha_hora.minute

        # 1) Traer todos los turnos del docente para este día
        turnos = db.scalars(
            select(Turno).where(
                Turno.docente_id == docente_id,
                Turno.dia_semana == dow,
                Turno.activo == True
            )
        ).all()

        if not turnos:
            return None

        for turno in turnos:

            # 2) Buscar excepciones del turno
            exc = db.scalars(
                select(TurnoExcepcion).where(
                    TurnoExcepcion.turno_id == turno.id,
                    TurnoExcepcion.fecha == fecha_hora.date(),
                )
            ).first()

            # Horarios reales (con o sin excepción)
            ini = exc.hora_inicio_alt if exc and exc.hora_inicio_alt else turno.hora_inicio
            fin = exc.hora_fin_alt if exc and exc.hora_fin_alt else turno.hora_fin
            tol = turno.tolerancia_min or 0

            min_ini = ini.hour * 60 + ini.minute
            min_fin = fin.hour * 60 + fin.minute

            # 3) ¿Está vigente ahora?
            if min_ini - tol <= ahora_min <= min_fin:
                return turno, exc

        # Si ninguno coincide con la hora actual → no hay turno vigente
        return None


turno_repo = TurnoRepository(Turno)

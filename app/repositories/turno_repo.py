from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime
from app.models.turno_base import TurnoBase
from app.models.turno_excepcion import TurnoExcepcion

class TurnoRepository:

    def vigente_para(self, db: Session, docente_id: int, fecha_hora: datetime):
        dow = fecha_hora.weekday() + 1  # lunes=1 ... domingo=7
        ahora_min = fecha_hora.hour * 60 + fecha_hora.minute
        fecha = fecha_hora.date()

        # 1) turnos semanales del docente para ese día
        turnos = db.scalars(
            select(TurnoBase).where(
                TurnoBase.docente_id == docente_id,
                TurnoBase.dia_semana == dow,
                TurnoBase.activo == True
            )
        ).all()

        if not turnos:
            return None

        for tb in turnos:
            # 2) excepción de ese día (si existe)
            exc = db.scalars(
                select(TurnoExcepcion).where(
                    TurnoExcepcion.turno_base_id == tb.id,
                    TurnoExcepcion.fecha == fecha
                )
            ).first()

            ini = exc.hora_inicio_alt if exc and exc.hora_inicio_alt else tb.hora_inicio
            fin = exc.hora_fin_alt if exc and exc.hora_fin_alt else tb.hora_fin
            tol = tb.tolerancia_min or 0

            min_ini = ini.hour * 60 + ini.minute
            min_fin = fin.hour * 60 + fin.minute

            # 3) vigente ahora (con tolerancia hacia atrás)
            if (min_ini - tol) <= ahora_min <= min_fin:
                return tb, exc

        return None

turno_repo = TurnoRepository()

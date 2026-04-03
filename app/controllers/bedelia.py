from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import date, datetime, time, timedelta
from app.web.deps import get_db
from app.models.asistencia import Asistencia
from app.models.docente import Docente
from app.models.turno import Turno
from app.models.punto import Punto
from app.models.materia import Materia
import pytz
ARG_TZ = pytz.timezone("America/Argentina/Buenos_Aires")

router = APIRouter(prefix="/bedelia", tags=["bedelia"])

@router.get("/estado-diario")
def estado_diario(
    fecha: date = Query(...),
    db: Session = Depends(get_db)
):
    q = (db.query(Asistencia, Docente, Turno, Punto)
           .join(Docente, Docente.id==Asistencia.docente_id)
           .join(Turno, Turno.id==Asistencia.turno_id)
           .join(Punto, Punto.id==Asistencia.punto_id)
           .filter(func.date(Asistencia.created_at)==fecha))  # asumiendo created_at en Asistencia

    return [{
        "docente": f"{d.apellido}, {d.nombre}",
        "materia_id": t.materia_id,
        "punto": p.etiqueta,
        "estado": a.estado,
        "motivo": a.motivo,
        "valido": a.valido
    } for a, d, t, p in q.all()]


@router.get("/asistencias/hoy")
def asistencias_hoy(db: Session = Depends(get_db)):
    """Devuelve las asistencias del día actual para el panel de Bedelía."""

    hoy = datetime.utcnow().date()
    inicio = datetime.combine(hoy, time(0, 0, 0))
    fin = datetime.combine(hoy, time(23, 59, 59))

    asistencias = (
        db.query(Asistencia)
        .join(Docente, Asistencia.docente_id == Docente.id)
        .join(Turno, Asistencia.turno_id == Turno.id, isouter=True)
        .join(Punto, Asistencia.punto_id == Punto.id)
        .join(Materia, Turno.materia_id == Materia.id, isouter=True)
        .filter(Asistencia.ts_lectura_utc.between(inicio, fin))
        .order_by(Asistencia.ts_lectura_utc.desc())
        .all()
    )

    resultado = []
    for a in asistencias:
        resultado.append(
            {
                "id": a.id,
                "docente": f"{a.docente.nombre} {a.docente.apellido}",
                "materia": a.turno.materia.nombre if a.turno and a.turno.materia else None,
                "punto": a.punto.nombre if a.punto else None,
                "estado": a.estado.value if hasattr(a.estado, "value") else str(a.estado),
                "motivo": a.motivo_texto,
                "hora": a.ts_lectura_utc.isoformat(),
            }
        )

    return resultado


@router.get("/asistencias/calendario")
def asistencias_calendario(db: Session = Depends(get_db)):

    hoy = date.today()
    dow_hoy = hoy.isoweekday()  # 1=lunes

    # --- TURNOS DE HOY ---
    turnos_hoy = (
        db.query(Turno)
        .filter(Turno.activo == True, Turno.dia_semana == dow_hoy)
        .all()
    )

    # --- TURNOS PASADOS (otros días < hoy) ---
    turnos_pasados = (
        db.query(Turno)
        .filter(Turno.activo == True, Turno.dia_semana < dow_hoy)
        .all()
    )

    # --- TURNOS FUTUROS (otros días > hoy) ---
    turnos_futuros = (
        db.query(Turno)
        .filter(Turno.activo == True, Turno.dia_semana > dow_hoy)
        .all()
    )

    def estado_turno(t: Turno):
        """Busca asistencia del día correspondiente y devuelve estado real."""
        asist = (
            db.query(Asistencia)
            .filter(
                Asistencia.turno_id == t.id,
                func.date(Asistencia.ts_lectura_utc) == hoy
            )
            .order_by(Asistencia.ts_lectura_utc.desc())
            .first()
        )

        if asist:
            return asist.estado.value, asist.motivo_texto or "-", asist.ts_lectura_utc.strftime("%H:%M")
        else:
            return "PROGRAMADO", "-", f"{t.hora_inicio.strftime('%H:%M')} - {t.hora_fin.strftime('%H:%M')}"

    def turno_to_dict(t: Turno):
        estado, motivo, hora = estado_turno(t)
        return {
            "id": t.id,
            "docente": f"{t.docente.nombre} {t.docente.apellido}",
            "materia": t.materia.nombre if t.materia else "-",
            "punto": t.punto_plan.etiqueta if t.punto_plan else "-",
            "estado": estado,
            "motivo": motivo,
            "hora": hora,
            "fecha": hoy.strftime("%Y-%m-%d"),
        }

    return {
        "hoy": [turno_to_dict(t) for t in turnos_hoy],
        "pasadas": [turno_to_dict(t) for t in turnos_pasados],
        "futuras": [turno_to_dict(t) for t in turnos_futuros],
    }

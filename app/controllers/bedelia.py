from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, time, timedelta
import pytz
from app.web.deps import get_db
from app.models.asistencia import Asistencia
from app.models.docente import Docente
from app.models.turno_base import TurnoBase
from app.models.turno_instancia import TurnoInstancia
from app.models.punto import Punto
from app.models.materia import Materia

ARG_TZ = pytz.timezone("America/Argentina/Buenos_Aires")

router = APIRouter(prefix="/bedelia", tags=["bedelia"])

def obtener_dia_es(fecha):
    try:
        return {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
            "Saturday": "Sábado",
            "Sunday": "Domingo",
        }[fecha.strftime("%A")]
    except KeyError:
        return ""

def obtener_turnos_futuros(db: Session, hoy_ar):

    futuras = []

    for i in range(1, 8):  # próximos 7 días
        fecha = hoy_ar + timedelta(days=i)
        dia = fecha.isoweekday()

        turnos = (
            db.query(TurnoBase, Docente, Punto, Materia)
            .join(Docente, Docente.id == TurnoBase.docente_id)
            .join(Punto, Punto.id == TurnoBase.punto_id_plan)
            .join(Materia, Materia.id == TurnoBase.materia_id)
            .filter(
                TurnoBase.dia_semana == dia,
                TurnoBase.activo == True
            )
            .all()
        )

        for tb, d, p, m in turnos:
            futuras.append({
                "id": None,
                "fecha": fecha.strftime("%Y-%m-%d"),
                "docente": f"{d.nombre} {d.apellido}",
                "materia": m.nombre if m else "-",
                "punto": p.etiqueta if hasattr(p, "etiqueta") else getattr(p, "nombre", "-"),
                "hora_inicio": tb.hora_inicio.strftime("%H:%M"),
                "hora_fin": tb.hora_fin.strftime("%H:%M"),
                "estado": "PROGRAMADO",
                "motivo": "-",
                "hora": "-",
                "dia_semana": obtener_dia_es(fecha)
            })

    return futuras

def obtener_turnos_pasados(db: Session, hoy_ar):

    from datetime import timedelta

    pasadas = []

    for i in range(1, 8):  # últimos 7 días
        fecha = hoy_ar - timedelta(days=i)
        dia = fecha.isoweekday()

        turnos = (
            db.query(TurnoBase, Docente, Punto, Materia)
            .join(Docente, Docente.id == TurnoBase.docente_id)
            .join(Punto, Punto.id == TurnoBase.punto_id_plan)
            .join(Materia, Materia.id == TurnoBase.materia_id)
            .filter(
                TurnoBase.dia_semana == dia,
                TurnoBase.activo == True
            )
            .all()
        )

        for tb, d, p, m in turnos:
            pasadas.append({
                "id": None,
                "fecha": fecha.strftime("%Y-%m-%d"),
                "docente": f"{d.nombre} {d.apellido}",
                "materia": m.nombre if m else "-",
                "punto": p.etiqueta if hasattr(p, "etiqueta") else getattr(p, "nombre", "-"),
                "hora_inicio": tb.hora_inicio.strftime("%H:%M"),
                "hora_fin": tb.hora_fin.strftime("%H:%M"),
                "estado": "FINALIZADO (AUSENTE)",  # por defecto
                "motivo": "-",
                "hora": "-"
            })

    return pasadas

@router.get("/asistencias/calendario")
def asistencias_calendario(db: Session = Depends(get_db)):

    hoy_ar = datetime.now(ARG_TZ).date()

    def obtener_instancias(filtro_fecha):
        return (
            db.query(TurnoInstancia, TurnoBase, Docente, Punto, Materia)
            .join(TurnoBase, TurnoBase.id == TurnoInstancia.turno_base_id)
            .join(Docente, Docente.id == TurnoBase.docente_id)
            .join(Punto, Punto.id == TurnoInstancia.punto_id_real)   
            .join(Materia, Materia.id == TurnoBase.materia_id)
            .filter(filtro_fecha)
            .order_by(TurnoInstancia.fecha.desc(), TurnoBase.hora_inicio.asc())
            .all()
        )

    inst_pasadas = obtener_instancias(TurnoInstancia.fecha < hoy_ar)
    inst_hoy = obtener_instancias(TurnoInstancia.fecha == hoy_ar)
    inst_futuras = obtener_turnos_futuros(db, hoy_ar)

    def to_ar_hhmm(ts_utc: datetime | None) -> str:
        if not ts_utc:
            return "-"
        if ts_utc.tzinfo is None:
            ts_utc = pytz.UTC.localize(ts_utc)
        return ts_utc.astimezone(ARG_TZ).strftime("%H:%M")

    def estado_instancia(ti: TurnoInstancia):
        """Última asistencia para esa instancia."""
        asist = (
            db.query(Asistencia)
            .filter(Asistencia.turno_instancia_id == ti.id)
            .order_by(Asistencia.ts_lectura_utc.desc())
            .first()
        )

        if asist:
            return (
                asist.estado.value,
                asist.motivo_texto or "-",
                to_ar_hhmm(asist.ts_lectura_utc),
            )

        # si no hay asistencias, el estado lo define la instancia
        return (
            ti.estado.value if hasattr(ti.estado, "value") else str(ti.estado),
            "-",
            "-",
        )

    def hora_inicio_mostrar(tb: TurnoBase) -> str:
        return tb.hora_inicio.strftime("%H:%M")

    def hora_fin_mostrar(tb: TurnoBase) -> str:
        return tb.hora_fin.strftime("%H:%M")

    def instancia_to_dict(ti: TurnoInstancia, tb: TurnoBase, d: Docente, p: Punto, m: Materia):
        estado, motivo, hora_scan = estado_instancia(ti)

        return {
            "id": ti.id,
            "fecha": ti.fecha.strftime("%Y-%m-%d"),
            "dia_semana": obtener_dia_es(ti.fecha),

            "docente": f"{d.nombre} {d.apellido}",
            "materia": m.nombre if m else "-",

            # punto real del día (si se reubicó, esto cambia)
            "punto": p.etiqueta if hasattr(p, "etiqueta") else getattr(p, "nombre", "-"),

            # planificado con fallback, o real si existe
            "hora_inicio": hora_inicio_mostrar(tb),
            "hora_fin": hora_fin_mostrar(tb),

            "estado": estado,
            "motivo": motivo,
            "hora": hora_scan,  # hora del último scan (AR) si existe
        }

    return {
        "hoy": [instancia_to_dict(ti, tb, d, p, m) for (ti, tb, d, p, m) in inst_hoy],
        "pasadas": [
            instancia_to_dict(ti, tb, d, p, m)
            for (ti, tb, d, p, m) in inst_pasadas
        ],
        "futuras": inst_futuras
        ,
    }

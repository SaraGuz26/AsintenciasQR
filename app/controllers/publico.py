from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.models.docente import Docente
from app.models.materia import Materia
from app.models.punto import Punto
from app.models.turno_base import TurnoBase
from app.models.turno_instancia import TurnoInstancia
from app.models.asistencia import Asistencia
from datetime import datetime
import pytz

router = APIRouter(prefix="/publico", tags=["público"])
ARG_TZ = pytz.timezone("America/Argentina/Buenos_Aires")


@router.get("/profesores")
def listado(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Docente.id.label("docente_id"),
            Docente.apellido, Docente.nombre,
            Materia.nombre.label("materia"),
            Punto.etiqueta.label("aula"),
            TurnoBase.dia_semana,
            TurnoBase.hora_inicio,
            TurnoBase.hora_fin,
        )
        .join(TurnoBase, TurnoBase.docente_id == Docente.id)
        .join(Materia, Materia.id == TurnoBase.materia_id)
        .join(Punto, Punto.id == TurnoBase.punto_id_plan)
        .filter(
            Docente.activo == True,
            TurnoBase.activo == True,
            Materia.activo == True,
            Punto.activo == True,
        )
        .all()
    )

    return [
        {
            "docente_id": r.docente_id,
            "docente": f"{r.apellido}, {r.nombre}",
            "materia": r.materia,
            "aula": r.aula,
            "dia_semana": r.dia_semana,
            "hora_inicio": r.hora_inicio.strftime("%H:%M"),
            "hora_fin": r.hora_fin.strftime("%H:%M"),
        }
        for r in rows
    ]


@router.get("/consultas")
def consultas_publicas(dia: str = "hoy", db: Session = Depends(get_db)):

    ahora_ar = datetime.now(ARG_TZ)

    if dia == "hoy":
        dia_sem = ahora_ar.isoweekday()
    else:
        dia_sem = int(dia)

    # mostramos SOLO turnos base del día
    turnos = (
        db.query(TurnoBase, Docente, Materia, Punto)
        .join(Docente, Docente.id == TurnoBase.docente_id)
        .join(Materia, Materia.id == TurnoBase.materia_id)
        .join(Punto, Punto.id == TurnoBase.punto_id_plan)
        .filter(TurnoBase.activo == True)
        .filter(TurnoBase.dia_semana == dia_sem)
        .all()
    )

    resultado = []
    for tb, d, m, p_plan in turnos:

        # buscar instancia de HOY (Argentina)
        instancia = (
            db.query(TurnoInstancia)
            .filter(
                TurnoInstancia.turno_base_id == tb.id,
                TurnoInstancia.fecha == ahora_ar.date()
            )
            .first()
        )

        # estado + hora_registro desde la última asistencia de esa instancia
        estado = "PROGRAMADO"
        hora_registro = "-"

        if instancia:
            ultima = (
                db.query(Asistencia)
                .filter(Asistencia.turno_instancia_id == instancia.id)
                .order_by(Asistencia.ts_lectura_utc.desc())
                .first()
            )

            if ultima:
                ts = ultima.ts_lectura_utc
                if ts.tzinfo is None:
                    ts = pytz.UTC.localize(ts)
                hora_registro = ts.astimezone(ARG_TZ).strftime("%H:%M")
                estado = ultima.estado.value
            else:
                # sin asistencias: usar estado de la instancia
                estado = instancia.estado.value

        resultado.append({
            "docente": f"{d.nombre} {d.apellido}",
            "materia": m.nombre,
            "punto": (p_plan.etiqueta if hasattr(p_plan, "etiqueta") else getattr(p_plan, "nombre", "-")),
            "hora_inicio": tb.hora_inicio.strftime("%H:%M"),
            "hora_fin": tb.hora_fin.strftime("%H:%M"),
            "estado": estado,
            "hora_registro": hora_registro
        })

    return resultado

@router.get("/consultas/semana")
def consultas_semana(db: Session = Depends(get_db)):

    ahora_ar = datetime.now(ARG_TZ)

    turnos = (
        db.query(TurnoBase, Docente, Materia, Punto)
        .join(Docente, Docente.id == TurnoBase.docente_id)
        .join(Materia, Materia.id == TurnoBase.materia_id)
        .join(Punto, Punto.id == TurnoBase.punto_id_plan)
        .filter(TurnoBase.activo == True)
        .all()
    )

    resultado = []
    for tb, d, m, p_plan in turnos:

        instancia = (
            db.query(TurnoInstancia)
            .filter(
                TurnoInstancia.turno_base_id == tb.id,
                TurnoInstancia.fecha == ahora_ar.date()
            )
            .first()
        )

        estado = "PROGRAMADO"
        hora_registro = "-"

        if instancia:
            ultima = (
                db.query(Asistencia)
                .filter(Asistencia.turno_instancia_id == instancia.id)
                .order_by(Asistencia.ts_lectura_utc.desc())
                .first()
            )

            if ultima:
                ts = ultima.ts_lectura_utc
                if ts.tzinfo is None:
                    ts = pytz.UTC.localize(ts)
                hora_registro = ts.astimezone(ARG_TZ).strftime("%H:%M")
                estado = ultima.estado.value
            else:
                estado = instancia.estado.value

        resultado.append({
            "docente": f"{d.nombre} {d.apellido}",
            "materia": m.nombre,
            "punto": getattr(p_plan, "etiqueta", getattr(p_plan, "nombre", "-")),
            "hora_inicio": tb.hora_inicio.strftime("%H:%M"),
            "hora_fin": tb.hora_fin.strftime("%H:%M"),
            "estado": estado,
            "hora_registro": hora_registro,
            "dia_semana": tb.dia_semana  # 👈 CLAVE
        })

    return resultado
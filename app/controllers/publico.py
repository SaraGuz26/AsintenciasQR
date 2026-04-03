from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.models.docente import Docente
from app.models.materia import Materia
from app.models.punto import Punto
from app.models.turno import Turno
from app.models.asistencia import Asistencia
from datetime import datetime
import pytz  # si usás tz


router = APIRouter(prefix="/publico", tags=["público"])

@router.get("/profesores")
def listado(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Docente.id.label("docente_id"),
            Docente.apellido, Docente.nombre,
            Materia.nombre.label("materia"),
            Punto.etiqueta.label("aula"),
            Turno.dia_semana, Turno.hora_inicio, Turno.hora_fin
        )
        .join(Turno, Turno.docente_id == Docente.id)
        .join(Materia, Materia.id == Turno.materia_id)
        .join(Punto, Punto.id == Turno.punto_id_plan)   # <-- aquí
        .filter(
            Docente.activo == True,
            Turno.activo == True,
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

    ARG = pytz.timezone("America/Argentina/Buenos_Aires")
    ahora_ar = datetime.now(ARG)

    if dia == "hoy":
        dia_sem = ahora_ar.isoweekday()
    else:
        dia_sem = int(dia)

    turnos = (
        db.query(Turno, Docente, Materia, Punto)
        .join(Docente, Docente.id == Turno.docente_id)
        .join(Materia, Materia.id == Turno.materia_id)
        .join(Punto, Punto.id == Turno.punto_id_plan)
        .filter(Turno.dia_semana == dia_sem)
        .all()
    )

    resultado = []

    for t, d, m, p in turnos:

        asistencia = (
            db.query(Asistencia)
            .filter(Asistencia.turno_id == t.id)
            .order_by(Asistencia.ts_lectura_utc.desc())
            .first()
        )

        # ============================
        # 🔥 Convertir hora a Argentina
        # ============================
        if asistencia:
            ts = asistencia.ts_lectura_utc

            # si viene sin tzinfo, asumimos que es UTC
            if ts.tzinfo is None:
                ts = pytz.UTC.localize(ts)

            hora_local = ts.astimezone(ARG).strftime("%H:%M")
            estado = asistencia.estado.value
        else:
            hora_local = "-"
            # fallback estado
            ahora_min = ahora_ar.hour * 60 + ahora_ar.minute
            ini = t.hora_inicio.hour * 60 + t.hora_inicio.minute
            fin = t.hora_fin.hour * 60 + t.hora_fin.minute + (t.tolerancia_min or 0)

            if ahora_min < ini:
                estado = "PROGRAMADO"
            elif ahora_min > fin:
                estado = "FINALIZADO"
            else:
                estado = "SIN_ASISTENCIA"

        resultado.append({
            "docente": f"{d.nombre} {d.apellido}",
            "materia": m.nombre,
            "punto": p.etiqueta,
            "hora_inicio": t.hora_inicio.strftime("%H:%M"),
            "hora_fin": t.hora_fin.strftime("%H:%M"),
            "estado": estado,
            "hora_registro": hora_local
        })

    return resultado

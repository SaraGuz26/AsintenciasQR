from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import pytz
from datetime import timedelta
from app.web.deps import get_db
from app.services.turno_service import turno_service
from app.schemas.turno import (
    TurnoCreate,
    TurnoUpdate,
    TurnoOut,
    TurnoOutFull,
    TurnoOutEditable
)
from app.models.turno_base import TurnoBase
from app.models.turno_instancia import TurnoInstancia, EstadoTurnoInstancia
from app.models.materia import Materia
from app.models.punto import Punto
from app.models.asistencia import Asistencia
from datetime import datetime, time
from app.models.docente import Docente

router = APIRouter(prefix="/turnos", tags=["turnos"])
ARG_TZ = pytz.timezone("America/Argentina/Buenos_Aires")

@router.get("", response_model=list[TurnoOut])
def listar(db: Session = Depends(get_db)):
    return turno_service.list(db)

@router.post("", response_model=TurnoOut)
def crear(data: TurnoCreate, db: Session = Depends(get_db)):
    return turno_service.create(db, data)


@router.put("/{turno_id}", response_model=TurnoOut)
def actualizar(turno_id: int, data: TurnoUpdate, db: Session = Depends(get_db)):

    turno = db.query(TurnoBase).filter(TurnoBase.id == turno_id).first()
    if not turno:
        raise HTTPException(404, "El turno no existe")

    return turno_service.update(db, turno_id, data)


@router.delete("/{turno_id}")
def eliminar(turno_id: int, db: Session = Depends(get_db)):
    turno_service.remove(db, turno_id)
    return {"ok": True}


@router.get("/docente/{docente_id}", response_model=list[TurnoOutFull])
def por_docente(docente_id: int, db: Session = Depends(get_db)):

    rows = (
        db.query(TurnoBase, Materia, Punto)
        .join(Materia, Materia.id == TurnoBase.materia_id)
        .join(Punto, Punto.id == TurnoBase.punto_id_plan)
        .filter(TurnoBase.docente_id == docente_id)
        .all()
    )

    return [
        {
            "id": t.id,
            "dia_semana": t.dia_semana,
            "hora_inicio": t.hora_inicio,
            "hora_fin": t.hora_fin,
            "tolerancia_min": t.tolerancia_min,
            "activo": t.activo,
            "materia_id": m.id,
            "materia_nombre": m.nombre,
            "punto_id_plan": p.id,
            "punto_nombre": p.etiqueta,
        }
        for t, m, p in rows
    ]

@router.get("/{turno_id}", response_model=TurnoOutEditable)
def obtener(turno_id: int, db: Session = Depends(get_db)):

    t = db.query(TurnoBase).filter(TurnoBase.id == turno_id).first()
    if not t:
        raise HTTPException(404, "No existe")

    # estado se infiere por instancias (hoy)
    hoy = datetime.now(ARG_TZ).date()
    inst = (
        db.query(TurnoInstancia)
        .filter(
            TurnoInstancia.turno_base_id == t.id,
            TurnoInstancia.fecha == hoy
        )
        .first()
    )

    estado = inst.estado.value if inst else "PROGRAMADO"

    return {
        "id": t.id,
        "dia_semana": t.dia_semana,
        "hora_inicio": t.hora_inicio,
        "hora_fin": t.hora_fin,
        "tolerancia_min": t.tolerancia_min,
        "activo": t.activo,
        "estado": estado,
        "materia_id": t.materia_id,
        "materia_nombre": t.materia.nombre,
        "punto_id_plan": t.punto_id_plan,
        "punto_nombre": t.punto_plan.etiqueta,
    }

@router.get("/docente/{docente_id}/hoy", response_model=list[TurnoOutFull])
def turnos_hoy(docente_id: int, db: Session = Depends(get_db)):
    hoy_dow = datetime.now(ARG_TZ).isoweekday()  # 1..7

    rows = (
        db.query(TurnoBase, Materia, Punto)
        .join(Materia, Materia.id == TurnoBase.materia_id)
        .join(Punto, Punto.id == TurnoBase.punto_id_plan)
        .filter(
            TurnoBase.docente_id == docente_id,
            TurnoBase.dia_semana == hoy_dow,
            TurnoBase.activo == True
        )
        .all()
    )

    return [
        {
            "id": tb.id,
            "dia_semana": tb.dia_semana,
            "hora_inicio": tb.hora_inicio,
            "hora_fin": tb.hora_fin,
            "tolerancia_min": tb.tolerancia_min,
            "activo": tb.activo,
            "materia_id": m.id,
            "materia_nombre": m.nombre,
            "punto_id_plan": p.id,
            "punto_nombre": p.etiqueta if hasattr(p, "etiqueta") else getattr(p, "nombre", ""),
        }
        for tb, m, p in rows
    ]


@router.get("/docente/{docente_id}/estado-hoy")
def estado_docente_hoy(docente_id: int, db: Session = Depends(get_db)):

    ahora_ar = datetime.now(ARG_TZ)
    hoy_ar = ahora_ar.date()
    dow = ahora_ar.isoweekday()

    # traer TurnoBase del docente para hoy
    bases = (
        db.query(TurnoBase, Materia)
        .join(Materia, Materia.id == TurnoBase.materia_id)
        .filter(
            TurnoBase.docente_id == docente_id,
            TurnoBase.dia_semana == dow,
            TurnoBase.activo == True
        )
        .all()
    )

    resultado = []

    for tb, m in bases:

        # instancia del día (si ya fue creada)
        ti = (
            db.query(TurnoInstancia)
            .filter(
                TurnoInstancia.turno_base_id == tb.id,
                TurnoInstancia.fecha == hoy_ar
            )
            .first()
        )

        # punto real (si hay instancia) o plan
        if ti:
            p = db.query(Punto).filter(Punto.id == ti.punto_id_real).first()
            punto_nombre = p.etiqueta if p and hasattr(p, "etiqueta") else (getattr(p, "nombre", None) if p else None)
        else:
            p = db.query(Punto).filter(Punto.id == tb.punto_id_plan).first()
            punto_nombre = p.etiqueta if p and hasattr(p, "etiqueta") else (getattr(p, "nombre", None) if p else None)

        # última asistencia del día para esa instancia (si hay)
        ultima = None
        if ti:
            ultima = (
                db.query(Asistencia)
                .filter(Asistencia.turno_instancia_id == ti.id)
                .order_by(Asistencia.ts_lectura_utc.desc())
                .first()
            )

        if ti:
            if ti:
                if ti.estado == EstadoTurnoInstancia.FINALIZADO:

                    if ultima:
                        estado = f"FINALIZADO ({ultima.estado.value})"
                    else:
                        estado = "FINALIZADO (AUSENTE)"

                elif ti.estado == EstadoTurnoInstancia.EN_CURSO:
                    if ultima:
                        estado = ultima.estado.value
                    else:
                        estado = "EN_CURSO"

                else:
                    estado = "PROGRAMADO"
        else:
            # fallback solo por horario
            ahora_min = ahora_ar.hour * 60 + ahora_ar.minute
            ini = tb.hora_inicio.hour * 60 + tb.hora_inicio.minute
            fin = tb.hora_fin.hour * 60 + tb.hora_fin.minute + (tb.tolerancia_min or 0)

            if ahora_min < ini:
                estado = "PROGRAMADO"
            elif ahora_min > fin:
                estado = "FINALIZADO"
            else:
                estado = "EN_CURSO"

        resultado.append({
            "turno_base_id": tb.id,
            "materia_nombre": m.nombre,
            "punto_nombre": punto_nombre,
            "hora_inicio": tb.hora_inicio.strftime("%H:%M"),
            "hora_fin": tb.hora_fin.strftime("%H:%M"),
            "estado": estado,
            "turno_instancia_id": ti.id if ti else None
        })

    return resultado

@router.get("/{turno_id}", response_model=TurnoOutEditable)
def obtener(turno_id: int, db: Session = Depends(get_db)):

    tb = db.query(TurnoBase).filter(TurnoBase.id == turno_id).first()
    if not tb:
        raise HTTPException(404, "No existe")

    hoy_ar = datetime.now(ARG_TZ).date()
    ti = (
        db.query(TurnoInstancia)
        .filter(
            TurnoInstancia.turno_base_id == tb.id,
            TurnoInstancia.fecha == hoy_ar
        )
        .first()
    )

    estado = ti.estado.value if ti else "PROGRAMADO"

    punto = db.query(Punto).filter(Punto.id == tb.punto_id_plan).first()
    punto_nombre = punto.etiqueta if punto and hasattr(punto, "etiqueta") else getattr(punto, "nombre", "")

    materia = db.query(Materia).filter(Materia.id == tb.materia_id).first()

    return {
        "id": tb.id,
        "dia_semana": tb.dia_semana,
        "hora_inicio": tb.hora_inicio,
        "hora_fin": tb.hora_fin,
        "tolerancia_min": tb.tolerancia_min,
        "activo": tb.activo,

        "estado": estado,

        "materia_id": tb.materia_id,
        "materia_nombre": materia.nombre if materia else "",

        "punto_id_plan": tb.punto_id_plan,
        "punto_nombre": punto_nombre,
    }

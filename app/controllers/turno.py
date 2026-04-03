from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.services.turno_service import turno_service
from app.schemas.turno import TurnoOut, TurnoCreate, TurnoUpdate, TurnoOutFull, TurnoOutEditable
from app.models.turno import Turno, EstadoTurno
from app.models.materia import Materia
from app.models.punto import Punto
from app.models.asistencia import Asistencia
from sqlalchemy import func
from datetime import datetime, date
import pytz  # si usás tz


router = APIRouter(prefix="/turnos", tags=["turnos"])

@router.get("", response_model=list[TurnoOut])
def listar(db: Session = Depends(get_db)): return turno_service.list(db)

@router.post("", response_model=TurnoOut)
def crear(data: TurnoCreate, db: Session = Depends(get_db)): return turno_service.create(db, data)

@router.put("/{turno_id}", response_model=TurnoOut)
def actualizar(turno_id: int, data: TurnoUpdate, db: Session = Depends(get_db)):

    turno = db.query(Turno).filter(Turno.id == turno_id).first()
    if not turno:
        raise HTTPException(404, "El turno no existe")

    # ============================
    # A) Bloquear FINALIZADO
    # ============================
    if turno.estado == EstadoTurno.FINALIZADO:
        raise HTTPException(
            400,
            "No se puede editar un turno ya finalizado"
        )

    # ============================
    # B) Buscar asistencias
    # ============================
    asistencias = (
        db.query(Asistencia)
        .filter(Asistencia.turno_id == turno_id)
        .count()
    )

    # ============================
    # C) Turno EN CURSO
    # ============================
    if turno.estado == EstadoTurno.EN_CURSO:

        # Si tiene asistencias → solo se permite editar el punto
        if asistencias > 0:
            if (
                data.hora_inicio != turno.hora_inicio or
                data.hora_fin != turno.hora_fin or
                data.dia_semana != turno.dia_semana or
                data.materia_id != turno.materia_id
            ):
                raise HTTPException(
                    400,
                    "El turno está en curso: solo se permite modificar el punto del turno"
                )

            turno.punto_id_plan = data.punto_id_plan
            db.commit()
            db.refresh(turno)
            return turno

        else:
            # Caso raro: turno en curso sin asistencia
            if (
                data.hora_inicio != turno.hora_inicio or
                data.hora_fin != turno.hora_fin or
                data.dia_semana != turno.dia_semana or
                data.materia_id != turno.materia_id
            ):
                raise HTTPException(
                    400,
                    "El turno está en curso: solo se permite modificar el punto"
                )

            turno.punto_id_plan = data.punto_id_plan
            db.commit()
            db.refresh(turno)
            return turno

    # ============================
    # D) PROGRAMADO con asistencias → no editable
    # ============================
    if asistencias > 0:
        raise HTTPException(
            400,
            "No se puede editar un turno que ya tiene asistencias registradas"
        )

    # ============================
    # E) PROGRAMADO sin asistencias → edición total
    # ============================
    obj = turno_service.update(db, turno_id, data)
    return obj



@router.delete("/{turno_id}")
def eliminar(turno_id: int, db: Session = Depends(get_db)):
    turno_service.remove(db, turno_id); return {"ok": True}

@router.get("/docente/{docente_id}", response_model=list[TurnoOutFull])
def por_docente(docente_id: int, db: Session = Depends(get_db)):
    turnos = (
        db.query(Turno, Materia, Punto)
        .join(Materia, Materia.id == Turno.materia_id)
        .join(Punto, Punto.id == Turno.punto_id_plan)
        .filter(Turno.docente_id == docente_id)
        .all()
    )

    resultado = []
    for t, m, p in turnos:
        resultado.append({
            "id": t.id,
            "dia_semana": t.dia_semana,
            "hora_inicio": t.hora_inicio,
            "hora_fin": t.hora_fin,
            "tolerancia_min": t.tolerancia_min,
            "activo": t.activo,

            "materia_id": m.id,
            "materia_nombre": m.nombre,

            "punto_id_plan": p.id,
            "punto_nombre": p.etiqueta if hasattr(p, "etiqueta") else p.nombre
        })

    return resultado

@router.get("/{turno_id}", response_model=TurnoOut)
def obtener(turno_id: int, db: Session = Depends(get_db)):
    obj = db.query(Turno).filter(Turno.id == turno_id).first()
    if not obj:
        raise HTTPException(404, "No existe")
    return obj

from datetime import datetime

@router.get("/docente/{docente_id}/hoy", response_model=list[TurnoOutFull])
def turnos_hoy(docente_id: int, db: Session = Depends(get_db)):
    hoy = datetime.now().weekday() + 1  # lunes=1 ... domingo=7

    turnos = (
        db.query(Turno, Materia, Punto)
        .join(Materia, Materia.id == Turno.materia_id)
        .join(Punto, Punto.id == Turno.punto_id_plan)
        .filter(Turno.docente_id == docente_id)
        .filter(Turno.dia_semana == hoy)
        .all()
    )

    resultado = []
    for t, m, p in turnos:
        resultado.append({
            "id": t.id,
            "dia_semana": t.dia_semana,
            "hora_inicio": t.hora_inicio,
            "hora_fin": t.hora_fin,
            "tolerancia_min": t.tolerancia_min,
            "activo": t.activo,
            "materia_id": m.id,
            "materia_nombre": m.nombre,
            "punto_id_plan": p.id,
            "punto_nombre": p.etiqueta if hasattr(p, "etiqueta") else p.nombre
        })

    return resultado

@router.get("/docente/{docente_id}/estado-hoy")
def estado_docente_hoy(docente_id: int, db: Session = Depends(get_db)):

    ar_tz = pytz.timezone("America/Argentina/Buenos_Aires")
    ahora_ar = datetime.now(ar_tz)
    hoy = ahora_ar.date()

    turnos = (
        db.query(Turno, Materia, Punto)
        .join(Materia, Materia.id == Turno.materia_id)
        .join(Punto, Punto.id == Turno.punto_id_plan)
        .filter(Turno.docente_id == docente_id)
        .filter(Turno.dia_semana == ahora_ar.isoweekday())
        .all()
    )

    resultado = []

    for t, m, p in turnos:

        # asistencia más reciente del día
        asistencia = (
            db.query(Asistencia)
            .filter(Asistencia.turno_id == t.id)
            .filter(Asistencia.ts_lectura_utc >= hoy)
            .order_by(Asistencia.ts_lectura_utc.desc())
            .first()
        )

        # convertir horarios del turno a minutos
        minutos_ahora = ahora_ar.hour * 60 + ahora_ar.minute
        minutos_ini = t.hora_inicio.hour * 60 + t.hora_inicio.minute
        minutos_fin = t.hora_fin.hour * 60 + t.hora_fin.minute + (t.tolerancia_min or 0)

        # si hay asistencia → usar el estado real
        if asistencia:
            estado = asistencia.estado.value

        else:
            # NO hay asistencia registrada…
            if minutos_ahora < minutos_ini:
                estado = "PROGRAMADO"
            elif minutos_ahora > minutos_fin:
                estado = "FINALIZADO"
            else:
                estado = "AUSENTE"

        resultado.append({
            "turno_id": t.id,
            "materia_nombre": m.nombre,
            "punto_nombre": p.etiqueta,
            "hora_inicio": t.hora_inicio.strftime("%H:%M"),
            "hora_fin": t.hora_fin.strftime("%H:%M"),
            "estado": estado,
        })

    return resultado


@router.get("/{turno_id}", response_model=TurnoOutEditable)
def obtener(turno_id: int, db: Session = Depends(get_db)):
    obj = db.query(Turno).filter(Turno.id == turno_id).first()
    if not obj:
        raise HTTPException(404, "No existe")
    return obj
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.services.turno_service import turno_service
from app.schemas.turno import TurnoOut, TurnoCreate, TurnoUpdate, TurnoOutFull
from app.models.turno import Turno
from app.models.materia import Materia
from app.models.punto import Punto
from app.models.asistencia import Asistencia
from sqlalchemy import func
from datetime import datetime, date


router = APIRouter(prefix="/turnos", tags=["turnos"])

@router.get("", response_model=list[TurnoOut])
def listar(db: Session = Depends(get_db)): return turno_service.list(db)

@router.post("", response_model=TurnoOut)
def crear(data: TurnoCreate, db: Session = Depends(get_db)): return turno_service.create(db, data)

@router.put("/{turno_id}", response_model=TurnoOut)
def actualizar(turno_id: int, data: TurnoUpdate, db: Session = Depends(get_db)):
    obj = turno_service.update(db, turno_id, data)
    if not obj: raise HTTPException(404, "No existe")
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
    hoy_dia = datetime.now().weekday() + 1
    ahora = datetime.now().time()

    turnos = (
        db.query(Turno, Materia, Punto)
        .join(Materia, Materia.id == Turno.materia_id)
        .join(Punto, Punto.id == Turno.punto_id_plan)
        .filter(Turno.docente_id == docente_id)
        .filter(Turno.dia_semana == hoy_dia)
        .all()
    )

    resultado = []

    for t, m, p in turnos:

        asistencia = (
            db.query(Asistencia)
            .filter(Asistencia.turno_id == t.id)
            .filter(func.date(Asistencia.ts_lectura_utc) == date.today())
            .order_by(Asistencia.ts_lectura_utc.desc())
            .first()
        )

        if asistencia:
            estado = asistencia.estado.value
        else:
            estado = "FINALIZADO" if ahora > t.hora_fin else "PROGRAMADO"

        resultado.append({
            "turno_id": t.id,
            "materia_nombre": m.nombre,
            "punto_nombre": p.etiqueta,
            "hora_inicio": str(t.hora_inicio),
            "hora_fin": str(t.hora_fin),
            "estado": estado,
        })

    return resultado

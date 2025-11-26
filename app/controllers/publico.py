# app/controllers/publico.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.web.deps import get_db
from app.models.turno import Turno
from app.models.docente import Docente
from app.models.materia import Materia
from app.models.punto import Punto

router = APIRouter(prefix="/public", tags=["publico"])

@router.get("/estados")
def estados(
    ahora: bool | None = Query(True),
    qDocente: str | None = None,
    qMateria: str | None = None,
    solo_presentes: int | None = None,
    db: Session = Depends(get_db)
):
    """
    Foto del momento para estudiantes.
    Si ahora=True, filtra por día y hora actual.
    """
    now = datetime.now()
    dia = now.weekday()
    hora = now.time()

    q = (
        db.query(Turno, Docente, Materia, Punto)
        .join(Docente, Turno.docente_id == Docente.id)
        .join(Materia, Turno.materia_id == Materia.id)
        .join(Punto, Turno.punto_id == Punto.id)  # <-- si tu campo es punto_plan_id, cámbialo aquí
        .filter(Turno.activo == True, Docente.activo == True, Materia.activo == True)
    )

    if ahora:
        q = q.filter(
            Turno.dia_semana == dia,
            Turno.hora_inicio <= hora,
            Turno.hora_fin >= hora
        )

    if qDocente:
        like = f"%{qDocente}%"
        q = q.filter((Docente.apellido.like(like)) | (Docente.nombre.like(like)))

    if qMateria:
        like = f"%{qMateria}%"
        q = q.filter(Materia.nombre.like(like) | Materia.codigo.like(like))

    rows = q.all()

    # Estado "naive": si está en un turno vigente -> "En curso".
    # Ya cuando tengas asistencias registradas, podés reemplazar esto
    # por IN/OUT + tolerancias.
    out = []
    for t, d, m, p in rows:
        out.append({
            "profesor": f"{d.nombre} {d.apellido}",
            "materia": m.nombre,
            "aula": p.aula or p.etiqueta,
            "estado": "En curso",
            "desde": t.hora_inicio.strftime("%H:%M"),
            "hasta": t.hora_fin.strftime("%H:%M"),
        })

    if solo_presentes:
        out = [x for x in out if x["estado"].lower() == "en curso"]

    return out

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.models.docente import Docente
from app.models.materia import Materia
from app.models.punto import Punto
from app.models.turno import Turno

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

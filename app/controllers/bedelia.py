from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import date
from app.web.deps import get_db
from app.models.asistencia import Asistencia
from app.models.docente import Docente
from app.models.turno import Turno
from app.models.punto import Punto

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

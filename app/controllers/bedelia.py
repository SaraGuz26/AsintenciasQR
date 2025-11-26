# app/controllers/bedelia.py
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from datetime import datetime, date
import csv
import io

from app.web.deps import get_db
from app.models.turno import Turno
from app.models.docente import Docente
from app.models.materia import Materia
from app.models.punto import Punto
from app.models.asistencia import Asistencia

router = APIRouter(prefix="/bedelia", tags=["bedelia"])

def _parse_fecha(fecha_str: str | None) -> date:
    if fecha_str:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    return date.today()

@router.get("/resumen")
def resumen(
    fecha: str | None = Query(None, description="YYYY-MM-DD"),
    docente: str | None = Query(None, description="Filtro por nombre/apellido"),
    db: Session = Depends(get_db)
):
    """
    Resumen por docente para la fecha dada.
    presentes = asistencias registradas para esos turnos en esa fecha
    ausentes  = turnos del día - presentes
    tardanzas = 0 (placeholder por ahora)
    """
    d = _parse_fecha(fecha)
    dia = d.weekday()

    # Turnos del día, con docente/materia/punto
    q = (
        db.query(Turno, Docente, Materia, Punto)
        .join(Docente, Turno.docente_id == Docente.id)
        .join(Materia, Turno.materia_id == Materia.id)
        .join(Punto, Turno.punto_id == Punto.id)  # <-- cambia si es punto_plan_id
        .filter(
            Turno.activo == True,
            Docente.activo == True,
            Materia.activo == True,
            Turno.dia_semana == dia
        )
    )
    if docente:
        like = f"%{docente}%"
        q = q.filter((Docente.apellido.like(like)) | (Docente.nombre.like(like)))

    rows = q.all()

    # Agrupar por docente
    by_doc = {}
    for t, doc, mat, pto in rows:
        if doc.id not in by_doc:
            by_doc[doc.id] = {
                "profesor": f"{doc.nombre} {doc.apellido}",
                "turnos_del_dia": 0,
                "presentes": 0,
                "ausentes": 0,
                "tardanzas": 0,  # placeholder
            }
        by_doc[doc.id]["turnos_del_dia"] += 1

        # ¿Hubo asistencia para este turno en la fecha?
        hay_asistencia = (
            db.query(Asistencia.id)
            .filter(
                Asistencia.turno_id == t.id,
                Asistencia.fecha == d,
                Asistencia.es_valida == True
            )
            .first()
            is not None
        )
        if hay_asistencia:
            by_doc[doc.id]["presentes"] += 1

    # Calcular ausentes
    for v in by_doc.values():
        v["ausentes"] = v["turnos_del_dia"] - v["presentes"]

    # Salida ordenada por apellido
    salida = sorted(by_doc.values(), key=lambda x: x["profesor"])
    return salida

@router.get("/export.csv")
def export_csv(
    fecha: str | None = Query(None, description="YYYY-MM-DD"),
    docente: str | None = Query(None, description="Filtro por nombre/apellido"),
    db: Session = Depends(get_db)
):
    """
    Mismo dataset que /bedelia/resumen pero como CSV descargable.
    """
    data = resumen(fecha=fecha, docente=docente, db=db)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Profesor", "Turnos del día", "Presentes", "Ausentes", "Tardanzas"])
    for row in data:
        writer.writerow([
            row["profesor"],
            row["turnos_del_dia"],
            row["presentes"],
            row["ausentes"],
            row["tardanzas"]
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")  # BOM para Excel
    headers = {
        "Content-Disposition": f'attachment; filename="resumen_{fecha or date.today().isoformat()}.csv"'
    }
    return Response(content=csv_bytes, media_type="text/csv; charset=utf-8", headers=headers)

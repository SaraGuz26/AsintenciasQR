from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, time
import pytz  # si usás tz
from app.web.deps import get_db
from app.models.asistencia import Asistencia, EstadoAsistencia, FuenteLectura
from app.models.turno import Turno
from app.models.credencial import Credencial
from app.models.docente import Docente
from app.models.punto import Punto
from app.models.base import Base

router = APIRouter(prefix="/asistencias", tags=["asistencias"])

class RegistroQR(Base):
    punto_id: int
    credencial_id: int
    qr_nonce: str
    fuente: FuenteLectura

@router.post("/registrar")
def registrar_asistencia(data: RegistroQR, db: Session = Depends(get_db)):

    ahora = datetime.utcnow()

    # 1) Validar credencial
    cred = db.query(Credencial).filter(Credencial.id == data.credencial_id).first()
    if not cred:
        raise HTTPException(400, "Credencial inválida")

    docente = cred.docente
    if not docente:
        raise HTTPException(400, "La credencial no pertenece a ningún docente")

    # 2) Buscar turno activo
    dia = ahora.isoweekday()  # 1=Mon..7=Sun
    turnos = db.query(Turno).filter(
        Turno.docente_id == docente.id,
        Turno.activo == True,
        Turno.dia_semana == dia
    ).all()

    turno_actual = None
    estado = EstadoAsistencia.FUERA_DE_HORARIO

    # 3) Determinar si está dentro del turno o en tolerancia
    for t in turnos:
        inicio = datetime.combine(ahora.date(), t.hora_inicio)
        fin = datetime.combine(ahora.date(), t.hora_fin)

        # dentro del horario normal
        if inicio <= ahora <= fin:
            turno_actual = t
            estado = EstadoAsistencia.EN_CONSULTA
            break

        # dentro de tolerancia (tarde)
        limite_tarde = inicio.replace(minute=inicio.minute + t.tolerancia_min)
        if inicio < ahora <= limite_tarde:
            turno_actual = t
            estado = EstadoAsistencia.TARDE
            break

    # 4) Crear asistencia
    asistencia = Asistencia(
        docente_id=docente.id,
        punto_id=data.punto_id,
        turno_id=turno_actual.id if turno_actual else None,
        credencial_id=cred.id,
        ts_lectura_utc=ahora,
        estado=estado,
        motivo_id=None,
        motivo_texto=None,
        fuente=data.fuente,
        qr_nonce=data.qr_nonce,
        valido=True,
        detalle_error=None
    )

    db.add(asistencia)
    db.commit()
    db.refresh(asistencia)

    return {
        "ok": True,
        "estado": asistencia.estado,
        "turno_id": asistencia.turno_id,
        "docente": f"{docente.nombre} {docente.apellido}"
    }

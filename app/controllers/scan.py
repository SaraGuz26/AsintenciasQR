from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.web.deps import get_db
from app.utils.qr_crypto import verify_compact
from app.models.credencial import Credencial
from app.models.docente import Docente
from app.models.turno import Turno
from app.models.asistencia import Asistencia, EstadoAsistencia, FuenteLectura
from app.core.config import get_settings

router = APIRouter(prefix="/scan", tags=["lectura QR"])


@router.post("/validar")
def validar_qr(data: dict, db: Session = Depends(get_db)):
    """
    data = { "qr_text": "...", "punto_id": X }
    """
    s = get_settings()

    qr_text = data.get("qr_text")
    punto_id = data.get("punto_id")

    if not qr_text:
        raise HTTPException(400, "Falta qr_text")

    if not punto_id:
        raise HTTPException(400, "Falta punto_id")

    # ================================
    # 1. VERIFICAR FIRMA DEL QR
    # ================================
    try:
        payload = verify_compact(qr_text, s.SECRET_QR)
    except Exception:
        raise HTTPException(401, "QR inválido o alterado")

    cred_id = payload["credencial_id"]
    nonce = payload["nonce"]

    # ================================
    # 2. VALIDAR CREDENCIAL ACTIVA
    # ================================
    cred = (
        db.query(Credencial)
        .filter(Credencial.id == cred_id)
        .filter(Credencial.revocado == False)
        .first()
    )

    if not cred:
        raise HTTPException(403, "Credencial no válida")

    if cred.nonce_actual != nonce:
        raise HTTPException(403, "QR vencido")

    docente_id = cred.docente_id

    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(404, "Docente no encontrado")

    # ================================
    # 3. DETERMINAR TURNO CORRESPONDIENTE
    # ================================
    ahora = datetime.now()
    hora = ahora.time()
    dia_semana = ahora.weekday() + 1

    turnos = (
        db.query(Turno)
        .filter(Turno.docente_id == docente_id)
        .filter(Turno.dia_semana == dia_semana)
        .all()
    )

    turno_actual = None

    for t in turnos:
        inicio = t.hora_inicio
        fin = (datetime.combine(date.today(), t.hora_fin) +
               timedelta(minutes=t.tolerancia_min)).time()

        if inicio <= hora <= fin:
            turno_actual = t
            break

    # ================================
    # 4. DETERMINAR ESTADO
    # ================================
    if turno_actual:
        if hora <= turno_actual.hora_inicio:
            estado = EstadoAsistencia.EN_CONSULTA
        else:
            estado = EstadoAsistencia.TARDE
    else:
        estado = EstadoAsistencia.FUERA_DE_HORARIO

    # ================================
    # 5. GUARDAR REGISTRO
    # ================================
    asistencia = Asistencia(
        docente_id=docente_id,
        punto_id=punto_id,
        turno_id=turno_actual.id if turno_actual else None,
        credencial_id=cred.id,
        ts_lectura_utc=ahora,
        estado=estado,
        fuente=FuenteLectura.LECTOR,
        qr_nonce=nonce,
        valido=True
    )

    db.add(asistencia)
    db.commit()
    db.refresh(asistencia)

    return {
        "ok": True,
        "docente": f"{docente.apellido}, {docente.nombre}",
        "estado": estado.value,
        "turno_id": turno_actual.id if turno_actual else None
    }


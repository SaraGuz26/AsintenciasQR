# app/services/scan_service.py
from datetime import datetime, date, time, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.utils.qr_crypto import verify_compact
from app.models.credencial import Credencial
from app.models.turno import Turno
from app.models.asistencia import Asistencia
from app.models.docente import Docente
from app.models.materia import Materia
from app.models.punto import Punto

def _estado_turno(now: datetime, turno: Turno) -> str:
    hi: time = turno.hora_inicio
    hf: time = turno.hora_fin
    tol = (turno.tolerancia_min or 0)

    # convertir a datetimes del día
    dt_hi = now.replace(hour=hi.hour, minute=hi.minute, second=0, microsecond=0)
    dt_hf = now.replace(hour=hf.hour, minute=hf.minute, second=0, microsecond=0)
    dt_tol = dt_hi + timedelta(minutes=tol)

    if dt_hi <= now <= dt_hf:
        if now > dt_tol:
            return "Tarde"
        return "En curso"
    return "Fuera de turno"

def validar_y_registrar(db: Session, qr_text: str, punto_id: int):
    s = get_settings()

    # 1) Verificar firma y parsear payload
    try:
        payload = verify_compact(qr_text, s.SECRET_QR)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # payload esperado
    docente_id = int(payload.get("docente_id", 0))
    credencial_id = int(payload.get("credencial_id", 0))
    nonce = payload.get("nonce")
    exp = int(payload.get("exp", 0))

    if not (docente_id and credencial_id and nonce and exp):
        raise HTTPException(400, "Payload incompleto en el QR")

    now = datetime.now()
    if now.timestamp() > exp:
        raise HTTPException(400, "QR expirado")

    # 2) Validar credencial
    cred = db.query(Credencial).filter(
        Credencial.id == credencial_id,
        Credencial.docente_id == docente_id,
        Credencial.activo == True
    ).first()
    if not cred:
        raise HTTPException(400, "Credencial inexistente o inactiva")
    if cred.nonce_actual != nonce:
        raise HTTPException(400, "Credencial revocada o no vigente (nonce)")

    # 3) Buscar turno vigente para docente + punto + día
    dia = now.weekday()

    turno = (
        db.query(Turno)
        .filter(
            Turno.docente_id == docente_id,
            Turno.punto_id == punto_id,          # si tu campo es punto_plan_id, cambialo aquí
            Turno.dia_semana == dia,
            Turno.activo == True
        )
        .first()
    )
    if not turno:
        # podría existir Turno pero en otro punto → decide el mensaje que prefieras
        raise HTTPException(404, "No hay turno vigente para este punto")

    # 4) Calcular estado
    estado = _estado_turno(now, turno)

    # 5) Registrar asistencia si corresponde (idempotente por turno+fecha)
    hoy = date.today()
    ya_esta = db.query(Asistencia).filter(
        Asistencia.turno_id == turno.id,
        Asistencia.fecha == hoy,
        Asistencia.es_valida == True
    ).first()

    saved = False
    if not ya_esta and estado != "Fuera de turno":
        a = Asistencia(
            turno_id=turno.id,
            fecha=hoy,
            credencial_id=credencial_id,
            es_valida=True
        )
        db.add(a)
        db.commit()
        saved = True

    # 6) Armar respuesta enriquecida
    doc = db.query(Docente).get(docente_id)
    mat = db.query(Materia).get(turno.materia_id)
    pto = db.query(Punto).get(punto_id)

    return {
        "ok": True,
        "docente_id": docente_id,
        "profesor": f"{doc.nombre} {doc.apellido}" if doc else None,
        "materia": mat.nombre if mat else None,
        "aula": (pto.aula or pto.etiqueta) if pto else None,
        "estado": estado,
        "desde": turno.hora_inicio.strftime("%H:%M"),
        "hasta": turno.hora_fin.strftime("%H:%M"),
        "registrado": saved
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.services.docente_service import docente_service
from app.schemas.docente import DocenteOut, DocenteCreate, DocenteUpdate, DocenteQR
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.web.deps import get_db
from app.models.docente import Docente
from app.models.credencial import Credencial
from app.models.asistencia import Asistencia , FuenteLectura
from app.models.turno import Turno, EstadoTurno
from app.models.materia import Materia
from app.models.punto import Punto
import secrets
from datetime import datetime
from app.services.scan_service import scan_service
import json
import pytz
from datetime import datetime, timezone
from app.repositories.turno_repo import turno_repo
from app.models.asistencia import EstadoAsistencia
from app.schemas.turno import TurnoOutEditable

ARG_TZ = pytz.timezone("America/Argentina/Buenos_Aires")


router = APIRouter(prefix="/docentes", tags=["docentes"])

@router.get("", response_model=list[DocenteOut])
def listar(db: Session = Depends(get_db)):
    return docente_service.list(db)

@router.post("", response_model=DocenteOut)
def crear(data: DocenteCreate, db: Session = Depends(get_db)):
    return docente_service.create(db, data)

@router.get("/{docente_id}", response_model=DocenteOut)
def obtener(docente_id: int, db: Session = Depends(get_db)):
    obj = docente_service.get(db, docente_id)
    if not obj: raise HTTPException(404, "No existe")
    return obj

@router.put("/{docente_id}", response_model=DocenteOut)
def actualizar(docente_id: int, data: DocenteUpdate, db: Session = Depends(get_db)):
    obj = docente_service.update(db, docente_id, data)
    if not obj: raise HTTPException(404, "No existe")
    return obj

@router.delete("/{docente_id}")
def eliminar(docente_id: int, db: Session = Depends(get_db)):
    docente_service.remove(db, docente_id)
    return {"ok": True}

@router.get("/{docente_id}/credencial")
def obtener_credencial(docente_id: int, db: Session = Depends(get_db)):
    docente = db.query(Docente).filter(Docente.id == docente_id).first()
    if not docente:
        raise HTTPException(404, "Docente no existe")

    # Buscar credencial activa
    cred = (
        db.query(Credencial)
        .filter(
            Credencial.docente_id == docente_id,
            Credencial.revocado == False
        )
        .order_by(Credencial.emitido_en.desc())
        .first()
    )

    # SI NO EXISTE → LA CREAMOS AUTOMÁTICAMENTE
    if not cred:
        cred = Credencial(
            docente_id=docente_id,
            nonce_actual=secrets.token_hex(8)[:16],
            emitido_en=datetime.utcnow(),
            revocado=False
        )
        db.add(cred)
        db.commit()
        db.refresh(cred)

    # Devolver credencial (ya sea la existente o la recién creada)
    return {
        "docente_id": docente.id,
        "nombre": f"{docente.nombre} {docente.apellido}",
        "legajo": docente.legajo,
        "credencial_id": cred.id,
        "nonce": cred.nonce_actual,
        "emitido_en": cred.emitido_en.isoformat(),
        "qr_payload": {
            "credencial_id": cred.id,
            "nonce": cred.nonce_actual
        }
    }



@router.post("/{docente_id}/credencial/regenerar")
def regenerar_credencial(docente_id: int, db: Session = Depends(get_db)):

    cred = (
        db.query(Credencial)
        .filter(
            Credencial.docente_id == docente_id,
            Credencial.revocado == False
        )
        .first()
    )

    if not cred:
        raise HTTPException(404, "No existe una credencial activa para regenerar")

    cred.nonce_actual = secrets.token_hex(8)[:16]  # 16 chars
    cred.emitido_en = datetime.utcnow()

    db.add(cred)
    db.commit()
    db.refresh(cred)

    return {
        "ok": True,
        "credencial_id": cred.id,
        "nonce": cred.nonce_actual
    }


@router.post("/marcar-turno")
def marcar_turno(data: DocenteQR, db: Session = Depends(get_db)):

    ARG = pytz.timezone("America/Argentina/Buenos_Aires")
    ahora_ar = datetime.now(ARG)                    # aware local
    ahora_utc = ahora_ar.astimezone(pytz.UTC)       # guardar en UTC

    # -------------------------------------------------------
    # 1) Buscar credencial
    # -------------------------------------------------------
    cred = (
        db.query(Credencial)
        .filter(Credencial.id == data.credencial_id, Credencial.revocado == False)
        .first()
    )
    if not cred:
        raise HTTPException(404, "Credencial no válida")

    # -------------------------------------------------------
    # 2) Validar nonce
    # -------------------------------------------------------
    if cred.nonce_actual != data.nonce:
        raise HTTPException(400, "QR inválido o vencido")

    docente_id = cred.docente_id

    # -------------------------------------------------------
    # 3) Obtener turno vigente
    # -------------------------------------------------------
    t = turno_repo.vigente_para(db, docente_id, ahora_ar)

    if not t:
        raise HTTPException(400, detail="No tiene turno vigente ahora")

    turno, exc = t

    # -------------------------------------------------------
    # 4) Horario real con excepciones
    # -------------------------------------------------------
    ini = exc.hora_inicio_alt if exc and exc.hora_inicio_alt else turno.hora_inicio
    fin = exc.hora_fin_alt if exc and exc.hora_fin_alt else turno.hora_fin
    tol = turno.tolerancia_min or 0

    minutos_ahora = ahora_ar.hour * 60 + ahora_ar.minute
    minutos_ini   = ini.hour * 60 + ini.minute
    minutos_fin   = fin.hour * 60 + fin.minute

    # -------------------------------------------------------
    # 5) Determinar estado de ASISTENCIA (nuevo esquema)
    # -------------------------------------------------------
    if minutos_ahora < minutos_ini - tol:
        estado = EstadoAsistencia.AUSENTE
        motivo = "Fuera de horario (temprano)"
        valido = False

    elif minutos_ahora > minutos_fin:
        estado = EstadoAsistencia.AUSENTE
        motivo = "Fuera de horario (tarde)"
        valido = False

    elif minutos_ahora > minutos_ini + tol:
        estado = EstadoAsistencia.TARDE
        motivo = None
        valido = True

    else:
        estado = EstadoAsistencia.PRESENTE
        motivo = None
        valido = True

    # -------------------------------------------------------
    # 6) Prevenir duplicados HOY
    # -------------------------------------------------------
    inicio_hoy_ar  = datetime(ahora_ar.year, ahora_ar.month, ahora_ar.day, tzinfo=ARG)
    inicio_hoy_utc = inicio_hoy_ar.astimezone(pytz.UTC)

    ultima = (
        db.query(Asistencia)
        .filter(
            Asistencia.docente_id == docente_id,
            Asistencia.turno_id == turno.id,
            Asistencia.ts_lectura_utc >= inicio_hoy_utc,
        )
        .order_by(Asistencia.ts_lectura_utc.desc())
        .first()
    )

    # Si ya registró asistencia válida, no crear otra
    if ultima and ultima.estado in (EstadoAsistencia.PRESENTE, EstadoAsistencia.TARDE):
        return {
            "ok": True,
            "mensaje": "La asistencia ya estaba registrada",
            "estado": ultima.estado.value,
            "turno_id": turno.id,
            "hora": ultima.ts_lectura_utc,
        }

    # -------------------------------------------------------
    # 7) Registrar nueva asistencia
    # -------------------------------------------------------
    asistencia = Asistencia(
        docente_id=docente_id,
        turno_id=turno.id,
        punto_id=turno.punto_id_plan,
        credencial_id=cred.id,
        ts_lectura_utc=ahora_utc,
        estado=estado,
        motivo_texto=motivo,
        valido=valido,
        qr_nonce=data.nonce,
        fuente=FuenteLectura.CAMARA,
    )

    db.add(asistencia)

    # -------------------------------------------------------
    # 8) Cambiar estado del turno → EN_CURSO
    # -------------------------------------------------------
    from app.models.turno import EstadoTurno

    if turno.estado != EstadoTurno.EN_CURSO:
        turno.estado = EstadoTurno.EN_CURSO
        db.add(turno)

    db.commit()
    db.refresh(asistencia)

    # -------------------------------------------------------
    # 9) Respuesta al frontend
    # -------------------------------------------------------
    return {
        "ok": valido,
        "estado": estado.value,
        "turno_id": turno.id,
        "hora_lectura_local": ahora_ar.strftime("%H:%M"),
        "motivo": motivo
    }


@router.get("/docente/{docente_id}", response_model=list[TurnoOutEditable])
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

            "estado": t.estado.value,   # <-- AQUÍ SE AGREGA

            "materia_id": m.id,
            "materia_nombre": m.nombre,

            "punto_id_plan": p.id,
            "punto_nombre": p.etiqueta if hasattr(p, "etiqueta") else p.nombre
        })

    return resultado

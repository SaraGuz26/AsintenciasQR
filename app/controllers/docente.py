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
from app.models.asistencia import Asistencia , FuenteLectura, EstadoAsistencia
from app.models.turno_instancia import TurnoInstancia, EstadoTurnoInstancia
from app.models.turno_base import TurnoBase
from app.models.materia import Materia
from app.models.punto import Punto
import secrets
from datetime import datetime
import json
import pytz
from datetime import datetime, timezone
from app.repositories.turno_repo import turno_repo
from app.models.asistencia import EstadoAsistencia
from app.schemas.turno import TurnoOutEditable
from app.web.deps import get_current_docente  

ARG_TZ = pytz.timezone("America/Argentina/Buenos_Aires")


router = APIRouter(prefix="/docentes", tags=["docentes"])

# --- Ruta para el docente logueado ---
@router.get("/me", response_model=DocenteOut)
def mi_perfil(docente: Docente = Depends(get_current_docente)):
    """Devuelve el perfil del docente autenticado via JWT."""
    return docente

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

    ahora_ar = datetime.now(ARG_TZ)          # aware AR
    ahora_utc = ahora_ar.astimezone(pytz.UTC)

    # Buscar credencial activa
    cred = (
        db.query(Credencial)
        .filter(Credencial.id == data.credencial_id, Credencial.revocado == False)
        .first()
    )
    if not cred:
        raise HTTPException(404, "Credencial no válida")

    # Validar nonce
    if cred.nonce_actual != data.nonce:
        raise HTTPException(400, "QR inválido o vencido")

    docente_id = cred.docente_id

    # Obtener TurnoBase vigente 
    # Debe devolver: (turno_base, exc) o None
    t = turno_repo.vigente_para(db, docente_id, ahora_ar)
    if not t:
        raise HTTPException(400, detail="No tiene turno vigente ahora")

    turno_base, exc = t

    # 4) Horario real del día (si hay excepción)
    ini = exc.hora_inicio_alt if exc and exc.hora_inicio_alt else turno_base.hora_inicio
    fin = exc.hora_fin_alt if exc and exc.hora_fin_alt else turno_base.hora_fin
    tol = turno_base.tolerancia_min or 0

    minutos_ahora = ahora_ar.hour * 60 + ahora_ar.minute
    minutos_ini = ini.hour * 60 + ini.minute
    minutos_fin = fin.hour * 60 + fin.minute

    # 5) Determinar estado asistencia (igual que antes)
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

    # 6) Obtener o crear TurnoInstancia del día (fecha local AR)
    fecha_ar = ahora_ar.date()

    punto_real_id = (
        exc.punto_id_alt if (exc and getattr(exc, "punto_id_alt", None)) else turno_base.punto_id_plan
    )

    ti = (
        db.query(TurnoInstancia)
        .filter(TurnoInstancia.turno_base_id == turno_base.id,
                TurnoInstancia.fecha == fecha_ar)
        .first()
    )

    if not ti:
        ti = TurnoInstancia(
            turno_base_id=turno_base.id,
            fecha=fecha_ar,
            estado=EstadoTurnoInstancia.PROGRAMADO,
            punto_id_real=punto_real_id,
        )
        db.add(ti)
        db.flush()  # para tener ti.id sin commit

    # si cambió el punto por excepción y la instancia estaba con el plan viejo
    if ti.punto_id_real != punto_real_id:
        ti.punto_id_real = punto_real_id
        db.add(ti)

    # 7) Prevenir duplicados por instancia (no por turno_base)
    ultima = (
        db.query(Asistencia)
        .filter(
            Asistencia.turno_instancia_id == ti.id,
        )
        .order_by(Asistencia.ts_lectura_utc.desc())
        .first()
    )

    if ultima and ultima.estado in (EstadoAsistencia.PRESENTE, EstadoAsistencia.TARDE):
        return {
            "ok": True,
            "mensaje": "La asistencia ya estaba registrada",
            "estado": ultima.estado.value,
            "turno_instancia_id": ti.id,
            "hora_lectura_local": ahora_ar.strftime("%H:%M"),
        }

    # 8) Crear asistencia (punto del día = punto_real de instancia)
    asistencia = Asistencia(
        docente_id=docente_id,
        punto_id=ti.punto_id_real,
        turno_instancia_id=ti.id,
        credencial_id=cred.id,
        ts_lectura_utc=ahora_utc,
        estado=estado,
        motivo_texto=motivo,
        valido=valido,
        qr_nonce=data.nonce,
        fuente=FuenteLectura.CAMARA,
    )
    db.add(asistencia)

    # 9) Actualizar estado instancia si corresponde
    if valido and estado in (EstadoAsistencia.PRESENTE, EstadoAsistencia.TARDE):
        if ti.estado != EstadoTurnoInstancia.EN_CURSO:
            ti.estado = EstadoTurnoInstancia.EN_CURSO
        if not ti.inicio_real_utc:
            ti.inicio_real_utc = ahora_utc
        db.add(ti)

    db.commit()
    db.refresh(asistencia)

    return {
        "ok": valido,
        "estado": estado.value,
        "turno_instancia_id": ti.id,
        "hora_lectura_local": ahora_ar.strftime("%H:%M"),
        "motivo": motivo,
    }


@router.get("/docente/{docente_id}")
def por_docente(docente_id: int, db: Session = Depends(get_db)):

    rows = (
        db.query(TurnoBase, Materia, Punto)
        .join(Materia, Materia.id == TurnoBase.materia_id)
        .join(Punto, Punto.id == TurnoBase.punto_id_plan)
        .filter(TurnoBase.docente_id == docente_id)
        .all()
    )

    return [
        {
            "id": tb.id,
            "dia_semana": tb.dia_semana,
            "hora_inicio": tb.hora_inicio.strftime("%H:%M"),
            "hora_fin": tb.hora_fin.strftime("%H:%M"),
            "tolerancia_min": tb.tolerancia_min,
            "activo": tb.activo,

            "materia_id": m.id,
            "materia_nombre": m.nombre,

            "punto_id_plan": p.id,
            "punto_nombre": p.etiqueta if hasattr(p, "etiqueta") else getattr(p, "nombre", ""),
        }
        for (tb, m, p) in rows
    ]
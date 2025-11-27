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
from app.models.turno import Turno
import secrets
from datetime import datetime
from app.services.scan_service import scan_service
import json
from datetime import datetime, timezone
from app.repositories.turno_repo import turno_repo
from app.models.asistencia import EstadoAsistencia


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
    # 1) Buscar credencial por ID y que no esté revocada
    cred = (
        db.query(Credencial)
        .filter(
            Credencial.id == data.credencial_id,
            Credencial.revocado == False
        )
        .first()
    )

    if not cred:
        raise HTTPException(status_code=404, detail="Credencial no válida")

    # 2) Validar nonce
    if cred.nonce_actual != data.nonce:
        raise HTTPException(status_code=400, detail="QR inválido o vencido (nonce no coincide)")

    docente_id = cred.docente_id
    ahora = datetime.now() 

    # 3) Buscar turno vigente para este docente (usa la misma lógica que scan_service)
    t = turno_repo.vigente_para(db, docente_id, ahora)
    print("Turno forzado:", t)
    if not t:
        raise HTTPException(status_code=400, detail="El docente no tiene turno vigente en este momento")

    turno, exc = t

    # 4) Tomar horario efectivo (con excepción si la hubiera)
    ini = exc.hora_inicio_alt if exc and exc.hora_inicio_alt else turno.hora_inicio
    fin = exc.hora_fin_alt if exc and exc.hora_fin_alt else turno.hora_fin
    tol = turno.tolerancia_min or 0

    t_hora = ahora.time()
    minutos_ahora = t_hora.hour * 60 + t_hora.minute
    minutos_ini = ini.hour * 60 + ini.minute
    minutos_fin = fin.hour * 60 + fin.minute

    # 5) Determinar estado simple para Bedelía
    if minutos_ahora < minutos_ini - tol:
        estado = "INVALIDO"
        motivo = "Fuera de horario (temprano)"
        valido = False
    elif minutos_ahora > minutos_fin:
        estado = "INVALIDO"
        motivo = "Fuera de horario (tarde)"
        valido = False
    elif minutos_ahora > minutos_ini + tol:
        estado = "TARDE"
        motivo = None
        valido = True
    else:
        estado = "EN_CONSULTA"   # o "Presente"
        motivo = None
        valido = True

    # 6) Registrar asistencia
    asistencia = Asistencia(
        docente_id=docente_id,
        turno_id=turno.id,
        punto_id=turno.punto_id_plan,  # Bedelía usa el punto planificado
        estado=EstadoAsistencia[estado],
        motivo_id=None,
        motivo_texto=motivo,
        valido=valido,
        qr_nonce=data.nonce,
        fuente=FuenteLectura.CAMARA, 
        ts_lectura_utc=datetime.utcnow(),
    )

    db.add(asistencia)
    db.commit()
    db.refresh(asistencia)

    return {
        "ok": valido,
        "docente_id": docente_id,
        "turno_id": turno.id,
        "estado": estado,
        "motivo": motivo,
    }

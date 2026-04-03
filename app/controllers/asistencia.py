from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, time, timedelta, timezone
import pytz  # si usás tz
from app.web.deps import get_db
from app.models.asistencia import Asistencia, EstadoAsistencia, FuenteLectura
from app.models.turno import Turno, EstadoTurno
from app.models.credencial import Credencial
from app.models.docente import Docente
from app.models.punto import Punto
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import SessionLocal

router = APIRouter(prefix="/asistencias", tags=["asistencias"])

class RegistroQR(BaseModel):
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

def cerrar_turnos_vencidos():
    db: Session = SessionLocal()
    try:
        ARG = pytz.timezone("America/Argentina/Buenos_Aires")

        ahora_utc = datetime.now(timezone.utc)
        ahora_ar  = ahora_utc.astimezone(ARG)
        dia = ahora_ar.isoweekday()

        turnos = db.query(Turno).filter(
            Turno.activo == True,
            Turno.dia_semana == dia
        ).all()

        for turno in turnos:

            # hora fin + tolerancia
            fin_local = ARG.localize(
                datetime.combine(ahora_ar.date(), turno.hora_fin)
            ) + timedelta(minutes=turno.tolerancia_min or 0)

            fin_utc = fin_local.astimezone(timezone.utc)

            # turno aun no terminó
            if ahora_utc < fin_utc:
                continue

            # inicio del día
            inicio_local = ARG.localize(datetime.combine(ahora_ar.date(), time(0, 0)))
            inicio_utc   = inicio_local.astimezone(timezone.utc)

            # traer asistencias del turno HOY
            asistencias = db.query(Asistencia).filter(
                Asistencia.turno_id == turno.id,
                Asistencia.ts_lectura_utc >= inicio_utc
            ).all()

            # =============================
            # 🔥 1) SI EXISTE ALGUNA ASISTENCIA → NO CREAR AUTOMÁTICO
            # =============================
            if len(asistencias) > 0:
                # cerrar solo si está en curso
                if turno.estado != EstadoTurno.FINALIZADO:
                    turno.estado = EstadoTurno.FINALIZADO
                    db.add(turno)
                continue

            # =============================
            # 🔥 2) SI NO EXISTE NINGUNA ASISTENCIA → 1 AUSENTE
            # =============================
            nueva = Asistencia(
                docente_id=turno.docente_id,
                turno_id=turno.id,
                punto_id=turno.punto_id_plan,
                credencial_id=None,
                ts_lectura_utc=ahora_utc,
                estado=EstadoAsistencia.AUSENTE,
                motivo_texto="Ausente (cierre automático)",
                valido=False,
                qr_nonce="-",
                fuente=FuenteLectura.CAMARA,
            )
            db.add(nueva)

            turno.estado = EstadoTurno.FINALIZADO
            db.add(turno)

        db.commit()

    except Exception as e:
        print("[scheduler] Error:", e)
        db.rollback()
    finally:
        db.close()

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, time, timedelta, timezone
import pytz
from app.web.deps import get_db
from app.models.asistencia import Asistencia, EstadoAsistencia, FuenteLectura
from app.models.turno_base import TurnoBase
from app.models.turno_instancia import TurnoInstancia, EstadoTurnoInstancia

from app.models.turno_excepcion import TurnoExcepcion
from app.models.credencial import Credencial
from pydantic import BaseModel
from app.db.session import SessionLocal

router = APIRouter(prefix="/asistencias", tags=["asistencias"])
ARG = pytz.timezone("America/Argentina/Buenos_Aires")

class RegistroQR(BaseModel):
    punto_id: int
    credencial_id: int
    qr_nonce: str
    fuente: FuenteLectura

#Registro de asistencias
@router.post("/registrar")
def registrar_asistencia(data: RegistroQR, db: Session = Depends(get_db)):

    ahora_ar = datetime.now(ARG)
    ahora_utc = ahora_ar.astimezone(pytz.UTC)

    cred = db.query(Credencial).filter(Credencial.id == data.credencial_id).first()
    if not cred:
        raise HTTPException(400, "Credencial inválida")

    docente = cred.docente
    if not docente:
        raise HTTPException(400, "Docente inválido")

    dia = ahora_ar.isoweekday()

    turnos = db.query(TurnoBase).filter(
        TurnoBase.docente_id == docente.id,
        TurnoBase.activo == True,
        TurnoBase.dia_semana == dia
    ).all()

    turno_base = None
    estado = EstadoAsistencia.AUSENTE
    motivo = "Fuera de horario"

    for t in turnos:
        ini = t.hora_inicio
        fin = (datetime.combine(ahora_ar.date(), t.hora_fin) +
               timedelta(minutes=t.tolerancia_min or 0)).time()

        if ini <= ahora_ar.time() <= fin:
            turno_base = t

            if ahora_ar.time() <= t.hora_inicio:
                estado = EstadoAsistencia.PRESENTE
            else:
                estado = EstadoAsistencia.TARDE

            motivo = None
            break

    ti = None

    if turno_base:
        ti = db.query(TurnoInstancia).filter(
            TurnoInstancia.turno_base_id == turno_base.id,
            TurnoInstancia.fecha == ahora_ar.date()
        ).first()

        if not ti:
            ti = TurnoInstancia(
                turno_base_id=turno_base.id,
                fecha=ahora_ar.date(),
                estado=EstadoTurnoInstancia.EN_CURSO,
                punto_id_real=data.punto_id,
                inicio_real_utc=ahora_utc
            )
            db.add(ti)
            db.flush()

    # evitar duplicado real
    if ti:
        existente = db.query(Asistencia).filter(
            Asistencia.turno_instancia_id == ti.id,
            Asistencia.valido == 1
        ).first()

        if existente:
            return {
                "ok": True,
                "mensaje": "Ya registrada",
                "estado": existente.estado.value
            }

    asistencia = Asistencia(
        docente_id=docente.id,
        punto_id=data.punto_id,
        turno_instancia_id=ti.id if ti else None,
        credencial_id=cred.id,
        ts_lectura_utc=ahora_utc,
        estado=estado,
        motivo_texto=motivo,
        fuente=data.fuente,
        qr_nonce=data.qr_nonce,
        valido=1
    )

    db.add(asistencia)

    if ti and estado in (EstadoAsistencia.PRESENTE, EstadoAsistencia.TARDE):
        ti.estado = EstadoTurnoInstancia.EN_CURSO
        db.add(ti)

    db.commit()

    return {
        "ok": True,
        "estado": asistencia.estado.value,
        "turno_instancia_id": asistencia.turno_instancia_id,
        "docente": f"{docente.nombre} {docente.apellido}",
        "hora_lectura_local": ahora_ar.strftime("%H:%M"),
    }

#Cerrar automaticamente turno no asistidos
def cerrar_turnos_vencidos():
    db: Session = SessionLocal()
    try:
        ahora_ar = datetime.now(ARG)
        hoy = ahora_ar.date()
        dia = ahora_ar.isoweekday()

        turnos = db.query(TurnoBase).filter(
            TurnoBase.activo == True,
            TurnoBase.dia_semana == dia
        ).all()

        for turno in turnos:

            # calcular fin REAL
            fin = turno.hora_fin
            tol = turno.tolerancia_min or 0

            ahora_min = ahora_ar.hour * 60 + ahora_ar.minute
            fin_min = fin.hour * 60 + fin.minute + tol

            if ahora_min <= fin_min:
                continue

            # INSTANCIA
            ti = db.query(TurnoInstancia).filter(
                TurnoInstancia.turno_base_id == turno.id,
                TurnoInstancia.fecha == hoy
            ).first()

            if not ti:
                ti = TurnoInstancia(
                    turno_base_id=turno.id,
                    fecha=hoy,
                    estado=EstadoTurnoInstancia.FINALIZADO,
                    punto_id_real=turno.punto_id_plan,
                    fin_real_utc=datetime.utcnow()
                )
                db.add(ti)
                db.flush()

            # FINALIZAR TURNO SIEMPRE
            if ti.estado != EstadoTurnoInstancia.FINALIZADO:
                ti.estado = EstadoTurnoInstancia.FINALIZADO

                if not ti.fin_real_utc:
                    ti.fin_real_utc = datetime.utcnow()

                db.add(ti)

            # si ya marcó (presente/tarde) → NO crear AUSENTE
            ya_marcado = db.query(Asistencia).filter(
                Asistencia.turno_instancia_id == ti.id,
                Asistencia.valido == 1
            ).first()

            if ya_marcado:
                continue 

            # evitar duplicar AUSENTE
            ya_ausente = db.query(Asistencia).filter(
                Asistencia.turno_instancia_id == ti.id,
                Asistencia.estado == EstadoAsistencia.AUSENTE
            ).first()

            if ya_ausente:
                continue  

            # CREAR AUSENTE
            nueva = Asistencia(
                docente_id=turno.docente_id,
                punto_id=turno.punto_id_plan,
                turno_instancia_id=ti.id,
                ts_lectura_utc=datetime.utcnow(),
                estado=EstadoAsistencia.AUSENTE,
                motivo_texto="Ausente automático",
                valido=0,
                qr_nonce="-",
                fuente=FuenteLectura.CAMARA
            )

            db.add(nueva)

        db.commit()

    except Exception as e:
        print("[scheduler] Error:", e)
        db.rollback()
    finally:
        db.close()


def generar_instancias_del_dia():
    db: Session = SessionLocal()
    hoy = datetime.now(ARG).date()
    dia = hoy.isoweekday()

    turnos = db.query(TurnoBase).filter(
        TurnoBase.dia_semana == dia,
        TurnoBase.activo == True
    ).all()

    for turno in turnos:
        existe = db.query(TurnoInstancia).filter(
            TurnoInstancia.turno_base_id == turno.id,
            TurnoInstancia.fecha == hoy
        ).first()

        if not existe:
            nueva = TurnoInstancia(
                turno_base_id=turno.id,
                fecha=hoy,
                estado=EstadoTurnoInstancia.PROGRAMADO,
                punto_id_real=turno.punto_id_plan
            )
            db.add(nueva)

    db.commit()
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.turno_repo import turno_repo
from app.schemas.turno import TurnoCreate, TurnoUpdate
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.turno_base import TurnoBase
from app.models.turno_instancia import TurnoInstancia, EstadoTurnoInstancia
from app.models.asistencia import EstadoAsistencia, Asistencia, FuenteLectura
import pytz
from datetime import datetime

class TurnoService:

    def create(self, db: Session, data: TurnoCreate):

        if data.hora_fin <= data.hora_inicio:
            raise HTTPException(400, "La hora de fin debe ser mayor que la hora de inicio.")

        overlap = (
            db.query(TurnoBase)
            .filter(
                TurnoBase.docente_id == data.docente_id,
                TurnoBase.dia_semana == data.dia_semana,
                TurnoBase.hora_inicio < data.hora_fin,
                TurnoBase.hora_fin > data.hora_inicio
            )
            .first()
        )

        if overlap:
            raise HTTPException(400, "Este horario se superpone con otro turno existente.")

        obj = TurnoBase(**data.model_dump())
        db.add(obj)
        db.flush()  # 🔥 necesario para obtener obj.id

        # CREAR INSTANCIA + ASISTENCIA (solo hoy)

        ARG = pytz.timezone("America/Argentina/Buenos_Aires")

        ahora_ar = datetime.now(ARG)
        dia_hoy = ahora_ar.isoweekday()

        if data.dia_semana == dia_hoy:

            ahora_min = ahora_ar.hour * 60 + ahora_ar.minute
            ini_min = data.hora_inicio.hour * 60 + data.hora_inicio.minute
            fin_min = data.hora_fin.hour * 60 + data.hora_fin.minute

            # 🔹 estado del turno
            if ahora_min < ini_min:
                estado_turno = EstadoTurnoInstancia.PROGRAMADO

            elif ini_min <= ahora_min < fin_min:
                estado_turno = EstadoTurnoInstancia.EN_CURSO

            else:
                estado_turno = EstadoTurnoInstancia.FINALIZADO

            # crear instancia
            ti = TurnoInstancia(
                turno_base_id=obj.id,
                fecha=ahora_ar.date(),
                estado=estado_turno,
                punto_id_real=obj.punto_id_plan
            )

            if estado_turno == EstadoTurnoInstancia.EN_CURSO:
                ti.inicio_real_utc = datetime.utcnow()

            if estado_turno == EstadoTurnoInstancia.FINALIZADO:
                ti.fin_real_utc = datetime.utcnow()

            db.add(ti)
            db.flush()

        # 🔹 guardar todo
        db.commit()
        db.refresh(obj)

        return obj

def update(self, db: Session, id: int, data: TurnoUpdate):
    
    from datetime import datetime
    ARG = pytz.timezone("America/Argentina/Buenos_Aires")

    obj = db.query(TurnoBase).filter(TurnoBase.id == id).first()
    if not obj:
        raise HTTPException(404, "No existe")

    ahora_ar = datetime.now(ARG)
    hoy = ahora_ar.date()

    # 🔹 VALIDACIÓN: no modificar si ya pasó o está en curso
    ti = db.query(TurnoInstancia).filter(
        TurnoInstancia.turno_base_id == obj.id,
        TurnoInstancia.fecha == hoy
    ).first()

    if ti and ti.estado in [EstadoTurnoInstancia.EN_CURSO, EstadoTurnoInstancia.FINALIZADO]:
        raise HTTPException(400, "No se puede modificar un turno en curso o finalizado")

    # 🔹 VALIDACIONES
    hora_inicio = data.hora_inicio or obj.hora_inicio
    hora_fin = data.hora_fin or obj.hora_fin
    dia = data.dia_semana or obj.dia_semana

    if hora_fin <= hora_inicio:
        raise HTTPException(400, "Hora fin inválida")

    overlap = db.query(TurnoBase).filter(
        TurnoBase.docente_id == obj.docente_id,
        TurnoBase.dia_semana == dia,
        TurnoBase.hora_inicio < hora_fin,
        TurnoBase.hora_fin > hora_inicio,
        TurnoBase.id != obj.id
    ).first()

    if overlap:
        raise HTTPException(400, "Se superpone")

    # 🔹 UPDATE
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)

    db.flush()

    # CALCULAR ESTADO DE INSTANCIA
    ahora_min = ahora_ar.hour * 60 + ahora_ar.minute
    ini_min = hora_inicio.hour * 60 + hora_inicio.minute
    fin_min = hora_fin.hour * 60 + hora_fin.minute

    if ahora_min < ini_min:
        estado = EstadoTurnoInstancia.PROGRAMADO
    elif ini_min <= ahora_min < fin_min:
        estado = EstadoTurnoInstancia.EN_CURSO
    else:
        estado = EstadoTurnoInstancia.FINALIZADO

    if not ti:
        ti = TurnoInstancia(
            turno_base_id=obj.id,
            fecha=hoy,
            estado=estado,
            punto_id_real=obj.punto_id_plan
        )
        db.add(ti)
    else:
        ti.estado = estado

    if estado == EstadoTurnoInstancia.EN_CURSO and not ti.inicio_real_utc:
        ti.inicio_real_utc = datetime.utcnow()

    if estado == EstadoTurnoInstancia.FINALIZADO and not ti.fin_real_utc:
        ti.fin_real_utc = datetime.utcnow()

    db.add(ti)

    db.commit()
    db.refresh(obj)

    return obj
turno_service = TurnoService()

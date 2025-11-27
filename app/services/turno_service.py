from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.turno_repo import turno_repo
from app.schemas.turno import TurnoCreate, TurnoUpdate
from app.models.turno import Turno

class TurnoService:

    def list(self, db: Session):
        return turno_repo.list(db)

    def create(self, db: Session, data: TurnoCreate):

        # --- Validación 1: fin > inicio ---
        if data.hora_fin <= data.hora_inicio:
            raise HTTPException(400, "La hora de fin debe ser mayor que la hora de inicio.")

        # --- Validación 2: solapamiento ---
        overlap = (
            db.query(Turno)
            .filter(
                Turno.docente_id == data.docente_id,
                Turno.dia_semana == data.dia_semana,
                Turno.hora_inicio < data.hora_fin,
                Turno.hora_fin > data.hora_inicio
            )
            .first()
        )

        if overlap:
            raise HTTPException(400, "Este horario se superpone con otro turno existente.")

        return turno_repo.create(db, data)

    def update(self, db: Session, id: int, data: TurnoUpdate):
        obj = turno_repo.get(db, id)
        if not obj:
            return None

        # determinar horarios según inputs
        hora_inicio = data.hora_inicio or obj.hora_inicio
        hora_fin = data.hora_fin or obj.hora_fin

        # --- Validación 1: fin > inicio ---
        if hora_fin <= hora_inicio:
            raise HTTPException(400, "La hora de fin debe ser mayor que la hora de inicio.")

        # --- Validación 2: solapamiento ---
        overlap = (
            db.query(Turno)
            .filter(
                Turno.docente_id == obj.docente_id,
                Turno.dia_semana == (data.dia_semana or obj.dia_semana),
                Turno.hora_inicio < hora_fin,
                Turno.hora_fin > hora_inicio,
                Turno.id != obj.id
            )
            .first()
        )

        if overlap:
            raise HTTPException(400, "Este turno se superpone con otro existente.")

        return turno_repo.update(db, obj, data)

    def remove(self, db: Session, id: int):
        return turno_repo.remove(db, id)

turno_service = TurnoService()

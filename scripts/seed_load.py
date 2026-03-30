# scripts/seed_load.py
from datetime import time
from datetime import datetime
import pytz

from app.db.session import SessionLocal
from app.models.docente import Docente
from app.models.materia import Materia
from app.models.punto import Punto
from app.models.turno_base import TurnoBase
from app.models.turno_instancia import TurnoInstancia, EstadoTurnoInstancia

ARG_TZ = pytz.timezone("America/Argentina/Buenos_Aires")


def get_or_create_docente(db, legajo: str, **kwargs) -> Docente:
    obj = db.query(Docente).filter(Docente.legajo == legajo).first()
    if obj:
        return obj
    obj = Docente(legajo=legajo, **kwargs)
    db.add(obj)
    db.flush()  # obtiene id sin commit
    return obj


def get_or_create_materia(db, codigo: str, **kwargs) -> Materia:
    obj = db.query(Materia).filter(Materia.codigo == codigo).first()
    if obj:
        return obj
    obj = Materia(codigo=codigo, **kwargs)
    db.add(obj)
    db.flush()
    return obj


def get_or_create_punto(db, codigo: str, **kwargs) -> Punto:
    obj = db.query(Punto).filter(Punto.codigo == codigo).first()
    if obj:
        return obj
    obj = Punto(codigo=codigo, **kwargs)
    db.add(obj)
    db.flush()
    return obj


def get_or_create_turno_base(db, docente_id: int, materia_id: int, punto_id_plan: int,
                            dia_semana: int, hora_inicio: time, hora_fin: time,
                            tolerancia_min: int = 10, activo: bool = True) -> TurnoBase:
    obj = (
        db.query(TurnoBase)
        .filter(
            TurnoBase.docente_id == docente_id,
            TurnoBase.materia_id == materia_id,
            TurnoBase.punto_id_plan == punto_id_plan,
            TurnoBase.dia_semana == dia_semana,
            TurnoBase.hora_inicio == hora_inicio,
            TurnoBase.hora_fin == hora_fin,
        )
        .first()
    )
    if obj:
        return obj

    obj = TurnoBase(
        docente_id=docente_id,
        materia_id=materia_id,
        punto_id_plan=punto_id_plan,
        dia_semana=dia_semana,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        tolerancia_min=tolerancia_min,
        activo=activo,
    )
    db.add(obj)
    db.flush()
    return obj


def ensure_instancia_hoy(db, turno_base: TurnoBase):
    """
    Opcional: crea una instancia para HOY (Argentina) si:
    - hoy coincide con el dia_semana del turno_base
    - no existe ya la instancia
    """
    hoy_ar = datetime.now(ARG_TZ).date()
    dow = hoy_ar.isoweekday()

    if turno_base.dia_semana != dow:
        return

    existe = (
        db.query(TurnoInstancia)
        .filter(
            TurnoInstancia.turno_base_id == turno_base.id,
            TurnoInstancia.fecha == hoy_ar,
        )
        .first()
    )
    if existe:
        return

    inst = TurnoInstancia(
        turno_base_id=turno_base.id,
        fecha=hoy_ar,
        estado=EstadoTurnoInstancia.PROGRAMADO,
        punto_id_real=turno_base.punto_id_plan,  # por defecto el planificado
        inicio_real_utc=None,
        fin_real_utc=None,
    )
    db.add(inst)


def main():
    db = SessionLocal()
    try:
        # -------------------------
        # 1) Datos base
        # -------------------------
        ana = get_or_create_docente(
            db,
            legajo="D001",
            apellido="Pérez",
            nombre="Ana",
            email="ana.perez@utn.edu",
            depto="Sistemas",
            activo=True,
        )
        luis = get_or_create_docente(
            db,
            legajo="D002",
            apellido="Gómez",
            nombre="Luis",
            email="luis.gomez@utn.edu",
            depto="Sistemas",
            activo=True,
        )

        prog = get_or_create_materia(db, codigo="MAT101", nombre="Programación I", activo=True)
        bdd  = get_or_create_materia(db, codigo="MAT202", nombre="Bases de Datos", activo=True)

        a205 = get_or_create_punto(db, codigo="PISO_2_AULA_205", etiqueta="Piso 2 - Aula 205", aula="205", activo=True)
        bibl = get_or_create_punto(db, codigo="BIBLIOTECA", etiqueta="Biblioteca", aula="Hall", activo=True)

        # -------------------------
        # 2) Turnos Base
        # -------------------------
        # Ej: jueves 18–20 (dia_semana=4) Ana - Programación - Aula 205
        t1 = get_or_create_turno_base(
            db,
            docente_id=ana.id,
            materia_id=prog.id,
            punto_id_plan=a205.id,
            dia_semana=4,
            hora_inicio=time(18, 0),
            hora_fin=time(20, 0),
            tolerancia_min=10,
            activo=True,
        )

        # Ejemplo extra (opcional): martes 16–18 Luis - BDD - Biblioteca
        t2 = get_or_create_turno_base(
            db,
            docente_id=luis.id,
            materia_id=bdd.id,
            punto_id_plan=bibl.id,
            dia_semana=2,
            hora_inicio=time(16, 0),
            hora_fin=time(18, 0),
            tolerancia_min=10,
            activo=True,
        )

        # -------------------------
        # 3) Instancias de HOY (opcional)
        # -------------------------
        ensure_instancia_hoy(db, t1)
        ensure_instancia_hoy(db, t2)

        db.commit()
        print("Seeds cargados OK.")

        # -------------------------
        # 4) Usuarios para login
        # -------------------------
        from app.models.usuario import Usuario
        from app.security.auth import hash_password

        def get_or_create_usuario(db, email, password, rol):
            obj = db.query(Usuario).filter(Usuario.email == email).first()
            if obj:
                return obj
            obj = Usuario(
                email=email,
                password_hash=hash_password(password),
                rol=rol,
                activo=True,
            )
            db.add(obj)
            db.flush()
            return obj

        # Usuario bedelía
        get_or_create_usuario(db, "bedelia@utn.edu",    "bedelia123", "BEDELIA")

        # Usuarios docentes (mismo email que los docentes ya creados)
        get_or_create_usuario(db, "ana.perez@utn.edu",  "$2b$12$xW5HJPdPao1fO3ggj7lcn.qQ0Ak4h1TnjEBEji0geo71auqEeGTc.", "DOCENTE")
        get_or_create_usuario(db, "luis.gomez@utn.edu", "$2b$12$xW5HJPdPao1fO3ggj7lcn.qQ0Ak4h1TnjEBEji0geo71auqEeGTc.", "DOCENTE")

    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

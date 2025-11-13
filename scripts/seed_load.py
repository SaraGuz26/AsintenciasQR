# scripts/seed_load.py
from datetime import time
from app.db.session import SessionLocal
from app.models.docente import Docente
from app.models.materia import Materia
from app.models.punto import Punto
from app.models.turno import Turno

db = SessionLocal()
try:
    # Docentes
    if not db.query(Docente).first():
        d1 = Docente(legajo="D001", apellido="Pérez", nombre="Ana", email="ana.perez@utn.edu", depto="Sistemas", activo=True)
        d2 = Docente(legajo="D002", apellido="Gómez", nombre="Luis", email="luis.gomez@utn.edu", depto="Sistemas", activo=True)
        db.add_all([d1, d2])

    # Materias
    if not db.query(Materia).first():
        m1 = Materia(codigo="MAT101", nombre="Programación I", activo=True)
        m2 = Materia(codigo="MAT202", nombre="Bases de Datos", activo=True)
        db.add_all([m1, m2])

    # Puntos
    if not db.query(Punto).first():
        p1 = Punto(codigo="PISO_2_AULA_205", etiqueta="Piso 2 - Aula 205", aula="205", activo=True)
        p2 = Punto(codigo="BIBLIOTECA", etiqueta="Biblioteca", aula="Hall", activo=True)
        db.add_all([p1, p2])

    db.commit()

    # Turno simple (jueves 18–20) para Ana en A-205
    ana = db.query(Docente).filter_by(legajo="D001").first()
    prog = db.query(Materia).filter_by(codigo="MAT101").first()
    a205 = db.query(Punto).filter_by(codigo="PISO_2_AULA_205").first()

    if ana and prog and a205 and not db.query(Turno).first():
        t1 = Turno(
            docente_id=ana.id, materia_id=prog.id, punto_id_plan=a205.id,
            dia_semana=4, hora_inicio=time(18,0), hora_fin=time(20,0),
            tolerancia_min=10, activo=True
        )
        db.add(t1)
        db.commit()

    print("Seeds cargados.")
finally:
    db.close()

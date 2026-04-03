from app.db.session import SessionLocal
from app.models.materia import Materia

db = SessionLocal()

materias = [
    ("FIS01", "Física"),
    ("MAT01", "Matemática"),
    ("ECO01", "Economía"),
    ("PRO01", "Programación"),
    ("ALG01", "Algoritmos"),
    ("EST01", "Estadística"),
    ("ING01", "Inglés Técnico"),
    ("SO01", "Sistemas Operativos"),
    ("BD01", "Base de Datos")
]

for codigo, nombre in materias:
    m = Materia(codigo=codigo, nombre=nombre)
    db.add(m)

db.commit()
db.close()

print("Materias cargadas correctamente.")

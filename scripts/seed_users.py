# scripts/seed_users.py
from app.db.session import SessionLocal
from app.models.usuario import Usuario
from app.security.auth import hash_password

db = SessionLocal()
try:
    if not db.query(Usuario).filter_by(email="bedelia@utn.edu").first():
        u = Usuario(
            email="bedelia@utn.edu",
            password_hash=hash_password("bedelia123"),
            rol="bedelia",
            activo=True
        )
        db.add(u)
        db.commit()
        print("Usuario bedelia creado.")
    else:
        print("Usuario bedelia ya existe.")
finally:
    db.close()

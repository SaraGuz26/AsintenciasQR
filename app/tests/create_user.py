from passlib.context import CryptContext
from app.db.session import SessionLocal
from app.models.usuario import Usuario  

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user():
    db = SessionLocal()

    email = input("Email: ")
    password = input("Contraseña: ")
    rol = input("Rol (bedelia/docente): ")

    # verificar si ya existe
    existing = db.query(Usuario).filter(Usuario.email == email).first()
    if existing:
        print("⚠️ El usuario ya existe")
        return

    # hash
    password_hash = pwd_context.hash(password)

    user = Usuario(
        email=email,
        password_hash=password_hash,
        rol=rol,
        activo=True
    )

    db.add(Usuario)
    db.commit()
    db.close()

    print("✅ Usuario creado correctamente")


if __name__ == "__main__":
    create_user()
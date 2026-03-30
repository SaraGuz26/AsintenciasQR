from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

while True:
    password = input("Contraseña (enter para salir): ")
    if not password:
        break

    hashed = pwd_context.hash(password)
    print(f"\nHash:\n{hashed}\n")
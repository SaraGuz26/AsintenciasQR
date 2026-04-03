from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",  # explícito y compatible
    # por defecto passlib trunca >72 bytes (no lanza error)
)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(subject: str, extra: Optional[Dict[str, Any]] = None, expires_minutes: int = None) -> str:
    s = get_settings()
    to_encode = {"sub": subject}
    if extra:
        to_encode.update(extra)
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes or s.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, s.SECRET_KEY, algorithm=s.ALGORITHM)

def decode_token(token: str) -> dict:
    s = get_settings()
    return jwt.decode(token, s.SECRET_KEY, algorithms=[s.ALGORITHM])

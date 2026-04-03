from pydantic import BaseModel
from datetime import datetime

class CredencialCreate(BaseModel):
    docente_id: int

class CredencialOut(BaseModel):
    id: int
    docente_id: int
    nonce_actual: str | None = None
    emitido_en: datetime | None = None
    revocado_en: datetime | None = None
    motivo_revoc: str | None = None
    activo: bool
    class Config: from_attributes = True

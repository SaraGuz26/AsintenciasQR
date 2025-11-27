from pydantic import BaseModel
from datetime import datetime

class ScanIn(BaseModel):
    qr_payload: str   # contenido del QR (JSON base64 o dict firmado)
    punto_id: int
    timestamp: datetime | None = None  # opcional; servidor usa now si falta

class ScanOut(BaseModel):
    ok: bool
    estado: str
    docente_id: int | None = None
    turno_id: int | None = None
    motivo: str | None = None

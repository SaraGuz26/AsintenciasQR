import hmac, json, base64
from hashlib import sha256
from datetime import datetime, timezone, time as dtime
from sqlalchemy.orm import Session
from app.repositories.credencial_repo import credencial_repo
from app.repositories.turno_repo import turno_repo
from app.repositories.asistencia_repo import asistencia_repo
from app.models.asistencia import Asistencia

def _verify_signature(payload: dict, nonce: str) -> bool:
    """QR payload esperado: {"docente_id": int, "exp": int, "sig": "base64"} firmado con HMAC(nonce)."""
    sig = payload.get("sig")
    if not sig: return False
    body = {k: payload[k] for k in payload.keys() if k != "sig"}
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
    digest = hmac.new(nonce.encode(), raw, sha256).digest()
    expected = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return hmac.compare_digest(sig, expected)

def _within(h: datetime, ini: dtime, fin: dtime, tol_min: int) -> tuple[bool, str]:
    t = h.time()
    # ventana con tolerancia al IN; salida estricta simple
    if t < ini and (ini.hour*60+ini.minute)-(t.hour*60+t.minute) > tol_min:
        return False, "Fuera de horario (temprano)"
    if t > fin:
        return False, "Fuera de horario (tarde)"
    if t > ini and (t.hour*60+t.minute)-(ini.hour*60+ini.minute) > tol_min:
        return True, "Tarde"
    return True, "EnConsulta"

class ScanService:
    def validar(self, db: Session, qr_payload: str, punto_id: int, ts: datetime | None):
        now = ts or datetime.now(timezone.utc)

        # 1) parse payload
        try:
            data = json.loads(qr_payload) if not qr_payload.startswith("{") else json.loads(qr_payload)
        except Exception:
            return False, None, None, "QR inválido (parse)"

        docente_id = int(data.get("docente_id", 0))
        if not docente_id:
            return False, None, None, "QR sin docente"

        # 2) credencial activa y firma
        cred = credencial_repo.activa_de_docente(db, docente_id)
        if not cred or not cred.nonce_actual:
            return False, None, None, "Sin credencial activa"
        if not _verify_signature(data, cred.nonce_actual):
            return False, None, None, "Firma inválida"

        # 3) turno vigente (aplicando excepción)
        t = turno_repo.vigente_para(db, docente_id, now)
        if not t:
            return False, None, None, "Sin turno planificado hoy"
        turno, exc = t

        # punto efectivo y horario efectivo
        punto_ok = (exc.punto_id_alt if exc and exc.punto_id_alt else turno.punto_id_plan)
        ini = (exc.hora_inicio_alt if exc and exc.hora_inicio_alt else turno.hora_inicio)
        fin = (exc.hora_fin_alt if exc and exc.hora_fin_alt else turno.hora_fin)

        if punto_ok != punto_id:
            estado = "Reubicado"
            motivo = "Lectura en otro punto"
            valido = False
        else:
            ok, etiqueta = _within(now, ini, fin, turno.tolerancia_min or 0)
            estado = etiqueta if ok else "Invalido"
            motivo = None if ok else etiqueta
            valido = ok

        # 4) persistir asistencia
        a = Asistencia(
            docente_id=docente_id,
            turno_id=turno.id,
            punto_id=punto_id,
            estado=estado,
            motivo=motivo,
            valido=valido,
            fuente="lector"  # o "camara"
        )
        db.add(a); db.commit(); db.refresh(a)
        return True if valido else False, docente_id, turno.id, estado

scan_service = ScanService()

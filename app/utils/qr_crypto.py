# app/utils/qr_crypto.py
import base64, hmac, hashlib, json

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def b64url_decode(s: str) -> bytes:
    # repone '=' si faltan
    pad = (-len(s)) % 4
    return base64.urlsafe_b64decode(s + ("=" * pad))

def sign_compact(json_payload: dict, secret: str) -> str:
    raw = json.dumps(json_payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    b64 = b64url_encode(raw)
    sig = hmac.new(secret.encode("utf-8"), b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"

def verify_compact(qr_text: str, secret: str) -> dict:
    try:
        b64, sig_hex = qr_text.split(".", 1)
    except ValueError:
        raise ValueError("Formato de QR inválido")
    calc = hmac.new(secret.encode("utf-8"), b64.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, sig_hex):
        raise ValueError("Firma HMAC inválida")
    raw = b64url_decode(b64)
    payload = json.loads(raw.decode("utf-8"))
    return payload

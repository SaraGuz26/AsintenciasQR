import hmac, hashlib

def hmac_sha256_hex(secret: bytes, payload: str) -> str:
    return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
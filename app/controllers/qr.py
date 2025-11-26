# app/controllers/qr.py
from fastapi import APIRouter, Query, Response, HTTPException
from time import time
import qrcode
from qrcode.constants import ERROR_CORRECT_M
from io import BytesIO

from app.core.config import get_settings
from app.utils.qr_crypto import sign_compact

router = APIRouter(prefix="/qr", tags=["qr"])

@router.get("/emitir.png")
def emitir_qr_png(
    docente_id: int = Query(...),
    credencial_id: int = Query(...),
    nonce: str = Query(...),
    exp_min: int = Query(60)
):
    """
    Genera PNG del QR firmado (compact) para escanear con el celular.
    NOTA: 'nonce' debe coincidir con credencial.nonce_actual en la DB.
    """
    s = get_settings()

    payload = {
        "docente_id": docente_id,
        "credencial_id": credencial_id,
        "nonce": nonce,
        "exp": int(time()) + exp_min * 60
    }
    qr_text = sign_compact(payload, s.SECRET_QR)

    try:
        qr_img = qrcode.make(qr_text, error_correction=ERROR_CORRECT_M, box_size=10, border=2)
        buf = BytesIO()
        qr_img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo generar el PNG: {e}")

    headers = {"Content-Disposition": f'inline; filename="qr_{docente_id}_{credencial_id}.png"'}
    return Response(content=png_bytes, media_type="image/png", headers=headers)

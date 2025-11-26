# scripts/emit_qr.py
import argparse
import os
from time import time
from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from app.core.config import get_settings
from app.utils.qr_crypto import sign_compact

def generar_qr_png(qr_text: str, out_path: str):
    img = qrcode.make(
        qr_text,
        error_correction=ERROR_CORRECT_M,  # robusto sin excederse de tamaño
        box_size=10,                       # tamaño del “módulo”
        border=2                           # margen blanco
    )
    Path(os.path.dirname(out_path)).mkdir(parents=True, exist_ok=True)
    img.save(out_path)

def main():
    parser = argparse.ArgumentParser(description="Emitir QR firmado (PNG) para credencial de docente")
    parser.add_argument("--docente-id", type=int, required=True)
    parser.add_argument("--credencial-id", type=int, required=True)
    parser.add_argument("--nonce", type=str, required=True, help="Debe coincidir con credencial.nonce_actual")
    parser.add_argument("--exp-min", type=int, default=60, help="Minutos hasta expiración (default 60)")
    parser.add_argument("--out", type=str, default=None, help="Ruta de salida PNG (opcional)")

    args = parser.parse_args()
    s = get_settings()

    payload = {
        "docente_id": args.docente_id,
        "credencial_id": args.credencial_id,
        "nonce": args.nonce,                        # Debe coincidir con la DB
        "exp": int(time()) + args.exp_min * 60      # epoch seconds
    }

    qr_text = sign_compact(payload, s.SECRET_QR)

    # nombre por defecto si no se indicó --out
    out_path = args.out or f"generated/qr_{args.docente_id}_{args.credencial_id}.png"

    generar_qr_png(qr_text, out_path)

    print("=== QR EMITIDO ===")
    print(f"Archivo PNG : {out_path}")
    print(f"QR (texto)  : {qr_text}")
    print(f"Payload     : {payload}")
    print("Listo. Escaneá el PNG con el celu y envía qr_text al endpoint /scan/validar.")

if __name__ == "__main__":
    main()

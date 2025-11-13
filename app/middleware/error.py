from fastapi import Request
from fastapi.responses import JSONResponse

async def http_error_handler(request: Request, exc: Exception):
    # Podés enriquecer con logging; por ahora devolvemos genérico
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "path": request.url.path},
    )

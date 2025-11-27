import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import get_settings
from app.controllers import health as health_router
from app.controllers import docente as docente_router
from app.controllers import punto as punto_router
from app.controllers import turno as turno_router
from app.controllers import turno_excepcion as turno_exc_router
from app.controllers import credencial as cred_router
from app.controllers import scan as scan_router
from app.controllers import publico as publico_router
from app.controllers import bedelia as bedelia_router
from app.controllers import materia as materias_router
from app.controllers import auth as auth_router
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.error import http_error_handler
from pathlib import Path


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title="AsistenciasQR-API", version="0.1.0")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request-ID
    app.add_middleware(RequestIdMiddleware)

    # Routers
    app.include_router(health_router.router)
    app.include_router(docente_router.router)
    app.include_router(punto_router.router)
    app.include_router(turno_router.router)
    app.include_router(turno_exc_router.router)
    app.include_router(cred_router.router)
    app.include_router(scan_router.router)
    app.include_router(publico_router.router)
    app.include_router(bedelia_router.router)
    app.include_router(auth_router.router)
    app.include_router(materias_router.router)
    

    # Error handler genérico
    app.add_exception_handler(Exception, http_error_handler)

    # Montar frontend estático:
    #  - /            -> sirve index.html
    #  - /bedelia    -> sirve bedelia.html (ver más abajo)
    FRONT_DIR = Path(__file__).resolve().parents[2] / "frontend"
    app.mount("/frontend", StaticFiles(directory=str(FRONT_DIR), html=True), name="frontend")

    return app

app = create_app()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import get_settings
from app.controllers import health as health_router
from app.controllers import docente as docentes_router
from app.controllers import publico as publico_router
from app.controllers import bedelia as bedelia_router
from app.controllers import qr as qr_router
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.error import http_error_handler

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
    app.include_router(docentes_router.router)
    app.include_router(publico_router.router)
    app.include_router(bedelia_router.router)
    app.include_router(qr_router.router)

    # Error handler genérico
    app.add_exception_handler(Exception, http_error_handler)

    # Montar frontend estático:
    #  - /            -> sirve index.html
    #  - /bedelia    -> sirve bedelia.html (ver más abajo)
    app.mount("/", StaticFiles(directory="frontend/public", html=True), name="frontend")

    return app

app = create_app()

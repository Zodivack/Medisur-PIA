import logging
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from app.config import load_settings
from app.metrics import APP_INFO, REQUEST_COUNT, REQUEST_DURATION

DATOS_SEMILLA = [
    ("Elemento de prueba", "Dato de relleno numero uno"),
    ("Otro elemento", "Informacion sin importancia"),
    ("Registro de ejemplo", "Texto generico para la demostracion"),
]


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class Item(BaseModel):
    id: int
    name: str
    description: str


class ItemStore:
    def __init__(self):
        self._items = []
        self._next_id = 1
        self._lock = threading.Lock()

    def list_items(self):
        with self._lock:
            return list(self._items)

    def add_item(self, name, description):
        with self._lock:
            item = {
                "id": self._next_id,
                "name": name,
                "description": description,
            }
            self._next_id += 1
            self._items.append(item)
            return item


def obtener_endpoint(request):
    ruta = request.scope.get("route")
    if ruta is None:
        return "no_encontrada"
    return ruta.path


def create_app(settings=None):
    if settings is None:
        settings = load_settings()

    logging.basicConfig(level=settings.log_level)
    logger = logging.getLogger(settings.app_name)

    store = ItemStore()

    @asynccontextmanager
    async def lifespan(app):
        if settings.seed_items:
            for nombre, descripcion in DATOS_SEMILLA:
                store.add_item(nombre, descripcion)
        app.state.ready = True
        logger.info("Servicio listo, version %s", settings.app_version)
        yield
        app.state.ready = False

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.state.ready = False

    APP_INFO.labels(
        version=settings.app_version,
        commit=settings.git_sha,
        build_date=settings.build_date,
    ).set(1)

    @app.middleware("http")
    async def medir_peticiones(request: Request, call_next):
        inicio = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duracion = time.perf_counter() - inicio
            endpoint = obtener_endpoint(request)
            REQUEST_COUNT.labels(request.method, endpoint, str(status_code)).inc()
            REQUEST_DURATION.labels(request.method, endpoint).observe(duracion)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "MediSur API"}

    @app.get("/ready")
    def ready(response: Response):
        if not app.state.ready:
            response.status_code = 503
            return {"status": "not_ready"}
        return {"status": "ready"}

    @app.get("/version")
    def version():
        return {
            "version": settings.app_version,
            "commit": settings.git_sha,
            "build_date": settings.build_date,
        }

    @app.get("/metrics")
    def metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/api/items", response_model=list[Item])
    def listar_items():
        return store.list_items()

    @app.post("/api/items", response_model=Item, status_code=201)
    def crear_item(datos: ItemCreate):
        return store.add_item(datos.name, datos.description)

    return app


app = create_app()
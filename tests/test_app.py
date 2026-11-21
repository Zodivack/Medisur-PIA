import pytest
from fastapi.testclient import TestClient

from app.config import Settings, load_settings
from app.main import create_app


def crear_settings(seed_items=True):
    return Settings(
        app_name="test-api",
        app_version="1.2.3",
        git_sha="abc1234",
        build_date="2026-01-01T00:00:00Z",
        log_level="INFO",
        seed_items=seed_items,
    )


@pytest.fixture
def client():
    app = create_app(crear_settings())
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client_vacio():
    app = create_app(crear_settings(seed_items=False))
    with TestClient(app) as test_client:
        yield test_client


def test_health_devuelve_ok(client):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {
    "status": "ok",
    "service": "MediSur API"
    }


def test_ready_devuelve_ok_cuando_arranco(client):
    respuesta = client.get("/ready")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ready"}


def test_ready_devuelve_503_antes_de_arrancar():
    app = create_app(crear_settings())
    cliente_sin_arranque = TestClient(app)
    respuesta = cliente_sin_arranque.get("/ready")
    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "not_ready"}


def test_version_devuelve_valores_configurados(client):
    respuesta = client.get("/version")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["version"] == "1.2.3"
    assert datos["commit"] == "abc1234"
    assert datos["build_date"] == "2026-01-01T00:00:00Z"


def test_listar_items_devuelve_datos_semilla(client):
    respuesta = client.get("/api/items")
    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 3


def test_listar_items_vacio_sin_semilla(client_vacio):
    respuesta = client_vacio.get("/api/items")
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_crear_item_devuelve_201(client_vacio):
    cuerpo = {"name": "Nuevo", "description": "Texto cualquiera"}
    respuesta = client_vacio.post("/api/items", json=cuerpo)
    assert respuesta.status_code == 201
    datos = respuesta.json()
    assert datos["id"] == 1
    assert datos["name"] == "Nuevo"
    assert datos["description"] == "Texto cualquiera"


def test_crear_item_aparece_en_la_lista(client_vacio):
    client_vacio.post("/api/items", json={"name": "Uno"})
    client_vacio.post("/api/items", json={"name": "Dos"})
    respuesta = client_vacio.get("/api/items")
    nombres = []
    for item in respuesta.json():
        nombres.append(item["name"])
    assert nombres == ["Uno", "Dos"]


def test_crear_item_sin_nombre_devuelve_422(client_vacio):
    respuesta = client_vacio.post("/api/items", json={"description": "Sin nombre"})
    assert respuesta.status_code == 422


def test_crear_item_con_nombre_vacio_devuelve_422(client_vacio):
    respuesta = client_vacio.post("/api/items", json={"name": ""})
    assert respuesta.status_code == 422


def test_metrics_expone_contador_y_duracion(client):
    client.get("/health")
    respuesta = client.get("/metrics")
    assert respuesta.status_code == 200
    texto = respuesta.text
    assert "http_requests_total" in texto
    assert 'endpoint="/health"' in texto
    assert 'status_code="200"' in texto
    assert "http_request_duration_seconds_bucket" in texto


def test_metrics_expone_version_desplegada(client):
    respuesta = client.get("/metrics")
    assert 'app_info{build_date="2026-01-01T00:00:00Z",commit="abc1234",version="1.2.3"}' in respuesta.text


def test_ruta_inexistente_devuelve_404_y_se_cuenta(client):
    respuesta = client.get("/no-existe")
    assert respuesta.status_code == 404
    metricas = client.get("/metrics").text
    assert 'endpoint="no_encontrada"' in metricas
    assert 'status_code="404"' in metricas


def test_load_settings_lee_variables_de_entorno(monkeypatch):
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    monkeypatch.setenv("GIT_SHA", "deadbee")
    monkeypatch.setenv("BUILD_DATE", "2026-02-02T10:00:00Z")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("SEED_ITEMS", "false")
    settings = load_settings()
    assert settings.app_version == "9.9.9"
    assert settings.git_sha == "deadbee"
    assert settings.build_date == "2026-02-02T10:00:00Z"
    assert settings.log_level == "DEBUG"
    assert settings.seed_items is False


def test_load_settings_usa_valores_por_defecto(monkeypatch):
    monkeypatch.delenv("APP_VERSION", raising=False)
    monkeypatch.delenv("SEED_ITEMS", raising=False)
    settings = load_settings()
    assert settings.app_version == "desconocida"
    assert settings.seed_items is True
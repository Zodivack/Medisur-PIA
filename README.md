# Medisur-PIA

Servicio piloto desarrollado con FastAPI para el proyecto de automatización CI/CD sobre Kubernetes de MediSur, S.A. de C.V.

## Tecnologías

- Python
- FastAPI
- Uvicorn
- Prometheus Client
- Pydantic
- Pytest
- Pytest-Cov

## Estructura del proyecto

```text
Medisur-PIA/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   └── metrics.py
│
├── tests/
│   └── test_app.py
│
├── Dockerfile
├── .dockerignore
├── .gitignore
├── pytest.ini
├── requirements.txt
└── requirements-dev.txt
```

## Instalación local

Crear un entorno virtual:

```powershell
py -m venv .venv
```

Instalar dependencias de ejecución:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Instalar dependencias de desarrollo:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

## Variables de entorno

| Variable | Valor predeterminado | Descripción |
|---|---|---|
| APP_NAME | devops-api | Nombre de la aplicación |
| APP_VERSION | 1.0 | Versión desplegada |
| GIT_SHA | desconocido | SHA del commit |
| BUILD_DATE | 21-11-26 | Fecha de construcción |
| LOG_LEVEL | INFO | Nivel de registro |
| SEED_ITEMS | true | Cargar registros iniciales |
| PORT | 8000 | Puerto de ejecución en Docker |

## Ejecutar la aplicación

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Endpoints

| Método | Endpoint | Descripción |
|---|---|---|
| GET | /health | Estado del proceso |
| GET | /ready | Disponibilidad del servicio |
| GET | /version | Versión y SHA del commit |
| GET | /metrics | Métricas de Prometheus |
| GET | /api/items | Consultar registros |
| POST | /api/items | Crear un registro |

## Pruebas unitarias

Ejecutar las pruebas:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Generar cobertura:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing --cov-report=xml
```

La cobertura mínima requerida por el proyecto es del 60 %.

## Construcción de Docker

La imagen utiliza un Dockerfile multietapa y ejecuta la aplicación con un usuario sin privilegios.

Las variables de versión, SHA y fecha se inyectan durante la construcción.

## Seguridad

No almacenar contraseñas, tokens, llaves privadas ni archivos de configuración sensibles en el repositorio.
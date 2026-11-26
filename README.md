# MediSur PIA — API y plataforma CI/CD

Servicio piloto desarrollado con **FastAPI** para el proyecto de automatización de integración y entrega continua (CI/CD) de MediSur, S.A. de C.V. La aplicación se empaqueta en Docker, se publica en GitHub Container Registry (GHCR) y se despliega en Kubernetes (k3s).

La versión indicada en el archivo `VERSION` del repositorio es la referencia utilizada por Jenkins para construir la siguiente imagen. La versión que responde la aplicación en ejecución puede ser distinta temporalmente después de realizar un rollback de Kubernetes.

## Funcionalidades

- API REST para consultar y crear registros de ejemplo.
- Endpoints de salud, disponibilidad y metadatos de compilación.
- Métricas HTTP compatibles con Prometheus.
- Pruebas automatizadas con Pytest y reporte de cobertura.
- Análisis estático con SonarQube y validación mediante Quality Gate.
- Construcción de imagen Docker multietapa y publicación en GHCR.
- Despliegue automatizado en Kubernetes mediante Jenkins.
- Monitoreo de infraestructura, aplicación y recursos de Kubernetes con Prometheus y Grafana.

> **Alcance de los datos:** los registros de `/api/items` se almacenan en memoria dentro del proceso. No se utiliza una base de datos; los registros creados se pierden al reiniciar o reemplazar el contenedor. `SEED_ITEMS=true` carga tres registros de ejemplo al iniciar la aplicación.

## Tecnologías

| Área | Tecnologías |
|---|---|
| API | Python, FastAPI, Uvicorn, Pydantic |
| Métricas | Prometheus Client |
| Pruebas | Pytest, Pytest-Cov, HTTPX |
| Calidad | SonarQube, Quality Gate |
| CI/CD | Jenkins, GitHub Webhooks |
| Contenedores | Docker, GitHub Container Registry (GHCR) |
| Orquestación | Kubernetes (k3s) |
| Monitoreo | Prometheus, Grafana, Node Exporter, kube-state-metrics |

## Estructura del repositorio

```text
Medisur-PIA/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   └── metrics.py
├── tests/
│   └── test_app.py
├── k8s/
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── ingress.yaml
│   ├── jenkins-rbac.yaml
│   ├── namespace.yaml
│   └── service.yaml
├── .dockerignore
├── .gitignore
├── Dockerfile
├── Jenkinsfile
├── VERSION
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
└── sonar-project.properties
```

## Requisitos

- Python 3.12 para ejecutar la aplicación y las pruebas.
- Docker para construir y ejecutar la imagen localmente.
- Para el flujo completo de entrega: acceso al repositorio de GitHub, Jenkins, SonarQube, GHCR y al clúster k3s.

## Instalación y ejecución local (PowerShell)

Entrar al directorio del repositorio y crear el entorno virtual:

```powershell
py -m venv .venv
```

Instalar las dependencias de desarrollo (este archivo también instala las dependencias de ejecución):

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

También se pueden instalar únicamente las dependencias de ejecución:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Iniciar la API localmente:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Con el servidor activo, la documentación interactiva de FastAPI está disponible en `http://127.0.0.1:8000/docs` y la documentación alternativa en `http://127.0.0.1:8000/redoc`.

## Variables de entorno

| Variable | Valor predeterminado en la aplicación/imagen | Descripción |
|---|---|---|
| `APP_NAME` | `devops-api` en la aplicación; `MediSur API` en el ConfigMap de Kubernetes | Nombre del servicio y del logger. |
| `APP_VERSION` | `desconocida` | Versión de la aplicación. Jenkins la obtiene del archivo `VERSION` y la inyecta al construir la imagen. |
| `GIT_SHA` | `desconocido` | SHA completo del commit utilizado para construir la imagen. |
| `BUILD_DATE` | `desconocida` | Fecha y hora UTC de construcción en formato ISO 8601. |
| `LOG_LEVEL` | `INFO` | Nivel de registro de la aplicación. |
| `SEED_ITEMS` | `true` | Carga los tres registros de ejemplo cuando la aplicación inicia. Acepta `true/false`, `1/0`, `yes/no` y `si`. |
| `PORT` | `8000` en la imagen Docker | Puerto en el que Uvicorn escucha dentro del contenedor. |

El archivo `VERSION` contiene la versión que Jenkins utiliza para el siguiente despliegue. Actualmente, el valor registrado en el repositorio es `1.0.1`. Un rollback de Kubernetes cambia la imagen en ejecución, pero no modifica este archivo en GitHub.

## Endpoints de la API

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/health` | Comprueba que el proceso de la API responde. |
| `GET` | `/ready` | Indica si la aplicación terminó su inicialización. Devuelve HTTP 503 mientras no esté lista. |
| `GET` | `/version` | Devuelve la versión, el SHA del commit y la fecha de construcción. |
| `GET` | `/metrics` | Expone métricas en formato Prometheus. |
| `GET` | `/api/items` | Consulta los registros de ejemplo y los registros creados durante la ejecución actual. |
| `POST` | `/api/items` | Crea un registro y devuelve HTTP 201. |

### Ejemplo de solicitud para crear un registro

```http
POST /api/items
Content-Type: application/json

{
  "name": "Registro de ejemplo",
  "description": "Elemento creado mediante la API"
}
```

El campo `name` es obligatorio y admite entre 1 y 100 caracteres. `description` es opcional, tiene un valor predeterminado vacío y admite hasta 500 caracteres.

### Métricas expuestas

- `http_requests_total`: contador de peticiones HTTP, etiquetado por método, endpoint y código de respuesta.
- `http_request_duration_seconds`: histograma de duración de las peticiones, etiquetado por método y endpoint.
- `app_info`: indicador con etiquetas de versión, SHA del commit y fecha de construcción.

## Pruebas automatizadas y cobertura

Ejecutar las pruebas:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Ejecutar las pruebas en modo compacto:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

La configuración de `pytest.ini` genera automáticamente el reporte de cobertura en terminal y el archivo `coverage.xml`. También establece una cobertura mínima requerida del **60 %**; una ejecución por debajo de ese porcentaje falla.

Para solicitar explícitamente los reportes:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing --cov-report=xml
```

## Construcción y ejecución con Docker

El `Dockerfile` utiliza dos etapas basadas en `python:3.12-slim`: una etapa para instalar dependencias y otra para ejecutar la aplicación. La imagen final utiliza el usuario sin privilegios `10001`.

Construir una imagen local:

```powershell
docker build -t medisur-api:local .
```

Ejecutar el contenedor:

```powershell
docker run --rm -p 8000:8000 medisur-api:local
```

Consultar la API local desde otra terminal:

```powershell
curl.exe -fsS http://127.0.0.1:8000/health
curl.exe -fsS http://127.0.0.1:8000/ready
curl.exe -fsS http://127.0.0.1:8000/version
```

Para una imagen de despliegue, Jenkins proporciona durante la construcción los argumentos `APP_VERSION`, `GIT_SHA` y `BUILD_DATE`; por ello, la respuesta de `/version` identifica exactamente la compilación desplegada.

## Integración y entrega continua (Jenkins)

El trabajo utilizado es `MediSur-Pipeline`. El `Jenkinsfile` define el siguiente flujo:

1. **Checkout:** descarga la revisión de Git configurada en el trabajo.
2. **Pruebas y cobertura:** ejecuta Pytest dentro de un contenedor `python:3.12-slim`, genera `coverage.xml` y el reporte JUnit `reports/pytest.xml`.
3. **Análisis SonarQube:** ejecuta SonarScanner usando `sonar-project.properties`.
4. **Quality Gate:** espera el resultado de SonarQube. Si el resultado no es aprobado, Jenkins detiene el pipeline y no continúa con la construcción ni el despliegue.
5. **Validación de Kubernetes:** comprueba el acceso al namespace `medisur` y el permiso para actualizar el Deployment.
6. **Metadatos:** lee la versión de `VERSION`, obtiene el SHA del commit y genera la fecha UTC.
7. **Construcción Docker:** construye la imagen y verifica que el usuario configurado sea `10001`.
8. **Publicación GHCR:** publica dos etiquetas de la misma imagen.
9. **Despliegue y pruebas de humo:** actualiza la imagen del Deployment, espera el rollout y valida `/health`, `/ready` y `/version`, incluida la coincidencia de versión y SHA. Si falla el despliegue o una prueba de humo después de aplicar la nueva imagen, el pipeline intenta restaurar la revisión anterior.

El trabajo utiliza el webhook de GitHub para detectar cambios en la rama configurada en Jenkins. Las credenciales de GitHub, GHCR y Kubernetes se guardan en Jenkins Credentials; no se escriben en el repositorio.

## Publicación de imágenes en GHCR

Las imágenes se publican en:

`ghcr.io/zodivack/medisur-api`

Jenkins genera dos etiquetas por compilación:

- `ghcr.io/zodivack/medisur-api:<VERSION>-<SHA_CORTO>`
- `ghcr.io/zodivack/medisur-api:<SHA_CORTO>`

Por ejemplo, para la versión `1.0.1` y un SHA corto `abcdef0`:

```text
ghcr.io/zodivack/medisur-api:1.0.1-abcdef0
ghcr.io/zodivack/medisur-api:abcdef0
```

Paquete del proyecto: <https://github.com/Zodivack/Medisur-PIA/pkgs/container/medisur-api>

## Despliegue en Kubernetes (k3s)

Los manifiestos se encuentran en `k8s/` y definen:

- Namespace: `medisur`.
- Deployment: `medisur-api`, con dos réplicas.
- Estrategia de actualización: `RollingUpdate`, con `maxSurge: 1` y `maxUnavailable: 0`.
- Service: `ClusterIP`, puerto 80 hacia el puerto 8000 del contenedor.
- Ingress: clase `traefik`, que dirige las solicitudes al Service `medisur-api`.
- ConfigMap: configura el nombre de la aplicación, el nivel de logs, la carga de datos de ejemplo y el puerto.
- RBAC: manifiesto para los permisos que requiere Jenkins en Kubernetes.

El contenedor utiliza controles de seguridad: ejecución como usuario no root `10001`, `allowPrivilegeEscalation: false`, eliminación de capacidades Linux y perfil seccomp `RuntimeDefault`. El Deployment define probes de inicio, salud y disponibilidad, además de solicitudes y límites de CPU y memoria.

**Actualización de imagen:** el pipeline de Jenkins actualiza el Deployment mediante `kubectl set image` con la etiqueta generada para el commit. Antes de aplicar manualmente `k8s/deployment.yaml`, se debe comprobar que el campo `image` tenga la etiqueta que se desea desplegar; un manifiesto con una etiqueta anterior puede reemplazar la imagen que Jenkins dejó activa.

Para consultar el estado desde la VM que administra k3s:

```bash
sudo k3s kubectl get deployments,pods,services,ingress -n medisur
```

Para consultar la imagen que utiliza el Deployment:

```bash
sudo k3s kubectl get deployment medisur-api -n medisur \
  -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

## Monitoreo

La infraestructura y la aplicación se monitorean mediante Prometheus y Grafana:

- **Node Exporter:** recopila métricas de CPU, memoria, disco y red de las máquinas virtuales.
- **kube-state-metrics:** expone el estado de los recursos de Kubernetes, como Deployments, réplicas y Pods.
- **Prometheus:** recopila métricas de los exporters, de Kubernetes y del endpoint `/metrics` de MediSur API.
- **Grafana:** presenta los tableros `MediSur - Infraestructura` y `MediSur - Aplicación y Kubernetes`.

Se configuraron alertas para uso de disco superior al 80 %, más de tres reinicios de contenedor en diez minutos y réplicas disponibles inferiores a las deseadas en el Deployment.

## Seguridad

- No almacenar contraseñas, tokens, llaves privadas, kubeconfig ni archivos de configuración sensibles en el repositorio.
- Mantener credenciales y tokens en el almacén de credenciales de Jenkins.
- Ejecutar la imagen y los Pods con usuario no privilegiado.
- No publicar puertos administrativos de Jenkins, SonarQube, Prometheus o Grafana sin controles de acceso adecuados.

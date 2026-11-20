from prometheus_client import Counter, Gauge, Histogram

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total de peticiones HTTP por endpoint y codigo de respuesta",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Duracion de las peticiones HTTP en segundos",
    ["method", "endpoint"],
)

APP_INFO = Gauge(
    "app_info",
    "Informacion de la version desplegada",
    ["version", "commit", "build_date"],
)
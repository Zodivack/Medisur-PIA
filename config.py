import os
from dataclasses import dataclass


def leer_booleano(nombre, por_defecto):
    valor = os.getenv(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in ("1", "true", "yes", "si")


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    git_sha: str
    build_date: str
    log_level: str
    seed_items: bool


def load_settings():
    return Settings(
        app_name=os.getenv("APP_NAME", "devops-api"),
        app_version=os.getenv("APP_VERSION", "desconocida"),
        git_sha=os.getenv("GIT_SHA", "desconocido"),
        build_date=os.getenv("BUILD_DATE", "desconocida"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        seed_items=leer_booleano("SEED_ITEMS", True),
    )
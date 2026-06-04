"""Observabilidad: logs estructurados (JSON) y métricas Prometheus.

- `setup_observability(app, service_name)` configura el logging raíz en formato
  JSON (timestamp, nivel, logger, servicio, mensaje) y expone `/metrics` con las
  métricas HTTP estándar (latencia, conteo y códigos por endpoint).
"""
import logging
import sys

from prometheus_fastapi_instrumentator import Instrumentator
from pythonjsonlogger import jsonlogger


class _ServiceFilter(logging.Filter):
    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self.service
        return True


def _configure_logging(service_name: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(service)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
        )
    )
    handler.addFilter(_ServiceFilter(service_name))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers = [handler]
        lg.propagate = False


def setup_observability(app, service_name: str) -> None:
    _configure_logging(service_name)
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

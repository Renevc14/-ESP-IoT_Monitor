"""Defaults de entorno para importar los módulos sin secretos reales."""
import os

os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key")

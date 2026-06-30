"""Defaults de entorno para importar los módulos sin BD ni secretos reales."""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key")

"""Defaults de entorno para importar los módulos sin BD real."""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

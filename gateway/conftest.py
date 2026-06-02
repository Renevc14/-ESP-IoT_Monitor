"""Test environment defaults so `app.config.Settings` can be imported without
a real database or secrets (unit tests do not touch external services)."""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key-do-not-use-in-prod")

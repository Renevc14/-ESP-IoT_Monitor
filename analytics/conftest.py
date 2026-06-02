"""Test environment defaults so analytics modules import without a real database."""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")

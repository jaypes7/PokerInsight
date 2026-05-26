import os

os.environ.setdefault("APP_ENV", "ci")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:ci@localhost:5432/ci")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

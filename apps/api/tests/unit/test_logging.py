from app.core.config import Settings
from app.observability.logging import configure_logging


def test_configure_logging_accepts_dev_settings() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://postgres:ci@localhost:5432/ci",
        redis_url="redis://localhost:6379/0",
        app_env="ci",
    )

    configure_logging(settings)

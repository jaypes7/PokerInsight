from collections.abc import Callable
from importlib import import_module
from typing import Any, TypeVar

from app.core.config import get_settings

F = TypeVar("F", bound=Callable[..., object])


class _LocalCelery:
    def __init__(self) -> None:
        self.conf: dict[str, Any] = {}

    def task(self, *_args: object, **_kwargs: object) -> Callable[[F], F]:
        def decorator(fn: F) -> F:
            return fn

        return decorator


try:
    Celery = import_module("celery").Celery
except (ImportError, AttributeError):
    celery_app = _LocalCelery()
else:
    settings = get_settings()
    celery_app = Celery(
        "pokerinsight",
        broker=settings.redis_celery_broker,
        backend=settings.redis_celery_result,
        include=["app.worker.tasks"],
    )
    celery_app.conf.update(
        task_queues={
            "parsing": {"exchange": "parsing", "routing_key": "parsing"},
            "stats": {"exchange": "stats", "routing_key": "stats"},
            "email": {"exchange": "email", "routing_key": "email"},
            "billing": {"exchange": "billing", "routing_key": "billing"},
        },
        task_default_queue="parsing",
        task_acks_late=True,
        task_reject_on_worker_lost=True,
    )

import logging
import sys
from collections.abc import Callable

import structlog
from structlog.typing import EventDict, Processor

from app.core.config import Settings


def _service_fields(settings: Settings) -> Processor:
    def add_fields(_logger: logging.Logger, _method_name: str, event_dict: EventDict) -> EventDict:
        event_dict["service"] = "api"
        event_dict["env"] = settings.app_env
        event_dict["version"] = f"{settings.app_version}+{settings.git_sha[:12]}"
        return event_dict

    return add_fields


def configure_logging(settings: Settings) -> None:
    level = logging.getLevelName(settings.app_log_level)
    renderer: Callable[..., object]
    if settings.is_production:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=False)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _service_fields(settings),
            structlog.processors.dict_tracebacks,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

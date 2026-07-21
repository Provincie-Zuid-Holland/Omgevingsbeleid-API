import logging
import os
from typing import Dict, Optional

from azure.monitor.opentelemetry import configure_azure_monitor
from fastapi import Request

logger_name: str = os.getenv("LOG_LOGGER_NAME", "obzh")
logger = logging.getLogger(logger_name)


def init_logging() -> None:
    level_str: str = os.getenv("LOG_LEVEL", "INFO").upper()
    level: int = getattr(logging, level_str, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    applicationinsights_connection_string: str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    if applicationinsights_connection_string:
        configure_azure_monitor(logger_name=logger_name, instrumentation_options={"fastapi": {"enabled": True}})


def log_message(
    message: str, severity: int = logging.INFO, exception: Optional[Exception] = None, request: Optional[Request] = None
) -> None:
    api_env: str = os.getenv("API_ENV", "unknown environment")
    extra: Dict[str, str] = {"api_env": api_env}
    if request:
        extra["request_path"] = request.url.path
        extra["request_method"] = request.method

    match severity:
        case s if s >= logging.ERROR:
            if exception:
                logger.exception(message, exc_info=exception, extra=extra)
            else:
                logger.error(message, extra=extra)
        case s if s >= logging.WARNING:
            logger.warning(message, extra=extra)
        case s if s >= logging.INFO:
            logger.info(message, extra=extra)
        case _:
            logger.debug(message, extra=extra)

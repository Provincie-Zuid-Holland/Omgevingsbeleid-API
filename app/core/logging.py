import logging
import os

from azure.monitor.opentelemetry import configure_azure_monitor


def init_logging() -> None:
    level_str: str = os.getenv("LOG_LEVEL", "INFO").upper()
    level: int = getattr(logging, level_str, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    logger_name: str = os.getenv("LOG_LOGGER_NAME", "obzh")
    logger = logging.getLogger(logger_name)

    applicationinsights_connection_string: str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    logger.info(f"applicationinsights_connection_string: {applicationinsights_connection_string}")
    if applicationinsights_connection_string:
        configure_azure_monitor(logger_name=logger_name)

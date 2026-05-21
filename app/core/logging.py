import logging
import os


def init_logging() -> None:
    level_str: str = os.getenv("LOG_LEVEL", "INFO").upper()
    level: int = getattr(logging, level_str, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

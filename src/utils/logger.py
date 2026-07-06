import logging
from pathlib import Path

from configs.constants import LOG_DIR


def setup_logger(
    logger_name: str = "etl_logger"
) -> logging.Logger:

    """
    Configure application logger.

    Args:
        logger_name:
            Logger identifier

    Returns:
        Configured logger
    """

    LOG_DIR.mkdir(
        exist_ok=True
    )

    log_file = LOG_DIR / "pipeline.log"

    logger = logging.getLogger(
        logger_name
    )

    logger.setLevel(
        logging.INFO
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(
        log_file
    )

    console_handler = logging.StreamHandler()

    file_handler.setFormatter(
        formatter
    )

    console_handler.setFormatter(
        formatter
    )

    if not logger.handlers:

        logger.addHandler(
            file_handler
        )

        logger.addHandler(
            console_handler
        )

    return logger
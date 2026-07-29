import logging
from pathlib import Path

from .settings import LOGS_DIR

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def create_logger(name: str, log_file: Path) -> logging.Logger:
    """Создаёт и настраивает логгер по имени и пути к файлу."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    return logger


def setup_file_readers_logger() -> logging.Logger:
    return create_logger("file_readers", LOGS_DIR / "file_readers.log")


def setup_utils_logger() -> logging.Logger:
    return create_logger("utils", LOGS_DIR / "utils.log")


def setup_views_logger() -> logging.Logger:
    return create_logger("views", LOGS_DIR / "views.log")


def setup_reports_logger() -> logging.Logger:
    return create_logger("reports", LOGS_DIR / "reports.log")


def setup_main_logger() -> logging.Logger:
    return create_logger("main", LOGS_DIR / "main.log")


def setup_services_logger() -> logging.Logger:
    return create_logger("services", LOGS_DIR / "services.log")

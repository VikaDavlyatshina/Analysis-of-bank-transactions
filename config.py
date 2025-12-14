import logging
from pathlib import Path

# Базовые пути
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
USER_SETTINGS = PROJECT_ROOT/ "user_settings.json"
LOGS_DIR = PROJECT_ROOT / "logs"
TEST_LOGS_DIR = PROJECT_ROOT / "tests" / "logs_test"
REPORTS_DIR =  PROJECT_ROOT / "reports"

# Создаём папку reports если её нет
REPORTS_DIR.mkdir(exist_ok=True)


# Создаём папки если их нет
LOGS_DIR.mkdir(exist_ok=True)
TEST_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Пути к файлам данных
EXCEL_FILE = DATA_DIR / "operations.xlsx"

# Стандартный формат логов
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


# ---------- Универсальная функция ----------
def create_logger(name: str, log_file: Path):
    """Создаёт и настраивает логгер по имени и пути к файлу."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


# ---------- Логгеры для основного приложения ----------
def setup_file_readers_logger():
    return create_logger("file_readers", LOGS_DIR / "file_readers.log")

def setup_utils_logger():
    return create_logger("utils", LOGS_DIR / "utils.log")

def setup_views_logger():
    return create_logger("views", LOGS_DIR / "views.log")

def setup_reports_logger():
    return create_logger("reports", LOGS_DIR / "reports.log")

def setup_main_logger():
    return create_logger("views", LOGS_DIR / "main.log")

def setup_services_logger():
    return create_logger("services", LOGS_DIR / "services.log")

# ---------- Логгеры для тестов ----------
def setup_test_file_readers_logger():
    return create_logger("test_file_readers", TEST_LOGS_DIR / "test_file_readers.log")

def setup_test_utils_logger():
    return create_logger("test_utils", TEST_LOGS_DIR / "test_utils.log")

def setup_test_views_logger():
    return create_logger("test_views", TEST_LOGS_DIR / "test_views.log")
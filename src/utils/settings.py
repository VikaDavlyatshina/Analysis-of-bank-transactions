import json
from pathlib import Path
from typing import Any, Dict

from config import setup_utils_logger

logger = setup_utils_logger()


def load_user_settings(file_name: str) -> Dict[str, Any]:
    default_settings = {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]}

    settings_path = Path(file_name)

    if not settings_path.exists():
        logger.warning(f"Файл настроек '{file_name}' не найден. Используем настройки по умолчанию.")
        return default_settings

    try:
        with open(settings_path, "r", encoding="utf-8") as file:
            user_settings = json.load(file)

        if not isinstance(user_settings, dict):
            logger.error(f"Файл '{file_name}' должен содержать словарь (dict), а не {type(user_settings).__name__}")
            return default_settings

        result = default_settings.copy()

        for key in default_settings:
            if key in user_settings:
                result[key] = user_settings[key]
            else:
                logger.info(f"В настройках отсутствует поле '{key}', используем значение по умолчанию")

        logger.info(f"Настройки загружены из файла '{file_name}'")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка JSON в файле '{file_name}': {e}. Используем настройки по умолчанию.")
        return default_settings

    except Exception as e:
        logger.error(f"Неизвестная ошибка при чтении файла '{file_name}': {e}")
        return default_settings


def save_json_directly(data: dict, file_path: Path) -> bool:
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Файл сохранен: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения файла {file_path}: {e}")
        return False

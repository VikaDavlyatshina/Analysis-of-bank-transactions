from datetime import datetime
from typing import Optional

from config import setup_utils_logger

logger = setup_utils_logger()


def get_greeting(now: Optional[datetime] = None) -> str:
    try:
        if now is None:
            now = datetime.now()
        hour = now.hour

        if 5 <= hour < 12:
            return "Доброе утро"
        if 12 <= hour < 17:
            return "Добрый день"
        if 17 <= hour < 22:
            return "Добрый вечер"
        return "Доброй ночи"

    except Exception as e:
        if isinstance(e, (AttributeError, TypeError)):
            logger.error(f"Некорректный объект времени: {e}")
        elif isinstance(e, ValueError):
            logger.error(f"Некорректное значение времени: {e}")
        else:
            logger.exception(f"Неожиданная ошибка при формировании приветствия: {e}")

        return "Добрый день"

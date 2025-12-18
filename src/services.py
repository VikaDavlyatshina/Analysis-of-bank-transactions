import re
from typing import Any, Dict, List

from config import REPORTS_DIR, setup_services_logger
from src.utils import save_report

logger = setup_services_logger()


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """
    Рассчитывает сумму, которую можно отложить в Инвесткопилку за указанный месяц
    """

    logger.info(f"Запуск Инвесткопилки: месяц={month}, лимит={limit}, транзакций={len(transactions)}")

    if limit not in (10, 50, 100):
        logger.warning("Неверный лимит округления")
        raise ValueError("limit должен быть '10', '50' или '100'")

    filtered_transactions: List[Dict[str, Any]] = []
    for transaction in transactions:
        date_str = transaction.get("Дата операции")
        amount = transaction.get("Сумма операции")

        # если дата - не строка
        if not isinstance(date_str, str):
            logger.debug("Дата операции не строка — пропуск")
            continue

        # если дата не с нужным месяцем - пропускаем
        if not date_str.startswith(month):
            continue

        if not isinstance(amount, (int, float)):
            logger.debug("Сумма операции не число — пропуск")
            continue

        # если Сумма операции больше нуля - пропускаем
        if amount >= 0:
            continue

        filtered_transactions.append(transaction)

    logger.info(f"Отфильтровано транзакций: {len(filtered_transactions)}")

    def rounding_diff(value: float) -> float:
        abs_value = abs(value)
        rounded = ((abs_value + limit - 1) // limit) * limit
        diff = rounded - abs_value
        logger.debug(f"Округление: {abs_value} → {rounded}, в копилку: {diff}")
        return diff

    total = sum(rounding_diff(transaction["Сумма операции"]) for transaction in filtered_transactions)

    logger.info(f"Итого в Инвесткопилку: {total:.2f} ₽")
    return float(total)


def simple_search(transactions: List[Dict[str, Any]], search_string: str, reports_dir=REPORTS_DIR) -> Dict[str, Any]:
    """Ищет транзакции по строке в описании и категории"""

    logger.info(f"Простой поиск: строка='{search_string}', транзакций={len(transactions)}")

    if not isinstance(search_string, str) or not search_string.strip():
        return {
            "service": "Простой поиск",
            "status": "empty",
            "search_string": "",
            "found_count": 0,
            "transactions": [],
            "message": "Строка поиска пуста",
        }

    def contains_search_text(transaction: Dict[str, Any]) -> bool:
        try:
            if not isinstance(transaction, dict):
                return False
            desc = transaction.get("Описание", "").lower()
            cat = transaction.get("Категория", "").lower()
            search_lower = search_string.lower()
            return search_lower in desc or search_lower in cat
        except (AttributeError, TypeError):
            logger.debug("Ошибка при обработке транзакции", exc_info=True)
            return False

    result_transactions = list(filter(contains_search_text, transactions))
    result = {
        "service": "Простой поиск",
        "status": "success",
        "search_string": search_string,
        "found_count": len(result_transactions),
        "transactions": result_transactions,
        "message": f"Найдено {len(result_transactions)} транзакций по запросу '{search_string}'",
    }

    save_report(result, filename="simple_search_report.json", reports_dir=reports_dir)
    return result


def find_phone_numbers(transactions: List[Dict[str, Any]], reports_dir=REPORTS_DIR) -> Dict[str, Any]:
    """Ищет транзакции с телефонными номерами в описании"""

    logger.info(f"Поиск телефонов: транзакций={len(transactions)}")

    if not transactions:
        return {
            "service": "Поиск по телефонным номерам",
            "status": "empty",
            "found_count": 0,
            "transactions": [],
            "message": "Нет транзакций для поиска",
        }

    phone_pattern = re.compile(r"(?:\+7|7|8)\s?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", re.IGNORECASE)
    found_transactions = [transaction for transaction in transactions if phone_pattern.search(str(transaction.get("Описание", "")))]

    result = {
        "service": "Поиск по телефонным номерам",
        "status": "success",
        "found_count": len(found_transactions),
        "transactions": found_transactions,
        "message": f"Найдено {len(found_transactions)} транзакций с телефонными номерами",
    }

    save_report(result, filename="find_phone_numbers_report.json", reports_dir=reports_dir)
    return result

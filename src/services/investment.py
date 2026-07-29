from typing import Any, Dict, List

from config import setup_services_logger

logger = setup_services_logger()


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    logger.info(f"Запуск Инвесткопилки: месяц={month}, лимит={limit}, транзакций={len(transactions)}")

    if limit not in (10, 50, 100):
        logger.warning(f"Неверный лимит {limit}. Допустимые значения: 10, 50, 100")
        raise ValueError(f"Неверный лимит {limit}. Допустимые значения: 10, 50, 100")

    filtered_transactions: List[Dict[str, Any]] = []
    for transaction in transactions:
        date_str = transaction.get("Дата операции")
        amount = transaction.get("Сумма операции")

        if not isinstance(date_str, str):
            logger.debug("Дата операции не строка — пропуск")
            continue

        if not date_str.startswith(month):
            continue

        if not isinstance(amount, (int, float)):
            logger.debug("Сумма операции не число — пропуск")
            continue

        if amount >= 0:
            continue

        filtered_transactions.append(transaction)

    logger.info(f"Отфильтровано транзакций: {len(filtered_transactions)}")

    def rounding_diff(value: float) -> float:
        abs_value = abs(value)
        rounded = ((abs_value + limit - 1) // limit) * limit
        diff = rounded - abs_value
        return diff

    total = sum(rounding_diff(transaction["Сумма операции"]) for transaction in filtered_transactions)

    logger.info(f"Итого в Инвесткопилку: {total:.2f} ₽")
    return float(total)

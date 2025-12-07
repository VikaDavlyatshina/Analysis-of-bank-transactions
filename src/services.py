import logging
import re
from typing import Any, Dict, List


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """Рассчитывает сумму для Инвесткопилки на основе округления трат"""

    # 1. Фильтрация транзакций по месяцу и по тратам
    def is_target_month_and_spending(transaction: Dict[str, Any]) -> bool:
        try:
            date_str = transaction.get("Дата операции", "")
            is_correct_month = date_str.startswith(month)
            is_spending = transaction.get("Сумма операции", 0) < 0
            return is_correct_month and is_spending
        except (AttributeError, TypeError):
            return False

    filtered_transactions = filter(is_target_month_and_spending, transactions)

    # 2. Расчет общей суммы через генератор и sum()

    def calculate_rounding(transaction: Dict[str, Any]) -> float:
        """Рассчитывает сумму для копилки от одной транзакции."""
        amount = abs(transaction["Сумма операции"])
        rounded_amount = ((amount + limit - 1) // limit) * limit
        investment = rounded_amount - amount
        return investment

    # Используем генераторное выражение с sum()

    total_investment = sum(calculate_rounding(trans) for trans in filtered_transactions)
    return total_investment


def simple_search(transactions: List[Dict[str, Any]], search_string: str) -> List[Dict[str, Any]]:
    """Ищет транзакции по строке в описании"""

    if not search_string:
        return []

    # Функция - предикат для фильтрации
    def contains_search_text(transaction: Dict[str, Any]) -> bool:
        """Проверяет, содержит ли транзакция искомую сумму"""
        description = transaction.get("Описание", "").lower()
        category = transaction.get("Категория", "").lower()
        search_lower = search_string.lower()

        # Ищем в описании или в категории
        return (search_lower in description) or (search_lower in category)

    # Применяем фильтр и преобразуем в список
    result = list(filter(contains_search_text, transactions))
    return result


def find_phone_numbers(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ищет транзакции по телефонным номерам в описании"""

    if not transactions:
        return []

    found_operations = []

    # Используем регулярное выражение для поиска номеров
    phone_pattern = re.compile(r"(?:\+7|7|8)\s?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", re.IGNORECASE)

    # Перебираем каждую операцию в списке
    for operation in transactions:
        # Получаем описание операции
        description = operation.get("Описание", "")

        if phone_pattern.search(description):
            found_operations.append(operation)

    return found_operations

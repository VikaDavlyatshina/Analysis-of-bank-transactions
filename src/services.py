from config import setup_services_logger
import re
from typing import Any, Dict, List

logger = setup_services_logger()

def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """Рассчитывает сумму для Инвесткопилки на основе округления трат"""

    logger.info(f"Запуск Инвесткопилки: месяц={month}, лимит={limit}, транзакций={len(transactions)}")

    # 1. Фильтрация транзакций по месяцу и по тратам
    def is_target_month_and_spending(transaction: Dict[str, Any]) -> bool:
        try:
            date_str = transaction.get("Дата операции", "")
            is_correct_month = date_str.startswith(month)
            is_spending = transaction.get("Сумма операции", 0) < 0
            return is_correct_month and is_spending
        except (AttributeError, TypeError) as e:
            logger.debug(f"Ошибка фильтрации транзакции: {e}")
            return False

    filtered_transactions = filter(is_target_month_and_spending, transactions)

    # 2. Расчет общей суммы через генератор и sum()

    def calculate_rounding(transaction: Dict[str, Any]) -> float:
        """Рассчитывает сумму для копилки от одной транзакции."""
        try:
            amount = abs(transaction["Сумма операции"])
            rounded_amount = ((amount + limit - 1) // limit) * limit
            investment = rounded_amount - amount
            logger.debug(f"Транзакция: {amount:.2f} → округление: {rounded_amount:.2f}, инвестиция: {investment:.2f}")
            return investment
        except Exception as e:
            logger.warning(f"Ошибка расчета для транзакции: {e}")
            return 0.0

    # Используем генераторное выражение с sum()

    total_investment = sum(calculate_rounding(trans) for trans in filtered_transactions)
    logger.info(f"ИТОГ: сумма для Инвесткопилки = {total_investment:.2f} руб")
    return total_investment


def simple_search(transactions: List[Dict[str, Any]], search_string: str) -> Dict[str, Any]:
    """Ищет транзакции по строке в описании"""

    try:
        logger.info(f"Запуск простого поиска по строке: '{search_string}'")
        logger.info(f"Всего транзакций для поиска: {len(transactions)}")

        if not search_string:
            logger.warning("Пустая строка поиска")
            return {
                "service": "simple_search",
                "status": "empty",
                "search_string": "",
                "found_count": 0,
                "transactions": [],
                 "message": "Строка поиска пуста"
            }

        # Функция - предикат для фильтрации
        def contains_search_text(transaction: Dict[str, Any]) -> bool:
            """Проверяет, содержит ли транзакция искомую сумму"""
            try:
                description = transaction.get("Описание", "").lower()
                category = transaction.get("Категория", "").lower()
                search_lower = search_string.lower()

                found_in_desc = search_lower in description
                found_in_cat = search_lower in category

                if found_in_desc or found_in_cat:
                    logger.debug(f"Найдено в транзакции: описание='{description[:50]}...', категория='{category}'")

                return found_in_desc or found_in_cat
            except Exception as e:
                logger.debug(f"Ошибка проверки транзакции: {e}")
                return False

        # Применяем фильтр и преобразуем в список
        result_transactions = list(filter(contains_search_text, transactions))

        logger.info(f"Поиск завершен: найдено {len(result_transactions)} транзакций")

        return {
        "service": "simple_search",
        "status": "success",
        "search_string": search_string,
        "found_count": len(result_transactions),
        "transactions": result_transactions,
        "message": f"Найдено {len(result_transactions)} транзакций по запросу '{search_string}'"
        }

    except Exception as e:
        logger.error(f"Ошибка в simple_search: {e}")
        return {
            "service": "simple_search",
            "status": "error",
            "error": str(e),
            "found_count": 0,
            "transactions": [],
        }


def find_phone_numbers(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ищет транзакции по телефонным номерам в описании
    """
    try:
        logger.info("Поиск транзакций с телефонными номерами")
        if not transactions:
            logger.warning("Пустой список транзакций")
            return {
                "service": "find_phone_numbers",
                 "status": "empty",
                  "found_count": 0,
                  "transactions": [],
                   "message": "Нет транзакций для поиска"
            }

        found_operations = []

        # Используем регулярное выражение для поиска номеров
        phone_pattern = re.compile(r"(?:\+7|7|8)\s?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", re.IGNORECASE)

        # Перебираем каждую операцию в списке
        for operation in transactions:
          # Получаем описание операции
          description = operation.get("Описание", "")

          if phone_pattern.search(description):
              found_operations.append(operation)

        logger.info(f"Поиск завершен: найдено {len(found_operations)} транзакций с номерами")
        return {
                "service": "find_phone_numbers",
                "status": "success",
                "found_count": len(found_operations),
                "transactions": found_operations,
                 "message": f"Найдено {len(found_operations)} транзакций с телефонными номерами"
            }

    except Exception as e:
        logger.error(f"Ошибка в find_phone_numbers: {e}")
        return {
        "service": "find_phone_numbers",
        "status": "error",
        "error": str(e),
        "found_count": 0,
        "transactions": []
         }

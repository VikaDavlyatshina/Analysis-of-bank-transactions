from config import setup_services_logger, REPORTS_DIR
from src.views import save_report
import re
from typing import Any, Dict, List

logger = setup_services_logger()


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int, reports_dir=REPORTS_DIR) -> float:
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

    # 2. Расчет суммы для копилки от одной транзакции
    def calculate_rounding(transaction: Dict[str, Any]) -> float:
        """Рассчитывает сумму для копилки от одной транзакции."""
        try:
            amount = abs(transaction["Сумма операции"])
            rounded_amount = ((amount + limit - 1) // limit) * limit
            investment = rounded_amount - amount
            logger.debug(f"Транзакция: {amount:.2f} → округление: {rounded_amount:.2f}, инвестиция: {investment:.2f}")
            return float(investment)
        except Exception as e:
            logger.warning(f"Ошибка расчета для транзакции: {e}")
            return 0.0

    # 3. Суммируем все инвестиции и приводим к float
    total_investment = float(sum(calculate_rounding(trans) for trans in filtered_transactions))
    logger.info(f"ИТОГ: сумма для Инвесткопилки = {total_investment:.2f} руб")

    # 4. Сохраняем отчет в JSON
    report_data = {
        "month": month,
        "limit": limit,
        "total_investment": total_investment
    }
    save_report(report_data,
                filename="investment_bank_report.json",
                reports_dir=reports_dir)

    return total_investment


def simple_search(transactions: List[Dict[str, Any]], search_string: str, reports_dir=REPORTS_DIR) -> Dict[str, Any]:
    """Ищет транзакции по строке в описании и категории"""

    if not search_string:
        return {
            "service": "simple_search",
            "status": "empty",
            "search_string": "",
            "found_count": 0,
            "transactions": [],
            "message": "Строка поиска пуста"
        }

    def contains_search_text(transaction: Dict[str, Any]) -> bool:
        try:
            desc = transaction.get("Описание", "").lower()
            cat = transaction.get("Категория", "").lower()
            search_lower = search_string.lower()
            return search_lower in desc or search_lower in cat
        except Exception:
            return False

    result_transactions = list(filter(contains_search_text, transactions))
    result = {
        "service": "simple_search",
        "status": "success",
        "search_string": search_string,
        "found_count": len(result_transactions),
        "transactions": result_transactions,
        "message": f"Найдено {len(result_transactions)} транзакций по запросу '{search_string}'"
    }

    save_report(result, filename="simple_search_report.json", reports_dir=reports_dir)
    return result


def find_phone_numbers(transactions: List[Dict[str, Any]], reports_dir=REPORTS_DIR) -> Dict[str, Any]:
    """Ищет транзакции с телефонными номерами в описании"""

    if not transactions:
        return {
            "service": "find_phone_numbers",
            "status": "empty",
            "found_count": 0,
            "transactions": [],
            "message": "Нет транзакций для поиска"
        }

    phone_pattern = re.compile(r"(?:\+7|7|8)\s?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", re.IGNORECASE)
    found_transactions = [t for t in transactions if phone_pattern.search(t.get("Описание", ""))]

    result = {
        "service": "find_phone_numbers",
        "status": "success",
        "found_count": len(found_transactions),
        "transactions": found_transactions,
        "message": f"Найдено {len(found_transactions)} транзакций с телефонными номерами"
    }

    save_report(result, filename="find_phone_numbers_report.json", reports_dir=reports_dir)
    return result
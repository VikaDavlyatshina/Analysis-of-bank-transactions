import re
from typing import Any, Dict, List, Optional
from config import setup_services_logger
from pathlib import Path
from src.reports import report_to_file

logger = setup_services_logger()


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """
    Рассчитывает сумму, которую можно отложить в Инвесткопилку за указанный месяц
    """

    logger.info(f"Запуск Инвесткопилки: месяц={month}, лимит={limit}, транзакций={len(transactions)}")

    if limit not in (10, 50, 100):
        logger.warning(f"Неверный лимит {limit}. Допустимые значения: 10, 50, 100")
        raise ValueError(f"Неверный лимит {limit}. Допустимые значения: 10, 50, 100")

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
        return diff

    total = sum(rounding_diff(transaction["Сумма операции"]) for transaction in filtered_transactions)

    logger.info(f"Итого в Инвесткопилку: {total:.2f} ₽")
    return float(total)


@report_to_file
def simple_search(
        transactions: List[Dict[str, Any]],
        search_string: str,
        reports_dir: Optional[Path] = None  # Используется декоратором @report_to_file
) -> Dict[str, Any]:
    """
    Простой поиск транзакций по строке.
    Возвращает словарь с результатами поиска.
    """

    if reports_dir:
        logger.debug(f"Директория для сохранения отчета: {reports_dir}")

    if not isinstance(search_string, str) or not search_string.strip():
        return {
            "service": "Простой поиск",
            "status": "success",
            "search_string": "",
            "found_count": 0,
            "transactions": [],
            "message": "Строка поиска пуста",
            "skip_save": True,  # Говорим декоратору не сохранять пустой результат
        }

    search_lower = search_string.lower()

    def contains_search_text(transaction: Dict[str, Any]) -> bool:
        if not isinstance(transaction, dict):
            return False
        desc = str(transaction.get("Описание", "")).lower()
        cat = str(transaction.get("Категория", "")).lower()
        return search_lower in desc or search_lower in cat

    result_transactions: List[Dict[str, Any]] = list(filter(contains_search_text, transactions))

    result = {
        "service": "Простой поиск",
        "status": "success",
        "search_string": search_string,
        "found_count": len(result_transactions),
        "transactions": result_transactions,
        "message": f"Найдено {len(result_transactions)} транзакций по запросу '{search_string}'",
    }

    return result

@report_to_file(filename="find_phone_numbers_report.json")
def find_phone_numbers(
        transactions: List[Dict[str, Any]],
        reports_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Ищет транзакции с телефонными номерами в описании.
    Возвращает словарь с результатами.
    ВАЖНО: сохраняет обратную совместимость с main() через ключ 'found_count'
    """
    if reports_dir:
        logger.debug(f"Директория для сохранения отчета телефонов: {reports_dir}")

    logger.info(f"Поиск телефонов: всего транзакций={len(transactions)}")

    phone_pattern = re.compile(
        r'(?:\+7|7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{2,3}[\s\-]?\d{2}[\s\-]?\d{2}',
        re.IGNORECASE
    )

    found_transactions = []
    total_phones_found = 0

    for t in transactions:
        if not isinstance(t, dict):
            continue

        desc = str(t.get("Описание", ""))
        # Используем findall() для поиска ВСЕХ номеров
        matches = phone_pattern.findall(desc)

        if matches:
            total_phones_found += len(matches)
            logger.debug(f"Найдены номера: '{desc}' → {matches}")

            # Создаем копию транзакции с дополнительной информацией
            t_copy = t.copy()
            t_copy['Найденные_телефоны'] = matches
            t_copy['Количество_найденных_номеров'] = len(matches)

            found_transactions.append(t_copy)

    result = {
        "service": "Поиск по телефонным номерам",
        "status": "success",
        "found_count": len(found_transactions),
        "found_transactions_count": len(found_transactions),  # транзакций с номерами
        "total_phones_found": total_phones_found,  # всего номеров
        "transactions": found_transactions,
        "message": f"Найдено {len(found_transactions)} транзакций с {total_phones_found} телефонными номерами",
    }

    return result
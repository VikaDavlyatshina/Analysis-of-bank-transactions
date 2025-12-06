import datetime
from typing import Any, Dict, List, Optional
from config import setup_views_logger, EXCEL_FILE
from src.file_readers import (
    filter_successful_transactions,
    filter_transactions_by_date_range,
    load_transactions_from_excel,
)
from src.utils import get_currency_rates, get_greeting, get_stock_prices, load_user_settings
from dotenv import load_dotenv
import os

logger = setup_views_logger()


# Загрузка переменных из .env файла
load_dotenv()

API_KEY_Freecurrencyapi = os.getenv("API_KEY_Freecurrencyapi")  # Получение токена API для валют
API_KEY_twelvedata = os.getenv("API_KEY_twelvedata")  # Получение токена API для валют


def get_cards_summary(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Считает статистику по банковским картам:
    - последние 4 цифры карты,
    - total_spent (сумма расходов),
    - cashback = 1 рубль на каждые 100 руб.
    """
    cards_data: Dict[str, Dict[str, Any]] = {}

    for transaction in transactions:
        card_number = transaction.get("Номер карты", "")
        if not isinstance(card_number, str):
            card_number = str(card_number)

        # Берём последние 4 цифры для карт вида "*1234"
        last_digits = card_number[-4:] if card_number and card_number.startswith("*") else "0000"

        amount = transaction.get("Сумма операции", 0.0)
        if not isinstance(amount, (int, float)):
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                amount = 0.0

        # Считаем только траты (отрицательные суммы)
        if amount < 0:
            if last_digits not in cards_data:
                cards_data[last_digits] = {
                    "last_digits": last_digits,
                    "total_spent": 0.0,
                    "cashback": 0.0
                }
            cards_data[last_digits]["total_spent"] += abs(amount)

    # Считаем кешбэк и округляем
    for info in cards_data.values():
        info["total_spent"] = round(info["total_spent"], 2)
        info["cashback"] = round(info["total_spent"] / 100, 2)

    return list(cards_data.values())


def get_top_transactions(transactions: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Возвращает топ N транзакций по абсолютной сумме.
    Формат даты: 'DD.MM.YYYY'
    """
    if not transactions:
        return []

    # Сортируем по абсолютной сумме (убывание)
    sorted_transactions = sorted(
        transactions,
        key=lambda t: abs(t.get("Сумма операции", 0)),
        reverse=True
    )[:limit]

    result = []
    for transaction in sorted_transactions:
        date_obj = transaction.get("Дата операции")
        date_str = ""

        if hasattr(date_obj, "strftime"):
            date_str = date_obj.strftime("%d.%m.%Y")
        elif isinstance(date_obj, str):
            date_str = date_obj

        result.append({
            "date": date_str,
            "amount": round(transaction.get("Сумма операции", 0), 2),
            "category": transaction.get("Категория", "Не указано"),
            "description": transaction.get("Описание", "Не указано"),
        })

    return result


def format_currency_rates(raw_rates: Optional[Dict[str, float]]) -> List[Dict[str, Any]]:
    """Конвертирует словарь курсов в список для JSON"""
    if not raw_rates:
        return []
    return [{"currency": cur, "rate": rate} for cur, rate in raw_rates.items()]


def format_stock_prices(raw_stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Форматирует цены акций для JSON"""
    if not raw_stocks:
        return []
    return [{"stock": stock["stock"], "price": stock["price"]} for stock in raw_stocks]


def generate_financial_report(date_string: str) -> Dict[str, Any]:
    """
    ГЛАВНАЯ ФУНКЦИЯ - создает полный финансовый отчет.
    Принимает дату в формате "YYYY-MM-DD HH:MM:SS"
    Возвращает JSON-совместимый словарь.
    """
    logger.info(f"Генерация отчета для даты: {date_string}")

    # 1. Приветствие
    greeting = get_greeting()

    # 2. Парсим дату и вычисляем период (с начала месяца)
    try:
        target_date = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        month_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        logger.info(f"Период анализа: {month_start.date()} - {target_date.date()}")
    except Exception as e:
        logger.error(f"Ошибка парсинга даты: {e}")
        return {
            "greeting": greeting,
            "cards": [],
            "top_transactions": [],
            "currency_rates": [],
            "stock_prices": []
        }

    # 3. Загружаем настройки пользователя
    user_settings = load_user_settings()
    currencies_to_show = user_settings.get("user_currencies", [])
    stocks_to_show = user_settings.get("user_stocks", [])

    try:
        # ЗАГРУЖАЕМ КАК DATAFRAME
        df = load_transactions_from_excel(EXCEL_FILE)  # передаем путь!

        # ПРЕОБРАЗУЕМ В СПИСОК СЛОВАРЕЙ
        all_transactions_list = df.to_dict('records')

        # ТЕПЕРЬ ФИЛЬТРУЕМ
        filtered_by_date = filter_transactions_by_date_range(
            all_transactions_list, month_start, target_date
        )
        successful_transactions = filter_successful_transactions(filtered_by_date)

        logger.info(f"Транзакций за период: {len(filtered_by_date)}")
        logger.info(f"Успешных транзакций: {len(successful_transactions)}")

        # Для отладки
        if successful_transactions:
            logger.info(f"Пример транзакции: {successful_transactions[0].get('Дата операции')}")

    except Exception as e:
        logger.error(f"Ошибка чтения транзакций: {e}")
        import traceback
        logger.error(traceback.format_exc())
        successful_transactions = []

    # 5. Получаем курсы валют и цены акций
    try:
        currency_rates = get_currency_rates(
            apikey=API_KEY_Freecurrencyapi,
            base_currency="RUB",
            currencies=currencies_to_show)
    except Exception as e:
        logger.error(f"Ошибка получения курсов валют: {e}")
        currency_rates = None

    try:
        stock_prices = get_stock_prices(stocks_to_show)
    except Exception as e:
        logger.error(f"Ошибка получения цен акций: {e}")
        stock_prices = []

    # 6. Считаем статистику
    cards_info = get_cards_summary(successful_transactions)
    top_transactions = get_top_transactions(successful_transactions)

    # 7. Формируем финальный отчет
    report = {
        "greeting": greeting,
        "cards": cards_info,
        "top_transactions": top_transactions,
        "currency_rates": format_currency_rates(currency_rates),
        "stock_prices": format_stock_prices(stock_prices),
    }

    logger.info(f"Отчет готов! Карт: {len(cards_info)}, Топ операций: {len(top_transactions)}")
    return report

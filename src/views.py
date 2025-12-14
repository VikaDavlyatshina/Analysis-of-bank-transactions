from datetime import datetime
from typing import Any, Dict, List, Optional
from config import setup_views_logger, EXCEL_FILE, USER_SETTINGS, REPORTS_DIR
from src.file_readers import load_transactions_from_excel
from src.utils import (get_currency_rates, get_greeting, get_stock_prices, load_user_settings,
                       filter_transactions_by_date, filter_successful_transaction, convert_transactions_to_rub)
from dotenv import load_dotenv
import json
import os
import pandas as pd
logger = setup_views_logger()


# Загрузка переменных из .env файла
load_dotenv()

API_KEY_Freecurrencyapi = os.getenv("API_KEY_Freecurrencyapi")  # Получение токена API для валют
API_KEY_twelvedata = os.getenv("API_KEY_twelvedata")  # Получение токена API для валют


def get_cards_summary(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Считает статистику по банковским картам:
      последние 4 цифры карты,
      total_spent (сумма расходов),
      cashback = 1 рубль на каждые 100 руб.
    """
    if df.empty:
        return []

    # 1. Фильтруем только расходы, отрицательные суммы
    expenses_df =  df[df['Сумма операции'] < 0].copy()

    if expenses_df.empty:
        return []

    # 2. Группируем по номеру карты
    result = []

    for card_number, group in expenses_df.groupby('Номер карты'):
        total_spent = abs(group['Сумма операции'].sum())
        cashback = total_spent * 0.01  # 1% кэшбэк

        card_str = str(card_number)
        last_digits = card_str[-4:]

        result.append({
            'last_digits': last_digits,
            'total_spent': round(total_spent, 2),
            'cashback': round(cashback, 2),
        })

    # 3. Сортируем по тратам
    result.sort(key=lambda x: x['total_spent'], reverse=True)

    return result

def get_top_transactions(df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Возвращает топ N транзакций по абсолютной сумме.
    Формат даты: 'DD.MM.YYYY'
    """

    if df.empty:
        return []

    # 1. Сортируем
    df_sorted = df.copy()
    df_sorted['abs_amount'] = df_sorted['Сумма операции'].abs()
    df_sorted = df_sorted.sort_values('abs_amount', ascending=False)

    # 2. Берём топ и преобразуем в словари
    top_records = df_sorted.head(limit).to_dict('records')

    # 3. Форматируем
    result = []
    for record in top_records:
        # Дата
        date_val = record['Дата операции']
        if isinstance(date_val, pd.Timestamp):
            date_str = date_val.strftime('%d.%m.%Y')
        else:
            date_str = str(date_val) if pd.notna(date_val) else "Нет даты"

        # Сумма
        amount_val = record['Сумма операции']
        if isinstance(amount_val, (int, float)):
            amount = round(float(amount_val), 2)
        else:
            amount = 0.0

        result.append({
            'date': date_str,
            'amount': amount,
            'category': str(record.get('Категория', 'Не указано')),
            'description': str(record.get('Описание', 'Без описания'))[:50]
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
        target_date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
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

    # 3. Загружаем данные
    try:
        # Загружаем как DataFrame
        df = load_transactions_from_excel(EXCEL_FILE)
        logger.info(f"Загружено {len(df)} транзакций")

        # Фильтруем по дате
        df_filtered = filter_transactions_by_date(df, month_start, target_date)
        df_successful = filter_successful_transaction(df_filtered)
        logger.info(f"Транзакций за период: {len(df_filtered)}")
        logger.info(f"Успешных транзакций: {len(df_successful)}")

    except Exception as e:
        logger.error(f"Ошибка обработки транзакций: {e}")
        df_successful = pd.DataFrame() # Пустой DataFrame

    # 4. Загружаем настройки пользователя
    settings = load_user_settings(USER_SETTINGS)

    # 5. Получаем курсы валют
    try:
        currency_rates = get_currency_rates(
            apikey=API_KEY_Freecurrencyapi,
            base_currency="RUB",
            currencies=settings.get("user_currencies", [])
        )
        if currency_rates is None:
            currency_rates = {}

    except Exception as e:
        logger.error(f"Ошибка получения курсов валют: {e}")
        currency_rates = {}

    if not df_successful.empty:
        currencies_in_data = set(df_successful["Валюта операции"].unique())
        missing = currencies_in_data - set(currency_rates.keys()) - {"RUB"}

        if missing:
            logger.warning(f"Нет курсов для валют: {missing}")

    # 6. Получаем акции
    try:
        stock_prices = get_stock_prices(settings.get("user_stocks", []))
    except Exception as e:
        logger.error(f"Ошибка получения цен акций: {e}")
        stock_prices = []

    # 7. Конвертируем в рубли
    df_successful = convert_transactions_to_rub(
        df_successful,
        currency_rates
    )
    logger.info("Суммы операций приведены к RUB")

    # 8. Считаем статистику
    cards_info = get_cards_summary(df_successful)
    top_transactions = get_top_transactions(df_successful)

    # 9. Формируем финальный отчет
    report = {
        "greeting": greeting,
        "cards": cards_info,
        "top_transactions": top_transactions,
        "currency_rates": format_currency_rates(currency_rates),
        "stock_prices": format_stock_prices(stock_prices),
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))

    logger.info(f"Отчет готов! Карт: {len(cards_info)}, Топ операций: {len(top_transactions)}")
    return report

def save_report(report: dict, filename: str = "report.json", reports_dir=REPORTS_DIR):
    """Сохраняет отчет в JSON файл в указанной папке"""
    try:
        reports_dir.mkdir(exist_ok=True)  # на случай, если папки нет
        file_path = reports_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"Отчет сохранен в {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        return False

ex_report = generate_financial_report("2019-10- 12:00:00")
save_report(ex_report, "my_report.json")
generate_financial_report("2019-10-10 12:00:00")
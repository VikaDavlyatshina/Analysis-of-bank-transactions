from datetime import datetime
from typing import Any, Dict, List, Optional
from config import setup_views_logger, EXCEL_FILE, USER_SETTINGS
from src.file_readers import (
    filter_successful_transactions,
    filter_transactions_by_date_range,
    load_transactions_from_excel,
)
from src.utils import get_currency_rates, get_greeting, get_stock_prices, load_user_settings
from dotenv import load_dotenv
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

    # Фильтруем только расходы
    expenses_df =  df[df['Сумма операции'] < 0].copy()

    if expenses_df.empty:
        return []

    # Группируем по последним цифрам карты
    grouped = expenses_df.groupby('Последние цифры карты')['Сумма операции'].agg(
        total_spent=lambda x: round(abs(x.sum()), 2),
        count=lambda x: len(x)
    ).reset_index()

    # Добавляем кэшбэк
    grouped['cashback'] = (grouped['total_spent']* 0.01).round(2)

    # Форматируем результат
    result = []
    for _, row in grouped.iterrows():
        if row['total_spent'] > 0:
            result.append({
                'last_digits': str(row['Последние цифры карты']),
                'total_spent': row['total_spent'],
                'cashback': row['cashback']
            })

    # Сортируем по убыванию трат
    result.sort(key=lambda x: x['total_spent'], reverse=True)

    return result

def get_top_transactions(df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Возвращает топ N транзакций по абсолютной сумме.
    Формат даты: 'DD.MM.YYYY'
    """
    # 1. Проверяем, не пустая ли таблица
    if df.empty:
        return []

    # 2. Создаём копию таблицы
    df_copy = df.copy()

    # 3. Используем колонку с абсолютной суммой
    if 'Абсолютная сумма' not in df_copy.columns:
        # Если по какой-то причине её нет - создаем
        df_copy['Абсолютная сумма'] = df_copy['Сумма операции'].abs()
        logger.warning("Колонка 'Абсолютная сумма' не найдена, создаем временно")

    # 4. Сортируем таблицу по абсолютной сумме(по убыванию)
    # ascending=False - "от большего к меньшему"
    df_sorted = df_copy.sort_values('Абсолютная сумма', ascending=False)

    # 5. Берём первые limit-строк (топ-N транзакций)
    top_count = min(limit, len(df_sorted))

    # 6. Создаём пустой список для результата
    result = []

    # 7. Перебираем топовые транзакции
    for i in range(top_count):
        # Получаем i-ю строку из отсортированной таблицы
        row = df_sorted.iloc[i]

      # 8. Обрабатываем дату
        date_str = ""  # Начинаем с пустой строки
        # Получаем значение даты из строки
        date_val = row['Дата операции']

        # Проверяем, что дата не пустая (не NaN)
        if pd.notna(date_val):  # проверяем "не пустое ли значение"
            if hasattr(date_val, 'strftime'):
                # Форматируем дату как "ДД.ММ.ГГГГ"
                date_str = date_val.strftime("%d.%m.%Y")
            else:
                date_str = str(date_val)

        #  9. Обрабатываем сумму
        amount_val = row['Сумма операции']

        try:
           if pd.isna(amount_val):
               amount = 0.0
           else:
               # Вычисляем значение
               computed_amount  = float(amount_val.item() if hasattr(amount_val, 'item') else amount_val)
               # Округляем и сохраняем
               amount = round(computed_amount, 2)

        except Exception as e:
            logger.warning(f"Не удалось преобразовать сумму {amount_val}: {e}")
            amount = 0.0

        # 10. Формируем запись о транзакции
        transaction_record = {
            'date': date_str,  # Дата в формате "21.12.2021"
            'amount': amount,  # Сумма
            'category': str(row.get('Категория', 'Не указано')),  # Категория
            'description': str(row.get('Описание', 'Не указано'))  # Описание
        }

        # Добавляем запись в результат
        result.append(transaction_record)

    # 11. Возвращаем готовый список транзакций
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

    # 3. Загружаем настройки пользователя
    user_settings = load_user_settings(USER_SETTINGS)
    currencies_to_show = user_settings.get("user_currencies", [])
    stocks_to_show = user_settings.get("user_stocks", [])

    try:
        # Загружаем как DataFrame
        df = load_transactions_from_excel(EXCEL_FILE)

        # Фильтруем по дате
        filtered_df = filter_transactions_by_date_range(df, month_start, target_date)

        # Фильтруем успешные
        successful_df = filter_successful_transactions(filtered_df)

        logger.info(f"Транзакций за период: {len(filtered_df)}")
        logger.info(f"Успешных транзакций: {len(successful_df)}")

    except Exception as e:
        logger.error(f"Ошибка обработки транзакций: {e}")
        import traceback
        logger.error(traceback.format_exc())
        successful_df = pd.DataFrame()

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
    cards_info = get_cards_summary(successful_df)
    top_transactions = get_top_transactions(successful_df)

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

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from dotenv import load_dotenv

from config import USER_SETTINGS, setup_views_logger
from src.utils import (
    convert_transactions_to_rub,
    filter_successful_transaction,
    filter_transactions_by_date,
    get_currency_rates,
    get_greeting,
    get_stock_prices,
    load_user_settings,
)

logger = setup_views_logger()

# Загрузка переменных из .env файла
load_dotenv()
API_KEY_Freecurrencyapi: Optional[str] = os.getenv("API_KEY_Freecurrencyapi")
API_KEY_twelvedata: Optional[str] = os.getenv("API_KEY_twelvedata")


def get_cards_summary(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Рассчитывает статистику по банковским картам из транзакций.

    Возвращает список словарей с информацией по каждой карте:
    - last_digits: последние 4 цифры номера карты
    - total_spent: общая сумма расходов по карте (в рублях)
    - cashback: расчетный кэшбэк (1% от расходов)

    Список отсортирован по убыванию суммы расходов.
    """
    logger.debug(f"Начало расчета статистики по картам. Всего транзакций: {len(df)}")

    # Проверяем на пустой DataFrame
    if df.empty:
        logger.info("DataFrame пустой, возвращаем пустой список")
        return []

    # Фильтруем только расходные операции (отрицательные суммы)
    expenses_df = df[df["Сумма операции"] < 0].copy()
    logger.debug(f"Найдено расходных операций: {len(expenses_df)}")

    if expenses_df.empty:
        logger.info("Нет расходных операций, возвращаем пустой список")
        return []

    result: List[Dict[str, Any]] = []

    # Группируем операции по номеру карты
    for card_number, group in expenses_df.groupby("Номер карты"):
        # Суммируем расходы по карте (берем абсолютное значение)
        total_spent = float(abs(group["Сумма операции"].sum()))
        # Рассчитываем кэшбэк как 1% от расходов
        cashback = total_spent * 0.01
        # Извлекаем последние 4 цифры номера карты для безопасности
        last_digits = str(card_number)[-4:] if card_number else ""

        logger.debug(f"Карта {last_digits}: расходы={total_spent:.2f}, кэшбэк={cashback:.2f}")

        result.append(
            {
                "last_digits": last_digits,
                "total_spent": round(total_spent, 2),
                "cashback": round(cashback, 2),
            }
        )

    # Сортируем карты по убыванию суммы расходов
    result.sort(key=lambda x: x["total_spent"], reverse=True)
    logger.info(f"Рассчитана статистика по {len(result)} картам")

    return result


def get_top_transactions(df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Возвращает список крупнейших транзакций по абсолютной сумме.

    Аргументы:
        df: DataFrame с транзакциями
        limit: количество транзакций для возврата (по умолчанию 5)

    Возвращает список словарей с информацией о транзакциях:
    - date: дата в формате ДД.ММ.ГГГГ
    - amount: сумма операции (может быть отрицательной для расходов)
    - category: категория операции
    - description: описание операции (обрезается до 50 символов)
    """
    logger.debug(f"Поиск крупнейших транзакций. Лимит: {limit}, всего транзакций: {len(df)}")

    if df.empty:
        logger.info("DataFrame пустой, возвращаем пустой список")
        return []

    # Создаем копию DataFrame для безопасной модификации
    df_sorted = df.copy()
    # Добавляем колонку с абсолютными значениями сумм для сортировки
    df_sorted["abs_amount"] = df_sorted["Сумма операции"].abs()
    # Сортируем по убыванию абсолютной суммы
    df_sorted = df_sorted.sort_values("abs_amount", ascending=False)

    # Берем top-N транзакций и преобразуем в список словарей
    top_records = df_sorted.head(limit).to_dict("records")
    logger.debug(f"Отобрано {len(top_records)} крупнейших транзакций")

    result: List[Dict[str, Any]] = []

    for record in top_records:
        # Обрабатываем дату операции
        date_val = record.get("Дата операции")
        if isinstance(date_val, pd.Timestamp):
            # Форматируем дату в удобный для отображения формат
            date_str = date_val.strftime("%d.%m.%Y")
        else:
            # Запасной вариант если дата не в правильном формате
            date_str = str(date_val) if date_val is not None else "Нет даты"

        # Обрабатываем сумму операции
        amount_val = record.get("Сумма операции")
        if isinstance(amount_val, (int, float)):
            amount = round(float(amount_val), 2)
        else:
            amount = 0.0

        # Формируем информацию о транзакции
        transaction_info = {
            "date": date_str,
            "amount": amount,
            "category": str(record.get("Категория", "Не указано")),
            "description": str(record.get("Описание", "Без описания"))[:50],  # Ограничиваем длину описания
        }

        result.append(transaction_info)
        logger.debug(f"Транзакция: {date_str}, сумма: {amount}, категория: {transaction_info['category']}")

    logger.info(f"Сформирован список из {len(result)} крупнейших транзакций")
    return result


def format_currency_rates(raw_rates: Optional[Dict[str, float]]) -> List[Dict[str, Any]]:
    """
    Форматирует сырые данные курсов валют для отображения.
    """
    logger.debug(f"Форматирование курсов валют. Получено курсов: {len(raw_rates) if raw_rates else 0}")

    if not raw_rates:
        logger.info("Нет данных о курсах валют, возвращаем пустой список")
        return []

    # Преобразуем словарь в список словарей для удобства отображения
    formatted_rates = [{"currency": cur, "rate": rate} for cur, rate in raw_rates.items()]
    logger.debug(f"Отформатировано {len(formatted_rates)} курсов валют")

    return formatted_rates


def format_stock_prices(raw_stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Форматирует сырые данные цен акций для отображения.
    """
    logger.debug(f"Форматирование цен акций. Получено акций: {len(raw_stocks)}")

    if not raw_stocks:
        logger.info("Нет данных о ценах акций, возвращаем пустой список")
        return []

    # Форматируем данные, извлекая только нужные поля
    formatted_stocks = []
    for stock in raw_stocks:
        try:
            formatted_stock = {
                "stock": stock.get("stock", ""),
                "price": float(stock.get("price", 0.0)),  # Гарантируем числовой тип
            }
            formatted_stocks.append(formatted_stock)
        except Exception as e:
            logger.warning(f"Ошибка форматирования данных акции {stock}: {e}")

    logger.debug(f"Отформатировано {len(formatted_stocks)} цен акций")
    return formatted_stocks


def generate_financial_report(df: pd.DataFrame, date_string: str) -> Dict[str, Any]:
    """
    Генерирует полный финансовый отчет для главной страницы.

    - Приветствие в зависимости от времени суток
    - Статистика по банковским картам
    - Список крупнейших транзакций
    - Курсы валют
    - Цены акций

    Аргументы:
        df: DataFrame с транзакциями
        date_string: дата для анализа в формате "YYYY-MM-DD HH:MM:SS"

    Возвращает:
        Словарь с данными для отображения на главной странице
    """
    logger.info(f"Начало генерации финансового отчета для даты: {date_string}")
    logger.debug(f"Размер входных данных: {len(df)} транзакций")

    # Получаем приветствие в зависимости от времени суток
    greeting = get_greeting()
    logger.debug(f"Сформировано приветствие: '{greeting}'")

    # Парсим дату для анализа
    try:
        target_date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        # Определяем начало месяца для анализа (последние 3 месяца)
        month_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        logger.debug(f"Целевая дата: {target_date}, начало месяца: {month_start}")
    except Exception as e:
        logger.error(f"Ошибка парсинга даты '{date_string}': {e}")
        # Возвращаем базовую структуру отчета в случае ошибки
        return {
            "greeting": greeting,
            "cards": [],
            "top_transactions": [],
            "currency_rates": [],
            "stock_prices": [],
        }

    # Фильтруем и обрабатываем транзакции
    try:
        logger.debug("Фильтрация транзакций по дате...")
        df_filtered = filter_transactions_by_date(df, month_start, target_date)
        logger.debug(f"После фильтрации по дате: {len(df_filtered)} транзакций")

        logger.debug("Фильтрация успешных транзакций...")
        df_successful = filter_successful_transaction(df_filtered)
        logger.debug(f"После фильтрации по статусу: {len(df_successful)} транзакций")

    except Exception as e:
        logger.error(f"Ошибка обработки транзакций: {e}")
        df_successful = pd.DataFrame()

    # Загружаем пользовательские настройки
    logger.debug("Загрузка пользовательских настроек...")
    settings = load_user_settings(str(USER_SETTINGS))
    logger.debug(
        f"Загружены настройки: {len(settings.get('user_currencies', []))} валют, "
        f"{len(settings.get('user_stocks', []))} акций"
    )

    # Получаем курсы валют
    currency_rates: Dict[str, float] = {}
    try:
        if API_KEY_Freecurrencyapi:
            logger.info("Получение курсов валют из API...")
            raw_rates = get_currency_rates(API_KEY_Freecurrencyapi, "RUB", settings.get("user_currencies", []))
            if raw_rates:
                currency_rates = raw_rates
                logger.info(f"Получено курсов валют: {len(currency_rates)}")
            else:
                logger.warning("Не удалось получить курсы валют из API")
        else:
            logger.warning("API ключ для Freecurrencyapi не найден, курсы валют не будут получены")
    except Exception as e:
        logger.error(f"Ошибка получения курсов валют: {e}")

    # Проверяем наличие курсов для валют в транзакциях
    if not df_successful.empty and currency_rates:
        currencies_in_data = set(df_successful["Валюта операции"].unique())
        # Ищем валюты без курсов (кроме RUB)
        missing = currencies_in_data - set(currency_rates.keys()) - {"RUB"}
        if missing:
            logger.warning(f"Отсутствуют курсы для валют в транзакциях: {missing}")

    # Получаем цены акций
    try:
        logger.info("Получение цен акций из API...")
        stock_prices = get_stock_prices(settings.get("user_stocks", []))
        logger.info(f"Получено цен акций: {len(stock_prices)}")
    except Exception as e:
        logger.error(f"Ошибка получения цен акций: {e}")
        stock_prices = []

    # Конвертируем все суммы в рубли
    logger.debug("Конвертация транзакций в рубли...")
    df_successful = convert_transactions_to_rub(df_successful, currency_rates)

    # Рассчитываем статистику по картам
    logger.debug("Расчет статистики по картам...")
    cards_info = get_cards_summary(df_successful)

    # Получаем крупнейшие транзакции
    logger.debug("Поиск крупнейших транзакций...")
    top_transactions = get_top_transactions(df_successful)

    # Формируем финальный отчет
    logger.debug("Формирование финального отчета...")
    report = {
        "greeting": greeting,
        "cards": cards_info,
        "top_transactions": top_transactions,
        "currency_rates": format_currency_rates(currency_rates),
        "stock_prices": format_stock_prices(stock_prices),
    }

    logger.info("Финансовый отчет успешно сгенерирован.")

    return report

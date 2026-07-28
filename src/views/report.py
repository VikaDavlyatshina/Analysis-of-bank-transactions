import os
from datetime import datetime
from typing import Any, Dict

import pandas as pd
from dotenv import load_dotenv

from config import USER_SETTINGS, setup_views_logger
from src.api import get_currency_rates, get_stock_prices
from src.utils import (
    convert_transactions_to_rub,
    filter_successful_transaction,
    filter_transactions_by_date,
    get_greeting,
    load_user_settings,
)
from src.views.cards import get_cards_summary
from src.views.rates import format_currency_rates, format_stock_prices
from src.views.transactions import get_top_transactions

load_dotenv()

logger = setup_views_logger()


def generate_financial_report(df: pd.DataFrame, date_string: str) -> Dict[str, Any]:
    logger.info(f"Начало генерации финансового отчета для даты: {date_string}")
    logger.debug(f"Размер входных данных: {len(df)} транзакций")

    greeting = get_greeting()
    logger.debug(f"Сформировано приветствие: '{greeting}'")

    try:
        target_date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        month_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        logger.debug(f"Целевая дата: {target_date}, начало месяца: {month_start}")
    except Exception as e:
        logger.error(f"Ошибка парсинга даты '{date_string}': {e}")
        return {
            "greeting": greeting,
            "cards": [],
            "top_transactions": [],
            "currency_rates": [],
            "stock_prices": [],
        }

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

    logger.debug("Загрузка пользовательских настроек...")
    settings = load_user_settings(str(USER_SETTINGS))
    logger.debug(
        f"Загружены настройки: {len(settings.get('user_currencies', []))} валют, "
        f"{len(settings.get('user_stocks', []))} акций"
    )

    currency_rates: Dict[str, float] = {}
    try:
        if os.getenv("API_KEY_Freecurrencyapi"):
            logger.info("Получение курсов валют из API...")
            raw_rates = get_currency_rates(
                os.getenv("API_KEY_Freecurrencyapi", ""), "RUB", settings.get("user_currencies", [])
            )
            if raw_rates:
                currency_rates = raw_rates
                logger.info(f"Получено курсов валют: {len(currency_rates)}")
            else:
                logger.warning("Не удалось получить курсы валют из API")
        else:
            logger.warning("API ключ для Freecurrencyapi не найден, курсы валют не будут получены")
    except Exception as e:
        logger.error(f"Ошибка получения курсов валют: {e}")

    if not df_successful.empty and currency_rates:
        currencies_in_data = set(df_successful["Валюта операции"].unique())
        missing = currencies_in_data - set(currency_rates.keys()) - {"RUB"}
        if missing:
            logger.warning(f"Отсутствуют курсы для валют в транзакциях: {missing}")

    try:
        logger.info("Получение цен акций из API...")
        stock_prices = get_stock_prices(settings.get("user_stocks", []))
        logger.info(f"Получено цен акций: {len(stock_prices)}")
    except Exception as e:
        logger.error(f"Ошибка получения цен акций: {e}")
        stock_prices = []

    logger.debug("Конвертация транзакций в рубли...")
    df_successful = convert_transactions_to_rub(df_successful, currency_rates)

    logger.debug("Расчет статистики по картам...")
    cards_info = get_cards_summary(df_successful)

    logger.debug("Поиск крупнейших транзакций...")
    top_transactions = get_top_transactions(df_successful)

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

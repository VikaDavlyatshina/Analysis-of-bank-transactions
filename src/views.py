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
    if df.empty:
        return []

    expenses_df = df[df["Сумма операции"] < 0].copy()
    if expenses_df.empty:
        return []

    result: List[Dict[str, Any]] = []
    for card_number, group in expenses_df.groupby("Номер карты"):
        total_spent = float(abs(group["Сумма операции"].sum()))
        cashback = total_spent * 0.01
        last_digits = str(card_number)[-4:]
        result.append({
            "last_digits": last_digits,
            "total_spent": round(total_spent, 2),
            "cashback": round(cashback, 2),
        })

    result.sort(key=lambda x: x["total_spent"], reverse=True)
    return result


def get_top_transactions(df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
    if df.empty:
        return []

    df_sorted = df.copy()
    df_sorted["abs_amount"] = df_sorted["Сумма операции"].abs()
    df_sorted = df_sorted.sort_values("abs_amount", ascending=False)
    top_records = df_sorted.head(limit).to_dict("records")

    result: List[Dict[str, Any]] = []
    for record in top_records:
        date_val = record.get("Дата операции")
        if isinstance(date_val, pd.Timestamp):
            date_str = date_val.strftime("%d.%m.%Y")
        else:
            date_str = str(date_val) if date_val is not None else "Нет даты"

        amount_val = record.get("Сумма операции")
        if isinstance(amount_val, (int, float)):
            amount = round(float(amount_val), 2)
        else:
            amount = 0.0

        result.append({
            "date": date_str,
            "amount": amount,
            "category": str(record.get("Категория", "Не указано")),
            "description": str(record.get("Описание", "Без описания"))[:50],
        })
    return result


def format_currency_rates(raw_rates: Optional[Dict[str, float]]) -> List[Dict[str, Any]]:
    if not raw_rates:
        return []
    return [{"currency": cur, "rate": rate} for cur, rate in raw_rates.items()]


def format_stock_prices(raw_stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not raw_stocks:
        return []
    return [{"stock": stock.get("stock", ""), "price": float(stock.get("price", 0.0))} for stock in raw_stocks]


def generate_financial_report(df: pd.DataFrame, date_string: str) -> Dict[str, Any]:
    logger.info(f"Генерация отчета для даты: {date_string}")

    greeting = get_greeting()

    try:
        target_date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        month_start = target_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    except Exception as e:
        logger.error(f"Ошибка парсинга даты: {e}")
        return {
            "greeting": greeting,
            "cards": [],
            "top_transactions": [],
            "currency_rates": [],
            "stock_prices": [],
        }

    try:
        df_filtered = filter_transactions_by_date(df, month_start, target_date)
        df_successful = filter_successful_transaction(df_filtered)
    except Exception as e:
        logger.error(f"Ошибка обработки транзакций: {e}")
        df_successful = pd.DataFrame()

    settings = load_user_settings(str(USER_SETTINGS))

    currency_rates: Dict[str, float] = {}
    try:
        if API_KEY_Freecurrencyapi:
            raw_rates = get_currency_rates(API_KEY_Freecurrencyapi, "RUB", settings.get("user_currencies", []))
            if raw_rates:
                currency_rates = raw_rates
    except Exception as e:
        logger.error(f"Ошибка получения курсов валют: {e}")

    if not df_successful.empty:
        currencies_in_data = set(df_successful["Валюта операции"].unique())
        missing = currencies_in_data - set(currency_rates.keys()) - {"RUB"}
        if missing:
            logger.warning(f"Нет курсов для валют: {missing}")

    try:
        stock_prices = get_stock_prices(settings.get("user_stocks", []))
    except Exception as e:
        logger.error(f"Ошибка получения цен акций: {e}")
        stock_prices = []

    df_successful = convert_transactions_to_rub(df_successful, currency_rates)

    cards_info = get_cards_summary(df_successful)
    top_transactions = get_top_transactions(df_successful)

    report = {
        "greeting": greeting,
        "cards": cards_info,
        "top_transactions": top_transactions,
        "currency_rates": format_currency_rates(currency_rates),
        "stock_prices": format_stock_prices(stock_prices),
    }

    return report
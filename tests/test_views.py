import json
from unittest.mock import patch
import pandas as pd

from src.views import (get_cards_summary, get_top_transactions, format_currency_rates, format_stock_prices,
                       generate_financial_report)
from src.utils import save_report


def test_get_cards_summary(sample_transactions_df):
    result = get_cards_summary(sample_transactions_df)
    assert len(result) == 2  # 2 карты
    # Проверка total_spent и cashback для первой карты
    card = result[0]
    assert card['last_digits'] == '1111'
    assert card['total_spent'] == 1500
    assert card['cashback'] == 15

def test_get_top_transactions(sample_transactions_df):
    result = get_top_transactions(sample_transactions_df, limit=2)
    assert len(result) == 2
    assert result[0]['amount'] == -1000
    assert result[1]['amount'] == -500

def test_format_currency_rates():
    rates = {"USD": 80, "EUR": 100}
    result = format_currency_rates(rates)
    assert isinstance(result, list)
    assert result[0]['currency'] in rates
    assert result[0]['rate'] in rates.values()

def test_format_stock_prices():
    stocks = [{"stock": "AAPL", "price": 150}]
    result = format_stock_prices(stocks)
    assert result[0]['stock'] == "AAPL"
    assert result[0]['price'] == 150

def test_save_report(tmp_path):
    report = {"greeting": "Добрый день", "cards": [], "top_transactions": [], "currency_rates": [], "stock_prices": []}
    file_name = tmp_path / "report.json"
    success = save_report(report, filename=str(file_name))
    assert success
    # Проверяем содержимое файла
    with open(file_name, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["greeting"] == "Добрый день"




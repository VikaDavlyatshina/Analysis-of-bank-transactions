import json
from unittest.mock import patch
import pandas as pd

from src.views import (get_cards_summary, get_top_transactions, format_currency_rates, format_stock_prices,
                       save_report, generate_financial_report)


def test_get_cards_summary(sample_transactions_df):
    result = get_cards_summary(sample_transactions_df)
    assert len(result) == 2  # 2 карты
    # Проверка total_spent и cashback для первой карты
    card = result[0]
    assert card['last_digits'] == '1111'
    assert card['total_spent'] == 1500
    assert card['cashback'] == 15
    assert card['transactions'] == 2

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


def test_generate_financial_report_basic():
    with patch("src.views.load_transactions_from_excel") as mock_load_excel, \
         patch("src.views.filter_transactions_by_date") as mock_filter_by_date, \
         patch("src.views.filter_successful_transaction") as mock_filter_successful, \
         patch("src.views.convert_transactions_to_rub") as mock_convert, \
         patch("src.views.get_currency_rates") as mock_currency_rates, \
         patch("src.views.get_stock_prices") as mock_stock_prices, \
         patch("src.views.load_user_settings") as mock_load_settings, \
         patch("src.views.get_greeting") as mock_greeting:

        # Моки
        mock_greeting.return_value = "Добрый день"
        mock_load_settings.return_value = {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}
        mock_currency_rates.return_value = {"USD": 80}
        mock_stock_prices.return_value = [{"stock": "AAPL", "price": 150}]

        # Важная правка: возвращаем пустой DataFrame
        mock_load_excel.return_value = pd.DataFrame()
        mock_filter_by_date.return_value = pd.DataFrame()
        mock_filter_successful.return_value = pd.DataFrame()
        mock_convert.return_value = pd.DataFrame()

        report = generate_financial_report("2025-12-14 12:00:00")

        assert isinstance(report, dict)
        assert "greeting" in report
        assert "cards" in report
        assert "top_transactions" in report
        assert "currency_rates" in report
        assert "stock_prices" in report

        assert report["greeting"] == "Добрый день"
        assert report["cards"] == []
        assert report["top_transactions"] == []
        assert report["currency_rates"] == [{"currency": "USD", "rate": 80}]
        assert report["stock_prices"] == [{"stock": "AAPL", "price": 150}]



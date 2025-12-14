from datetime import datetime
import pytest
import json
from unittest.mock import patch

from src.utils import (convert_transactions_to_rub, filter_successful_transaction, filter_transactions_by_date,
                       get_greeting, load_user_settings, get_stock_prices, get_currency_rates)



# convert_transactions_to_rub

def test_convert_transactions_to_rub(sample_transactions_df):
    rates = {"USD": 80, "EUR": 100}
    df = convert_transactions_to_rub(sample_transactions_df, rates)
    assert df.loc[0, "Сумма операции"] == -1000  # RUB не меняется
    assert df.loc[1, "Сумма операции"] == -40000  # USD конвертируется
    assert df.loc[2, "Сумма операции"] == -20000  # EUR конвертируется

def test_convert_transactions_missing_currency(sample_transactions_df):
    rates = {"USD": 80}
    df = convert_transactions_to_rub(sample_transactions_df, rates)
    assert df.loc[0, "Сумма операции"] == -1000  # RUB
    assert df.loc[1, "Сумма операции"] == -40000  # USD
    assert df.loc[2, "Сумма операции"] == -200  # EUR без курса → не конвертируется


# filter_transactions_by_date

def test_filter_transactions_by_date(sample_transactions_df):
    start = datetime(2021, 8, 1)
    end = datetime(2021, 8, 2)
    df_filtered = filter_transactions_by_date(sample_transactions_df, start, end)
    assert len(df_filtered) == 2
    assert all((df_filtered["Дата операции"] >= start) & (df_filtered["Дата операции"] <= end))



# filter_successful_transaction

def test_filter_successful_transaction(sample_transactions_df):
    df = sample_transactions_df.copy()
    df.loc[1, "Статус"] = "FAILED"
    df_successful = filter_successful_transaction(df)
    assert len(df_successful) == 2
    assert df_successful["Статус"].eq("OK").all()

# get_greeting

@pytest.mark.parametrize(
    "hour,expected",
    [
        (6, "Доброе утро"),
        (13, "Добрый день"),
        (18, "Добрый вечер"),
        (23, "Доброй ночи")
    ]
)
def test_get_greeting(hour, expected):
    dt = datetime(2021, 8, 1, hour)
    assert get_greeting(dt) == expected


# load_user_settings

def test_load_user_settings(tmp_path):
    file = tmp_path / "settings.json"
    data = {"user_currencies": ["GBP"], "user_stocks": ["NFLX"]}
    file.write_text(json.dumps(data), encoding="utf-8")
    settings = load_user_settings(file)
    assert settings["user_currencies"] == ["GBP"]
    assert settings["user_stocks"] == ["NFLX"]

def test_load_user_settings_missing_file(tmp_path):
    file = tmp_path / "missing.json"
    settings = load_user_settings(file)
    assert settings["user_currencies"] == ["USD", "EUR"]  # defaults
    assert settings["user_stocks"] == ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

def test_load_user_settings_bad_json(tmp_path):
    file = tmp_path / "bad.json"
    file.write_text("{ bad json }", encoding="utf-8")
    settings = load_user_settings(file)
    assert settings["user_currencies"] == ["USD", "EUR"]  # defaults

# get_currency_rates

@patch("src.utils.requests.get")
def test_get_currency_rates(mock_get):
    mock_resp = mock_get.return_value
    mock_resp.json.return_value = {"data": {"USD": 0.0125, "EUR": 0.01}}
    mock_resp.raise_for_status = lambda: None
    rates = get_currency_rates("FAKE_KEY")
    assert rates["USD"] == round(1 / 0.0125, 2)
    assert rates["EUR"] == round(1 / 0.01, 2)



# get_stock_prices

@patch("src.utils.requests.get")
def test_get_stock_prices(mock_get):
    mock_resp = mock_get.return_value
    mock_resp.json.return_value = {"price": "123.45"}
    mock_resp.raise_for_status = lambda: None
    prices = get_stock_prices(["AAPL"])
    assert prices[0]["price"] == 123.45
    assert prices[0]["stock"] == "AAPL"
    assert prices[0]["source"] == "twelvedata"
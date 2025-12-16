import pandas as pd
from datetime import datetime, timedelta
import pytest

@pytest.fixture
def sample_transactions_df():
    return pd.DataFrame({
        "Дата операции": pd.to_datetime(["2021-08-01", "2021-08-02", "2021-08-03"]),
        "Сумма операции": [-1000, -500, -200],
        "Валюта операции": ["RUB", "USD", "EUR"],
        "Категория": ["Еда", "Транспорт", "Развлечения"],
        "Описание": ["Кофе", "Такси", "Кино"],
        "Номер карты": ["1111", "1111", "2222"],
        "Статус": ["OK", "OK", "OK"]
    })

@pytest.fixture
def sample_data_for_report():
    data = [
        {"Дата операции": datetime.now() - timedelta(days=10), "Категория": "Еда", "Сумма операции": -500},
        {"Дата операции": datetime.now() - timedelta(days=20), "Категория": "Еда", "Сумма операции": -300},
        {"Дата операции": datetime.now() - timedelta(days=40), "Категория": "Транспорт", "Сумма операции": -200},
        {"Дата операции": datetime.now() - timedelta(days=70), "Категория": "Еда", "Сумма операции": -150},
        {"Дата операции": datetime.now() - timedelta(days=100), "Категория": "Еда", "Сумма операции": -100},
    ]

    return pd.DataFrame(data)

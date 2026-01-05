from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List
from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest


@pytest.fixture
def temp_excel_file(tmp_path: Path) -> Callable[[Dict[str, Any]], str]:
    """Фикстура для создания временного файла Excel"""

    def _create_file(data_dict: Dict[str, Any]) -> str:
        file_path = tmp_path / "test_transactions.xlsx"
        df = pd.DataFrame(data_dict)
        df.to_excel(file_path, index=False)
        return str(file_path)

    return _create_file


@pytest.fixture
def sample_transactions_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(
                [
                    "2021-08-01",  # 1 августа
                    "2021-08-01",  # еще одна 1 августа
                    "2021-08-02",  # 2 августа
                    "2021-08-03",  # 3 августа
                    "2021-08-04",  # 4 августа
                    "2021-10-03",
                    "2021-07-01",
                    "2021-08-31",
                ]
            ),
            "Сумма операции": [-1000, 500, -200, -300, -400, -500, 400, 2000],
            "Валюта операции": [
                "RUB",
                "USD",
                "EUR",
                "RUB",
                "USD",
                "EUR",
                "RUB",
                "RUB",
            ],
            "Категория": [
                "Еда",
                "Транспорт",
                "Развлечения",
                "Еда",
                "Транспорт",
                "Развлечения",
                "Супермаркет",
                "Транспорт",
            ],
            "Описание": ["Кофе", "Такси", "Кино", "Кафе", "Каршеринг", "Музей", "Покупка Магнит", "Метро"],
            "Номер карты": ["4515", "", "7232", "7232", "4515", "3672", "", "4515"],
            "Статус": ["OK", "FAILED", "OK", "OK", "FAILED", "OK", "OK", "OK"],
            "Кэшбэк": [0.0, 0.0, 15.0, 0.0, 36.0, 5.0, 0.0, 0.0],
            "MCC": ["5814", "7521", "6532", "1223", "5975", "7521", "", ""],
        }
    )


@pytest.fixture
def sample_data_for_report() -> pd.DataFrame:
    data = [
        {"Дата операции": datetime.now() - timedelta(days=10), "Категория": "Еда", "Сумма операции": -500},
        {"Дата операции": datetime.now() - timedelta(days=20), "Категория": "Еда", "Сумма операции": -300},
        {"Дата операции": datetime.now() - timedelta(days=40), "Категория": "Транспорт", "Сумма операции": -200},
        {"Дата операции": datetime.now() - timedelta(days=70), "Категория": "Еда", "Сумма операции": -150},
        {"Дата операции": datetime.now() - timedelta(days=100), "Категория": "Еда", "Сумма операции": -100},
    ]

    return pd.DataFrame(data)


@pytest.fixture
def mock_report_decorator():
    """Фикстура для мока декоратора report_to_file."""
    with patch('src.services.report_to_file', lambda func=None, **kwargs: (lambda f: f)):
        import importlib
        import src.services
        importlib.reload(src.services)
        yield

@pytest.fixture
def create_test_dataframe():
    """
    Фикстура для создания тестового DataFrame.
    Можно использовать в любом тесте, передав списки дат, сумм и категорий.
    """
    def _create(dates: List[str], amounts: List[float], categories: List[str]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Дата операции": pd.to_datetime(dates),
                "Сумма операции": amounts,
                "Категория": categories,
            }
        )
    return _create

@pytest.fixture
def transactions() -> List[Dict[str, Any]]:
    """Фикстура с тестовыми транзакциями"""
    return [
        {
            "Дата операции": "2025-12-01 12:00:00",
            "Сумма операции": -123.45,
        },
        {
            "Дата операции": "2025-12-02 12:00:00",
            "Сумма операции": -67.89,
        },
        {
            "Дата операции": "2025-11-30 12:00:00",  # Не подходит по месяцу
            "Сумма операции": -100.00,
        },
        {
            "Дата операции": "2025-12-03 12:00:00",
            "Сумма операции": 50.00,  # Положительная сумма - пропускается
        },
    ]

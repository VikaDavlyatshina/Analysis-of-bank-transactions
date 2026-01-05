import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional
from unittest.mock import Mock, patch

import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def disable_all_logs() -> Iterator[None]:
    """Автоматически отключает все логи во время тестов."""
    # Отключаем логирование полностью
    logging.disable(logging.CRITICAL)

    yield  # Тесты выполняются здесь

    # Включаем логирование обратно
    logging.disable(logging.NOTSET)


@pytest.fixture
def no_save() -> Iterator[None]:
    """Полностью блокирует сохранение файлов."""

    # Создаем заглушку, которая ничего не делает
    def mock_report_to_file(func: Optional[Callable[..., Any]] = None, **_kwargs: Any) -> Callable[..., Any]:
        if func is None:
            # @report_to_file()
            def decorator(inner_func: Callable[..., Any]) -> Callable[..., Any]:
                return inner_func  # Просто возвращаем функцию как есть

            return decorator
        else:
            # @report_to_file
            return func  # Просто возвращаем функцию без обертки

    # Мокаем все операции с файлами
    with patch("src.services.report_to_file", mock_report_to_file):
        with patch("builtins.open"):  # Блокируем открытие файлов
            with patch("json.dump"):  # Блокируем запись JSON
                with patch("pathlib.Path.mkdir"):  # Блокируем создание папок
                    # Перезагружаем модуль
                    import importlib

                    import src.services

                    importlib.reload(src.services)
                    yield


@pytest.fixture
def mock_currency_api() -> Iterator[None]:
    """Мокает API валют чтобы не было реальных запросов."""
    # Тестовые курсы валют
    test_rates: Dict[str, float] = {
        "USD": 0.011,  # 1 USD = 0.011 RUB (~91 RUB за доллар)
        "EUR": 0.012,  # 1 EUR = 0.012 RUB (~83 RUB за евро)
        "GBP": 0.014,  # 1 GBP = 0.014 RUB (~71 RUB за фунт)
    }

    # Мокаем requests.get
    with patch("src.utils.requests.get") as mock_get:
        # Создаем мок-ответ
        mock_response = Mock()
        mock_response.json.return_value = {"data": test_rates}
        mock_response.raise_for_status.return_value = None

        # Настраиваем мок
        mock_get.return_value = mock_response
        yield


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
            "Сумма операции": [-1000.0, 500.0, -200.0, -300.0, -400.0, -500.0, 400.0, 2000.0],
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
    data: List[Dict[str, Any]] = [
        {"Дата операции": datetime.now() - timedelta(days=10), "Категория": "Еда", "Сумма операции": -500.0},
        {"Дата операции": datetime.now() - timedelta(days=20), "Категория": "Еда", "Сумма операции": -300.0},
        {"Дата операции": datetime.now() - timedelta(days=40), "Категория": "Транспорт", "Сумма операции": -200.0},
        {"Дата операции": datetime.now() - timedelta(days=70), "Категория": "Еда", "Сумма операции": -150.0},
        {"Дата операции": datetime.now() - timedelta(days=100), "Категория": "Еда", "Сумма операции": -100.0},
    ]

    return pd.DataFrame(data)


@pytest.fixture
def mock_report_decorator() -> Iterator[None]:
    """Фикстура для мока декоратора report_to_file."""
    with patch("src.services.report_to_file", lambda func=None, **kwargs: (lambda f: f)):
        import importlib

        import src.services

        importlib.reload(src.services)
        yield


@pytest.fixture
def create_test_dataframe() -> Callable[[List[str], List[float], List[str]], pd.DataFrame]:
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


@pytest.fixture
def invest_data() -> List[Dict[str, Any]]:
    """Простые данные для тестов investment_bank."""
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
            "Дата операции": "2025-11-30 12:00:00",  # Другой месяц - не учитывается
            "Сумма операции": -100.00,
        },
        {
            "Дата операции": "2025-12-03 12:00:00",
            "Сумма операции": 50.00,  # Положительная - пропускается
        },
    ]


@pytest.fixture
def search_data() -> List[Dict[str, str]]:
    """Простые данные для тестов simple_search."""
    return [
        {"Описание": "Купил хлеб", "Категория": "Еда"},
        {"Описание": "Оплата интернета", "Категория": "Связь"},
        {"Описание": "Покупка в магазине", "Категория": "Супермаркет"},
        {"Описание": "Обед в кафе", "Категория": "Ресторан"},
        {"Описание": "Молоко", "Категория": "Еда"},
    ]

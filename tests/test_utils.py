import json
from datetime import datetime
from unittest.mock import patch, Mock
from typing import List, Dict, Any, Optional
from pathlib import Path

import pandas as pd
import requests
import pytest

from src.utils import (
    convert_transactions_to_rub,
    filter_successful_transaction,
    filter_transactions_by_date,
    get_currency_rates,
    get_greeting,
    get_stock_prices,
    load_user_settings,
    save_report,
    prepare_transactions_for_services,
)


# ==== filter_transactions_by_date ====
"""Тесты функции filter_transactions_by_date"""


@pytest.mark.parametrize("start_date, end_date, expected_count", [
    (datetime(2021, 8, 2), datetime(2021, 8, 2), 1),
    (datetime(2021, 8, 1), datetime(2021, 8, 3), 4),
    (datetime(2021, 8, 2), datetime(2021, 8, 4), 3),
    (datetime(2021, 8, 6), datetime(2021, 8, 8), 0),
    (datetime(2021, 8, 1), datetime(2021, 8, 5), 5)
])
def test_filter_count(
        sample_transactions_df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime,
        expected_count: int
) -> None:
    """Тест для проверки количества транзакций в диапазоне дат"""
    result: pd.DataFrame = filter_transactions_by_date(sample_transactions_df, start_date, end_date)
    assert len(result) == expected_count


def test_filter_preserves_columns(sample_transactions_df: pd.DataFrame) -> None:
    """Проверяем, что все колонки сохраняются после фильтрации"""
    result: pd.DataFrame = filter_transactions_by_date(
        sample_transactions_df,
        datetime(2021, 8, 1),
        datetime(2021, 8, 2)
    )

    assert set(result.columns) == set(sample_transactions_df.columns)
    assert "Категория" in result.columns


def test_filter_preserves_data_integrity(sample_transactions_df: pd.DataFrame) -> None:
    """Проверяем целостность данных"""
    result: pd.DataFrame = filter_transactions_by_date(
        sample_transactions_df,
        datetime(2021, 8, 1),
        datetime(2021, 8, 3)
    )

    assert len(result) == 4
    assert result["Сумма операции"].tolist() == [-1000, 500, -200, -300]
    assert result["Категория"].tolist() == ["Еда", "Транспорт", "Развлечения", "Еда"]


# ==== filter_successful_transaction ===
"""Тесты функции filter_successful_transaction"""


def test_filter_successful_transaction(sample_transactions_df: pd.DataFrame) -> None:
    """Тест фильтрации успешных транзакций"""
    df_successful: pd.DataFrame = filter_successful_transaction(sample_transactions_df)

    assert len(df_successful) == 6
    assert not df_successful["Статус"].eq("FAILED").any()


@pytest.mark.parametrize("statuses, sums, expected_count", [
    (["OK", "OK", "OK"], [-100, -200, -300], 3),
    (["FAILED", "FAILED", "FAILED"], [-100, -200, -300], 0),
    (["OK", "FAILED", "OK", "FAILED"], [-100, -200, -300, -400], 2),
    (["OK", "PENDING", "OK"], [-100, -200, -300], 2),
    ([], [], 0),
    (["OK"], [-100], 1),
    (["FAILED"], [-100], 0),
])
def test_filter_successful_transaction_parametrized(
        statuses: List[str],
        sums: List[float],
        expected_count: int
) -> None:
    """Параметризованный тест с разными комбинациями статусов"""
    df: pd.DataFrame = pd.DataFrame({
        "Статус": statuses,
        "Сумма операции": sums,
        "Категория": ["Еда"] * len(statuses)
    })

    result: pd.DataFrame = filter_successful_transaction(df)
    assert len(result) == expected_count

    if expected_count > 0:
        assert result["Статус"].eq("OK").all(), "Не все статусы 'OK'"
        expected_sums: List[float] = [
            sums[i] for i, status in enumerate(statuses) if status.upper() == "OK"
        ]
        actual_sums: List[float] = result["Сумма операции"].tolist()
        assert actual_sums == expected_sums, f"Ожидались суммы {expected_sums}, получены {actual_sums}"
    else:
        assert result.empty, "DataFrame должен быть пустым"


# === get_greeting ===
"""Тесты функции get_greeting"""


@pytest.mark.parametrize("hour, expected", [
    (5, "Доброе утро"), (11, "Доброе утро"),
    (12, "Добрый день"), (16, "Добрый день"),
    (17, "Добрый вечер"), (21, "Добрый вечер"),
    (22, "Доброй ночи"), (4, "Доброй ночи"),
])
def test_get_greeting_basic(hour: int, expected: str) -> None:
    """Базовый тест приветствий"""
    dt: datetime = datetime(2024, 1, 1, hour)
    assert get_greeting(dt) == expected


def test_get_greeting_default() -> None:
    """Тест вызова без параметров"""
    result: str = get_greeting()
    assert result in {"Доброе утро", "Добрый день", "Добрый вечер", "Доброй ночи"}


def test_get_greeting_boundaries() -> None:
    """Тест граничных значений времени"""
    boundaries: List[tuple[int, int, str]] = [
        (4, 59, "Доброй ночи"),
        (5, 0, "Доброе утро"),
        (11, 59, "Доброе утро"),
        (12, 0, "Добрый день"),
        (16, 59, "Добрый день"),
        (17, 0, "Добрый вечер"),
        (21, 59, "Добрый вечер"),
        (22, 0, "Доброй ночи"),
    ]

    for hour, minute, expected in boundaries:
        dt: datetime = datetime(2024, 1, 1, hour, minute)
        assert get_greeting(dt) == expected, f"{hour:02d}:{minute:02d}"


# === convert_transactions_to_rub ===
"""Тесты функции convert_transactions_to_rub"""


@pytest.mark.parametrize("amounts, currencies, rates, expected_amounts", [
    ([-1000, -500, -200], ["RUB", "USD", "EUR"], {"USD": 90.0, "EUR": 100.0}, [-1000, -45000, -20000]),
    ([100, 200, 300], ["USD", "EUR", "GBP"], {"USD": 90.0}, [9000, 200, 300]),
    ([500, 1000, 1500], ["RUB", "RUB", "RUB"], {"USD": 90.0}, [500, 1000, 1500]),
])
def test_convert_transactions_to_rub(
        amounts: List[float],
        currencies: List[str],
        rates: Dict[str, float],
        expected_amounts: List[float]
) -> None:
    """Тест конвертации нескольких транзакций"""
    df: pd.DataFrame = pd.DataFrame({
        "Валюта операции": currencies,
        "Сумма операции": amounts
    })

    result: pd.DataFrame = convert_transactions_to_rub(df, rates)

    for i, expected in enumerate(expected_amounts):
        assert result.iloc[i]["Сумма операции"] == expected


# === prepare_transactions_for_services ===
"""Тесты функции prepare_transactions_for_services"""


def test_prepare_transactions_for_services() -> None:
    """Тест преобразования DataFrame в список словарей"""
    df: pd.DataFrame = pd.DataFrame({
        "Дата операции": pd.to_datetime(["2024-01-15 14:30:00", "2024-01-16 10:00:00"]),
        "Дата платежа": pd.to_datetime(["2024-01-16", "2024-01-17"]),
        "Сумма операции": [-1000, 500],
        "Категория": ["Еда", "Транспорт"]
    })

    result: List[Dict[str, Any]] = prepare_transactions_for_services(df)

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["Дата операции"] == "2024-01-15 14:30:00"
    assert result[0]["Дата платежа"] == "2024-01-16"
    assert result[0]["Сумма операции"] == -1000
    assert result[0]["Категория"] == "Еда"


def test_prepare_transactions_for_services_without_dates() -> None:
    """Тест когда нет колонок с датами"""
    df: pd.DataFrame = pd.DataFrame({
        "Сумма операции": [100, 200],
        "Категория": ["A", "B"]
    })

    result: List[Dict[str, Any]] = prepare_transactions_for_services(df)

    assert len(result) == 2
    assert result[0]["Сумма операции"] == 100
    assert result[0]["Категория"] == "A"


def test_prepare_transactions_for_services_empty() -> None:
    """Тест с пустым DataFrame"""
    df: pd.DataFrame = pd.DataFrame(columns=["Дата операции", "Сумма операции"])
    # Укажи тип для колонки даты
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    result: List[Dict[str, Any]] = prepare_transactions_for_services(df)
    assert result == []

# === load_user_settings ===
"""Тесты функции load_user_settings"""


def test_load_user_settings(tmp_path: Path) -> None:
    """Тест загрузки пользовательских настроек из файла"""
    file: Path = tmp_path / "settings.json"
    data: Dict[str, Any] = {"user_currencies": ["GBP"], "user_stocks": ["NFLX"]}
    file.write_text(json.dumps(data), encoding="utf-8")

    settings: Dict[str, Any] = load_user_settings(str(file))
    assert settings["user_currencies"] == ["GBP"]
    assert settings["user_stocks"] == ["NFLX"]


def test_load_user_settings_missing_file(tmp_path: Path) -> None:
    """Тест загрузки настроек при отсутствии файла"""
    file: Path = tmp_path / "missing.json"
    settings: Dict[str, Any] = load_user_settings(str(file))
    assert settings["user_currencies"] == ["USD", "EUR"]
    assert settings["user_stocks"] == ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]


def test_load_user_settings_bad_json(tmp_path: Path) -> None:
    """Тест обработки некорректного JSON"""
    file: Path = tmp_path / "bad.json"
    file.write_text("{ bad json }", encoding="utf-8")
    settings: Dict[str, Any] = load_user_settings(str(file))
    assert settings["user_currencies"] == ["USD", "EUR"]


# === get_currency_rates ===
"""Тесты функции get_currency_rates"""


@pytest.mark.parametrize("api_response, expected_rates", [
    ({"data": {"USD": 0.01}}, {"USD": 100.00}),
    ({"data": {"USD": 0.02, "EUR": 0.015}}, {"USD": 50.00, "EUR": round(1 / 0.015, 2)}),
    ({"data": {"USD": 0.0}}, {"USD": 0.0}),
    ({"data": {"JPY": 1.5}}, {"JPY": round(1 / 1.5, 2)}),
])
def test_get_currency_rates_various_cases(
        api_response: Dict[str, Any],
        expected_rates: Dict[str, float]
) -> None:
    """Тест различных случаев получения курсов валют"""
    mock_response: Mock = Mock()
    mock_response.json.return_value = api_response
    mock_response.raise_for_status = Mock()

    with patch('src.utils.requests.get', return_value=mock_response):
        rates: Optional[Dict[str, float]] = get_currency_rates(
            "FAKE_KEY",
            currencies=list(api_response["data"].keys())
        )

    assert rates is not None
    for currency, expected_rate in expected_rates.items():
        actual_rate: float = rates[currency]
        assert abs(actual_rate - expected_rate) < 0.01


def test_get_currency_rate_api_error() -> None:
    """Тест ошибки при вызове API"""
    mock_response: Mock = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")

    with patch('src.utils.requests.get', return_value=mock_response):
        rates: Optional[Dict[str, float]] = get_currency_rates("FAKE_KEY")
        assert rates is None


def test_get_currency_rate_network_error() -> None:
    """Тест сетевой ошибки"""
    with patch('src.utils.requests.get', side_effect=requests.exceptions.RequestException("Network error")):
        rates: Optional[Dict[str, float]] = get_currency_rates("FAKE_KEY")
    assert rates is None


def test_currency_rates_no_api_key() -> None:
    """Тест без API ключа"""
    rates: Optional[Dict[str, float]] = get_currency_rates("")
    assert rates is None


# === get_stock_prices ===

def test_get_stock_prices_success() -> None:
    """Тест успешного получения цен акций"""
    stocks = ["AAPL", "MSFT"]

    mock_responses = [
        Mock(json=Mock(return_value={"price": "150.75"})),
        Mock(json=Mock(return_value={"price": "300.50"})),
    ]

    for mock in mock_responses:
        mock.raise_for_status = Mock()

    with patch('src.utils.requests.get') as mock_get:
        mock_get.side_effect = mock_responses
        with patch('src.utils.logger') as mock_logger:
            prices = get_stock_prices(stocks)

    assert len(prices) == 2
    assert prices[0]["price"] == 150.75
    assert prices[1]["price"] == 300.50

    # Проверяем логирование успеха
    mock_logger.info.assert_any_call("Цена AAPL: $150.75 (реальные данные)")


def test_get_stock_prices_no_price_in_response() -> None:
    """Тест когда в ответе API нет поля 'price'"""
    mock_response = Mock()
    mock_response.json.return_value = {}  # Нет поля price
    mock_response.raise_for_status = Mock()

    with patch('src.utils.requests.get', return_value=mock_response):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["AAPL"])

    assert result[0]["price"] == 270.0  # fallback
    # Проверяем, что было логгирование с правильным сообщением
    mock_logger.warning.assert_called_with(
        "Цена AAPL: $270.00 (заглушка - нет данных в API)"
    )


def test_get_stock_prices_empty_price_string() -> None:
    """Тест когда price есть но пустая строка"""
    mock_response = Mock()
    mock_response.json.return_value = {"price": ""}  # Пустая строка = False
    mock_response.raise_for_status = Mock()

    with patch('src.utils.requests.get', return_value=mock_response):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["TSLA"])

    # Пустая строка = False -> попадает в else
    assert result[0]["price"] == 245.0  # fallback
    mock_logger.warning.assert_called_with(
        "Цена TSLA: $245.00 (заглушка - нет данных в API)"
    )


def test_get_stock_prices_price_is_none() -> None:
    """Тест когда price есть но равен None"""
    mock_response = Mock()
    mock_response.json.return_value = {"price": None}  # None = False
    mock_response.raise_for_status = Mock()

    with patch('src.utils.requests.get', return_value=mock_response):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["AAPL"])

    # None = False -> попадает в else
    assert result[0]["price"] == 270.0  # fallback
    mock_logger.warning.assert_called_with(
        "Цена AAPL: $270.00 (заглушка - нет данных в API)"
    )


def test_get_stock_prices_price_is_false() -> None:
    """Тест когда price есть но False"""
    mock_response = Mock()
    mock_response.json.return_value = {"price": False}  # False = False
    mock_response.raise_for_status = Mock()

    with patch('src.utils.requests.get', return_value=mock_response):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["GOOGL"])

    # False = False -> попадает в else
    assert result[0]["price"] == 142.0  # fallback
    mock_logger.warning.assert_called_with(
        "Цена GOOGL: $142.00 (заглушка - нет данных в API)"
    )


def test_get_stock_prices_price_is_zero() -> None:
    """Тест когда price = 0"""
    mock_response = Mock()
    mock_response.json.return_value = {"price": "0"}
    mock_response.raise_for_status = Mock()

    with patch('src.utils.requests.get', return_value=mock_response):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["MSFT"])

    assert result[0]["price"] == 0.0

    # assert_any_call проверяет что такой вызов БЫЛ (не обязательно последний)
    mock_logger.info.assert_any_call("Цена MSFT: $0.00 (реальные данные)")

def test_get_stock_prices_price_is_zero_int() -> None:
    """Тест когда price = 0 как int"""
    mock_response = Mock()
    mock_response.json.return_value = {"price": 0}  # 0 = False!
    mock_response.raise_for_status = Mock()

    with patch('src.utils.requests.get', return_value=mock_response):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["AMZN"])

    # 0 = False -> попадает в else
    assert result[0]["price"] == 225.0  # fallback
    mock_logger.warning.assert_called_with(
        "Цена AMZN: $225.00 (заглушка - нет данных в API)"
    )


def test_get_stock_prices_http_error() -> None:
    """Тест HTTP ошибки - должен попасть в except requests.exceptions.HTTPError"""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")

    with patch('src.utils.requests.get', return_value=mock_response):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["AAPL"])

    assert result[0]["price"] == 270.0
    # Проверяем правильное сообщение об ошибке
    mock_logger.warning.assert_called_with(
        "Цена AAPL: $270.00 (заглушка - ошибка HTTP)"
    )


def test_get_stock_prices_network_error() -> None:
    """Тест сетевой ошибки"""
    with patch('src.utils.requests.get',
               side_effect=requests.exceptions.RequestException("Network error")):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["GOOGL"])

    assert result[0]["price"] == 142.0
    mock_logger.warning.assert_called_with(
        "Цена GOOGL: $142.00 (заглушка - ошибка подключения)"
    )


def test_get_stock_prices_general_exception() -> None:
    """Тест общего исключения - должен попасть в except (RequestException, Exception)"""
    with patch('src.utils.requests.get',
               side_effect=ValueError("Любая ошибка")):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["AAPL"])

    assert result[0]["price"] == 270.0
    mock_logger.warning.assert_called_with(
        "Цена AAPL: $270.00 (заглушка - ошибка подключения)"
    )


def test_get_stock_prices_invalid_price_format() -> None:
    """Тест когда price не число - вызовет ValueError при float()"""
    mock_response = Mock()
    mock_response.json.return_value = {"price": "not a number"}
    mock_response.raise_for_status = Mock()

    with patch('src.utils.requests.get', return_value=mock_response):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["AMZN"])

    # float("not a number") вызовет ValueError
    # который будет пойман в except (RequestException, Exception)
    assert result[0]["price"] == 225.0  # fallback
    mock_logger.warning.assert_called_with(
        "Цена AMZN: $225.00 (заглушка - ошибка подключения)"
    )


def test_get_stock_prices_json_decode_error() -> None:
    """Тест ошибки декодирования JSON"""
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status = Mock()

    with patch('src.utils.requests.get', return_value=mock_response):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["NVDA"])

    assert result[0]["price"] == 188.0
    mock_logger.warning.assert_called_with(
        "Цена NVDA: $188.00 (заглушка - ошибка подключения)"
    )


def test_get_stock_prices_timeout_error() -> None:
    """Тест таймаута"""
    with patch('src.utils.requests.get',
               side_effect=requests.exceptions.Timeout("Timeout")):
        with patch('src.utils.logger') as mock_logger:
            result = get_stock_prices(["SBER"])

    assert result[0]["price"] == 280.0
    mock_logger.warning.assert_called_with(
        "Цена SBER: $280.00 (заглушка - ошибка подключения)"
    )

# === save_report ===
"""Тесты функции save_report"""


def test_save_report(tmp_path: Path) -> None:
    """Тест сохранения отчета в файл"""
    report: Dict[str, Any] = {
        "greeting": "Добрый день",
        "cards": [],
        "top_transactions": [],
        "currency_rates": [],
        "stock_prices": []
    }
    file_name: Path = tmp_path / "report.json"
    success: bool = save_report(report, filename=str(file_name))

    assert success
    with open(file_name, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    assert data["greeting"] == "Добрый день"
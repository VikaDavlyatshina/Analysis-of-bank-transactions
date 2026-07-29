from typing import Any, Dict, List
from unittest.mock import patch

import pandas as pd

from src.views import (
    format_currency_rates,
    format_stock_prices,
    generate_financial_report,
    get_cards_summary,
    get_top_transactions,
)


def test_card_summary(sample_transactions_df: pd.DataFrame) -> None:
    """Тест расчета статистик по картам"""
    result: List[Dict[str, Any]] = get_cards_summary(sample_transactions_df)

    assert len(result) == 3

    # Создаем словарь для удобства проверки
    cards_dict: Dict[str, Dict[str, Any]] = {card["last_digits"]: card for card in result}

    assert cards_dict["4515"]["total_spent"] == 1400
    assert cards_dict["4515"]["cashback"] == 14

    assert cards_dict["7232"]["total_spent"] == 500
    assert cards_dict["7232"]["cashback"] == 5

    # Проверяем сортировку по убыванию трат
    assert result[0]["last_digits"] == "4515"  # 1400 - наибольшие траты
    assert result[1]["last_digits"] in ["7232", "3672"]  # по 500
    assert result[2]["last_digits"] in ["7232", "3672"]


def test_card_summary_empty_df() -> None:
    """Тест с пустым DataFrame"""
    empty_df: pd.DataFrame = pd.DataFrame(columns=["Сумма операции", "Номер карты"])
    result: List[Dict[str, Any]] = get_cards_summary(empty_df)

    assert result == []


def test_card_summary_no_expenses() -> None:
    """Тест, когда в DataFrame нет расходов"""
    df: pd.DataFrame = pd.DataFrame({"Сумма операции": [100, 1400, 2000], "Номер карты": ["1325", "2515", "7272"]})
    result: List[Dict[str, Any]] = get_cards_summary(df)

    assert result == []


def test_get_cards_summary_mixed_card_numbers() -> None:
    """Тест со смешанными номерами карт (пустые и непустые)"""
    df: pd.DataFrame = pd.DataFrame(
        {"Сумма операции": [-100, -200, -300, -400], "Номер карты": ["1234", "", "5678", ""]}
    )
    result: List[Dict[str, Any]] = get_cards_summary(df)

    cards_dict: Dict[str, Dict[str, Any]] = {card["last_digits"]: card for card in result}
    assert "1234" in cards_dict
    assert "" in cards_dict
    assert "5678" in cards_dict
    assert cards_dict["1234"]["total_spent"] == 100.0
    assert cards_dict["5678"]["total_spent"] == 300.0


def test_get_cards_summary_card_number_conversion() -> None:
    """Тест преобразования номера карты в строку"""
    # Проверяем что функция корректно работает с разными типами номеров
    test_cases: List[tuple[Any, str]] = [
        ("1234567812345678", "5678"),  # строка
        (1234567812345678, "5678"),  # число
        ("1234", "1234"),  # короткий номер
        ("", ""),  # пустая строка
    ]

    for card_number, expected_last_digits in test_cases:
        df: pd.DataFrame = pd.DataFrame({"Сумма операции": [-100], "Номер карты": [card_number]})
        result: List[Dict[str, Any]] = get_cards_summary(df)

        if card_number:  # Не пустой номер
            assert result[0]["last_digits"] == expected_last_digits


def test_get_cards_summary_rounding() -> None:
    """Тест округления сумм"""
    df: pd.DataFrame = pd.DataFrame({"Сумма операции": [-123.456, -789.012], "Номер карты": ["1111", "2222"]})
    result: List[Dict[str, Any]] = get_cards_summary(df)

    cards_dict: Dict[str, Dict[str, Any]] = {card["last_digits"]: card for card in result}

    # Проверяем округление до 2 знаков
    assert cards_dict["1111"]["total_spent"] == 123.46  # -123.456 → 123.46
    assert cards_dict["1111"]["cashback"] == 1.23  # 123.456 * 0.01 = 1.23456 → 1.23

    assert cards_dict["2222"]["total_spent"] == 789.01  # -789.012 → 789.01
    assert cards_dict["2222"]["cashback"] == 7.89  # 789.012 * 0.01 = 7.89012 → 7.89


def test_get_top_transactions(sample_transactions_df: pd.DataFrame) -> None:
    """Тест расчета топа транзакций"""
    result: List[Dict[str, Any]] = get_top_transactions(sample_transactions_df)

    assert len(result) == 5

    # Проверяем сортировку по убыванию трат
    assert result[0]["amount"] == 2000
    assert result[1]["amount"] == -1000
    assert result[2]["amount"] == -500


def test_get_top_transactions_default_limit(sample_transactions_df: pd.DataFrame) -> None:
    """Тест с лимитом по умолчанию (5 транзакций)"""
    result: List[Dict[str, Any]] = get_top_transactions(sample_transactions_df)  # limit=5 по умолчанию

    assert len(result) == 5

    # Проверяем порядок
    amounts: List[float] = [item["amount"] for item in result]
    assert amounts == [2000.0, -1000.0, -500.0, 500.0, -400]


def test_get_top_transactions_empty_dataframe() -> None:
    """Тест с пустым DataFrame"""
    empty_df: pd.DataFrame = pd.DataFrame(columns=["Сумма операции", "Дата операции"])
    result: List[Dict[str, Any]] = get_top_transactions(empty_df)
    assert result == []


def test_get_top_transactions_single_transaction() -> None:
    """Тест с одной транзакцией"""
    df: pd.DataFrame = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["2024-01-15"]),
            "Сумма операции": [-1000],
            "Категория": ["Еда"],
            "Описание": ["Обед"],
        }
    )

    result: List[Dict[str, Any]] = get_top_transactions(df)

    assert len(result) == 1
    assert result[0]["date"] == "15.01.2024"
    assert result[0]["amount"] == -1000.0
    assert result[0]["category"] == "Еда"
    assert result[0]["description"] == "Обед"


def test_format_currency_rates_basic() -> None:
    """Тест с обычными курсами"""
    rates: Dict[str, float] = {"USD": 90.0, "EUR": 100.0}
    result: List[Dict[str, Any]] = format_currency_rates(rates)

    # Проверяем что вернулся список
    assert isinstance(result, list)

    # Проверяем количество валют
    assert len(result) == 2

    # Проверяем первую валюту
    assert result[0]["currency"] == "USD"
    assert result[0]["rate"] == 90.0

    # Проверяем вторую валюту
    assert result[1]["currency"] == "EUR"
    assert result[1]["rate"] == 100.0


def test_format_currency_rates_empty() -> None:
    """Тест с пустыми данными"""
    # Пустой словарь
    result: List[Dict[str, Any]] = format_currency_rates({})
    assert result == []

    # None
    result = format_currency_rates(None)
    assert result == []


def test_format_stock_prices_basic() -> None:
    """Тест с обычными акциями"""
    stocks: List[Dict[str, Any]] = [
        {"stock": "AAPL", "price": 150.0, "source": "api"},
        {"stock": "GOOGL", "price": 130.0, "source": "fallback"},
    ]

    result: List[Dict[str, Any]] = format_stock_prices(stocks)

    # Проверяем структуру
    assert len(result) == 2

    # Проверяем первую акцию
    assert result[0]["stock"] == "AAPL"
    assert result[0]["price"] == 150.0

    # Проверяем что лишних полей нет
    assert "source" not in result[0]


def test_format_stock_prices_empty() -> None:
    """Тест с пустыми данными"""
    # Пустой список
    result: List[Dict[str, Any]] = format_stock_prices([])
    assert result == []

    # None
    assert result == []


def test_generate_financial_report_basic() -> None:
    """Простой тест главной функции"""
    # 1. Подготавливаем тестовые данные
    test_df: pd.DataFrame = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["2024-01-15"]),
            "Сумма операции": [-1000],
            "Валюта операции": ["RUB"],
            "Категория": ["Еда"],
            "Описание": ["Обед"],
            "Номер карты": ["1234"],
            "Статус": ["OK"],
        }
    )

    test_date: str = "2024-01-15 10:00:00"

    # 2. Подменяем все зависимости
    with patch("src.views.report.get_greeting") as mock_greeting, patch(
        "src.views.report.load_user_settings"
    ) as mock_settings, patch("src.views.report.get_currency_rates") as mock_rates, patch(
        "src.views.report.get_stock_prices"
    ) as mock_stocks:
        # Настраиваем моки
        mock_greeting.return_value = "Доброе утро"
        mock_settings.return_value = {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}
        mock_rates.return_value = {"USD": 90.0}
        mock_stocks.return_value = [{"stock": "AAPL", "price": 150.0}]

        # 3. Вызываем функцию
        result: Dict[str, Any] = generate_financial_report(test_df, test_date)

        # 4. Проверяем структуру отчета
        assert "greeting" in result
        assert "cards" in result
        assert "top_transactions" in result
        assert "currency_rates" in result
        assert "stock_prices" in result

        # 5. Проверяем конкретные значения
        assert result["greeting"] == "Доброе утро"
        assert isinstance(result["cards"], list)
        assert isinstance(result["top_transactions"], list)
        assert isinstance(result["currency_rates"], list)
        assert isinstance(result["stock_prices"], list)

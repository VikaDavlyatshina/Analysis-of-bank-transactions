from typing import Any, Dict, List

import pytest

from src.services import find_phone_numbers, investment_bank, simple_search

# ==== investment_bank ====
"""Тесты функции investment_bank"""


@pytest.mark.parametrize(
    "month, limit, expected",
    [
        ("2025-12", 50, 58.66),
        ("2025-12", 10, 8.66),
        ("2025-12", 100, 108.66),
    ],
)
def test_investment_bank_ok(invest_data: List[Dict[str, Any]], month: str, limit: int, expected: float) -> None:
    """Тест с правильными лимитами."""
    total = investment_bank(month, invest_data, limit)
    # Допускаем небольшую погрешность в расчетах
    assert abs(total - expected) < 0.01


@pytest.mark.parametrize("bad_limit", [5, 20, 200, 0])
def test_investment_bank_bad_limit(invest_data: List[Dict[str, Any]], bad_limit: int) -> None:
    """Тест с неправильными лимитами."""
    with pytest.raises(ValueError, match=f"Неверный лимит {bad_limit}"):
        investment_bank("2025-12", invest_data, bad_limit)


def test_investment_bank_empty() -> None:
    """Тест с пустым списком."""
    result = investment_bank("2025-12", [], 10)
    assert result == 0.0


# ==== simple_search ====
"""Тесты функции simple_search"""


@pytest.mark.parametrize(
    "search_text, expected_count",
    [
        ("хлеб", 1),
        ("ХЛЕБ", 1),  # Большие буквы
        ("супермаркет", 1),
        ("молоко", 1),
        ("еда", 2),  # 2 транзакции с категорией "Еда"
        ("Не указано", 0),
    ],
)
def test_simple_search_find(
    search_data: List[Dict[str, Any]], search_text: str, expected_count: int, no_save: bool
) -> None:
    """Тест поиска транзакций."""
    result = simple_search(search_data, search_text)
    assert result["found_count"] == expected_count
    assert result["search_string"] == search_text

    # Дополнительная проверка для найденных результатов
    if expected_count > 0:
        assert "Найдено" in result["message"]
    else:
        assert result["found_count"] == 0


def test_simple_search_empty_string(no_save: bool) -> None:
    """Тест с пустой строкой поиска."""
    data = [{"Описание": "Купил хлеб"}]
    result = simple_search(data, "")

    assert result["found_count"] == 0
    assert result.get("skip_save") is True
    assert "Строка поиска пуста" in result["message"]


def test_simple_search_no_data(no_save: bool) -> None:
    """Тест с пустым списком транзакций."""
    result = simple_search([], "хлеб")
    assert result["found_count"] == 0
    assert len(result["transactions"]) == 0


@pytest.mark.parametrize(
    "description, search_string, should_find",
    [
        ("Покупка в O'Reilly", "O'Reilly", True),
        ("Кафе Starbucks®", "Starbucks", True),
        ("Кафе Starbucks®", "Starbucks®", True),
    ],
)
def test_simple_search_special_characters(
    description: str, search_string: str, should_find: bool, no_save: bool
) -> None:
    """Тест поиска со специальными символами."""
    transactions = [{"Описание": description, "Категория": "Тест"}]
    result = simple_search(transactions, search_string)

    expected_count = 1 if should_find else 0
    assert result["found_count"] == expected_count


# ==== find_phone_numbers ====
"""Тесты функции find_phone_numbers"""


@pytest.mark.parametrize(
    "text, should_find",
    [
        ("Позвоните +7 921 123-45-67", True),
        ("Оплата услуг", False),
        ("Номер 89211234567", True),
        ("Без телефона", False),
    ],
)
def test_find_phone_numbers_basic(text: str, should_find: bool, no_save: bool) -> None:
    """Тест поиска телефонных номеров."""
    data = [{"Описание": text}]
    result = find_phone_numbers(data)

    if should_find:
        assert result["found_count"] == 1
        assert result["total_phones_found"] == 1
        assert "найдено" in result["message"].lower()
    else:
        assert result["found_count"] == 0
        assert result["total_phones_found"] == 0


def test_find_phone_numbers_multiple(no_save: bool) -> None:
    """Тест с несколькими номерами в одной строке."""
    data = [{"Описание": "Звоните +7 999 888-77-66 или 8-800-555-35-35"}]
    result = find_phone_numbers(data)

    assert result["found_count"] == 1  # Одна транзакция
    assert result["total_phones_found"] == 2  # Два номера
    assert result["transactions"][0]["Количество_найденных_номеров"] == 2
    assert len(result["transactions"][0]["Найденные_телефоны"]) == 2


def test_find_phone_numbers_structure(no_save: bool) -> None:
    """Тест структуры результата."""
    data = [{"Описание": "Позвоните +7 921 123-45-67"}]
    result = find_phone_numbers(data)

    # Проверяем обязательные поля
    required_fields = [
        "service",
        "status",
        "found_count",
        "found_transactions_count",
        "total_phones_found",
        "transactions",
        "message",
    ]
    for field in required_fields:
        assert field in result

    # Проверяем совместимость
    assert result["found_count"] == result["found_transactions_count"]

    # Проверяем структуру транзакции
    if result["transactions"]:
        transaction = result["transactions"][0]
        assert "Найденные_телефоны" in transaction
        assert "Количество_найденных_номеров" in transaction


def test_find_phone_numbers_empty(no_save: bool) -> None:
    """Тест с пустым списком."""
    result = find_phone_numbers([])
    assert result["found_count"] == 0
    assert result["total_phones_found"] == 0
    assert len(result["transactions"]) == 0


@pytest.mark.parametrize(
    "phone_format",
    [
        "+7 921 123-45-67",
        "8-921-123-45-67",
        "89211234567",
        "8(921)123-45-67",
    ],
)
def test_find_phone_numbers_formats(phone_format: str, no_save: bool) -> None:
    """Тест разных форматов телефонных номеров."""
    transactions = [{"Описание": f"Телефон: {phone_format}"}]
    result = find_phone_numbers(transactions)

    assert result["found_count"] == 1
    assert result["total_phones_found"] == 1


@pytest.mark.parametrize(
    "transactions_data, expected_found_count",
    [
        ([], 0),
        ([{"Описание": "Обычная транзакция"}], 0),
        (
            [
                None,  # None вместо словаря
                {"not_description": "нет поля Описание"},  # Нет поля "Описание"
                {"Описание": None},  # None вместо строки
                {"Описание": 123},  # Число вместо строки
                {"Описание": "Нормальная транзакция +7 999 888-77-66"},  # Корректная
            ],
            1,
        ),
    ],
)
def test_find_phone_numbers_edge_cases(transactions_data: List[Any], expected_found_count: int, no_save: bool) -> None:
    """Тест граничных случаев."""
    result = find_phone_numbers(transactions_data)
    assert result["found_count"] == expected_found_count

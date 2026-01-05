from pathlib import Path
from typing import Any, Dict, List
import pytest

from src.services import find_phone_numbers, investment_bank, simple_search


@pytest.mark.parametrize(
    "month, limit, expected",
    [
        ("2025-12", 50, 58.66),
        ("2025-12", 10, 8.66),
        ("2025-12", 100, 108.66),
    ]
)
def test_investment_bank(transactions: List[Dict[str, Any]], month: str, limit: int, expected: float) -> None:
    """Тестирует функцию инвестиционного банка с различными лимитами."""
    total: float = investment_bank(month, transactions, limit)
    assert abs(total - expected) < 0.01


@pytest.mark.parametrize(
    "invalid_limit",
    [5, 20, 200, 0]
)
def test_investment_bank_invalid_limit(transactions: List[Dict[str, Any]], invalid_limit: int) -> None:
    """Тест с некорректными лимитами."""
    with pytest.raises(ValueError, match=f"Неверный лимит {invalid_limit}"):
        investment_bank("2025-12", transactions, invalid_limit)


def test_investment_bank_empty_transactions() -> None:
    """Тест с пустым списком транзакций."""
    result = investment_bank("2025-12", [], 10)
    assert result == 0.0


# -------------------
# ТЕСТЫ SIMPLE_SEARCH
# -------------------
@pytest.fixture
def simple_transactions() -> List[Dict[str, Any]]:
    """Фикстура с транзакциями для simple_search."""
    return [
        {"Описание": "Купил хлеб", "Категория": "Еда"},
        {"Описание": "Оплата интернета", "Категория": "Связь"},
        {"Описание": "Покупка в магазине", "Категория": "Супермаркет"},
        {"Описание": "Обед в кафе", "Категория": "Ресторан"},
        {"Описание": "Молоко", "Категория": "Еда"},
    ]


@pytest.mark.parametrize(
    "search_string, expected_count, expected_description",
    [
        ("хлеб", 1, "Купил хлеб"),
        ("ХЛЕБ", 1, "Купил хлеб"),  # регистронезависимый
        ("супермаркет", 1, "Покупка в магазине"),
        ("молоко", 1, "Молоко"),
        ("еда", 2, None),  # не проверяем конкретное описание, только количество
        ("несуществующее", 0, None),
    ]
)
def test_simple_search_basic(
        mock_report_decorator,
        simple_transactions: List[Dict[str, Any]],
        search_string: str,
        expected_count: int,
        expected_description: str
) -> None:
    """Параметризованный тест simple_search."""
    from src.services import simple_search

    result = simple_search(simple_transactions, search_string)

    assert result["found_count"] == expected_count
    assert result["search_string"] == search_string
    assert "Найдено" in result["message"]

    if expected_description:
        assert result["transactions"][0]["Описание"] == expected_description


@pytest.mark.parametrize(
    "transactions_data, search_string, expected_skip_save, expected_message_contains",
    [
        ([{"Описание": "Купил хлеб"}], "", True, "Строка поиска пуста"),
        ([], "хлеб", False, None),
    ]
)
def test_simple_search_edge_cases(
        mock_report_decorator,
        transactions_data: List[Dict[str, Any]],
        search_string: str,
        expected_skip_save: bool,
        expected_message_contains: str
) -> None:
    """Тест граничных случаев simple_search."""
    from src.services import simple_search

    result = simple_search(transactions_data, search_string)

    if expected_skip_save:
        assert result.get("skip_save") == expected_skip_save
    if expected_message_contains:
        assert expected_message_contains in result["message"]


@pytest.mark.parametrize(
    "description, search_string, should_find",
    [
        ("Покупка в O'Reilly", "O'Reilly", True),
        ("Кафе Starbucks®", "Starbucks", True),
        ("Кафе Starbucks®", "Starbucks®", True),
    ]
)
def test_simple_search_special_characters(
        mock_report_decorator,
        description: str,
        search_string: str,
        should_find: bool
) -> None:
    """Тест поиска со специальными символами."""
    from src.services import simple_search

    transactions = [{"Описание": description, "Категория": "Тест"}]
    result = simple_search(transactions, search_string)

    expected_count = 1 if should_find else 0
    assert result["found_count"] == expected_count


# -------------------
# ТЕСТЫ FIND_PHONE_NUMBERS
# -------------------
@pytest.fixture
def phone_transactions() -> List[Dict[str, Any]]:
    """Фикстура с транзакциями для поиска телефонов."""
    return [
        {"Описание": "Позвоните +7 921 123-45-67"},
        {"Описание": "Оплата услуг"},
        {"Описание": "Телефон: 8-921-123-45-67"},
        {"Описание": "Номер 89211234567"},
    ]


@pytest.mark.parametrize(
    "description, expected_found_count, expected_phones_count",
    [
        ("Позвоните +7 921 123-45-67", 1, 1),
        ("Оплата услуг", 0, 0),
        ("Звоните +7 999 888-77-66 или 8-800-555-35-35", 1, 2),
        ("Без телефона", 0, 0),
    ]
)
def test_find_phone_numbers_basic(
        mock_report_decorator,
        description: str,
        expected_found_count: int,
        expected_phones_count: int
) -> None:
    """Параметризованный тест find_phone_numbers."""
    from src.services import find_phone_numbers

    transactions = [{"Описание": description}]
    result = find_phone_numbers(transactions)

    assert result["found_count"] == expected_found_count
    assert result["total_phones_found"] == expected_phones_count

    if expected_found_count > 0:
        assert result["transactions"][0]["Описание"] == description
        assert "найдено" in result["message"].lower()


@pytest.mark.parametrize(
    "phone_format",
    [
        "+7 921 123-45-67",
        "8-921-123-45-67",
        "89211234567",
        "8(921)123-45-67",
    ]
)
def test_find_phone_numbers_formats(
        mock_report_decorator,
        phone_format: str
) -> None:
    """Тест разных форматов телефонных номеров."""
    from src.services import find_phone_numbers

    transactions = [{"Описание": f"Телефон: {phone_format}"}]
    result = find_phone_numbers(transactions)

    assert result["found_count"] == 1
    assert result["total_phones_found"] == 1


def test_find_phone_numbers_structure(mock_report_decorator) -> None:
    """Тест структуры возвращаемых данных."""
    from src.services import find_phone_numbers

    transactions = [{"Описание": "Позвоните +7 921 123-45-67"}]
    result = find_phone_numbers(transactions)

    # Проверяем обязательные поля
    required_fields = [
        "service", "status", "found_count", "found_transactions_count",
        "total_phones_found", "transactions", "message"
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


@pytest.mark.parametrize(
    "transactions_data, expected_found_count",
    [
        ([], 0),
        ([{"Описание": "Обычная транзакция"}], 0),
        ([
             None,
             {"not_description": "нет поля Описание"},
             {"Описание": None},
             {"Описание": 123},
             {"Описание": "Нормальная транзакция +7 999 888-77-66"},
         ], 1),
    ]
)
def test_find_phone_numbers_edge_cases(
        mock_report_decorator,
        transactions_data: List[Any],
        expected_found_count: int
) -> None:
    """Тест граничных случаев find_phone_numbers."""
    from src.services import find_phone_numbers

    result = find_phone_numbers(transactions_data)
    assert result["found_count"] == expected_found_count


# -------------------
# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
# -------------------
@pytest.mark.integration
@pytest.mark.parametrize(
    "service_name, service_func, transactions, kwargs, expected_found_count",
    [
        (
                "simple_search",
                simple_search,
                [{"Описание": "Купил хлеб"}],
                {"search_string": "хлеб"},
                1
        ),
        (
                "find_phone_numbers",
                find_phone_numbers,
                [{"Описание": "Позвоните +7 921 123-45-67"}],
                {},
                1
        ),
    ]
)
def test_integration_services_real(
        tmp_path: Path,
        service_name: str,
        service_func: callable,
        transactions: List[Dict[str, Any]],
        kwargs: Dict[str, Any],
        expected_found_count: int
) -> None:
    """Интеграционный тест сервисов с реальным сохранением."""
    # Добавляем директорию для отчетов в kwargs
    kwargs["reports_dir"] = tmp_path

    # Вызываем функцию
    result = service_func(transactions, **kwargs)

    # Проверяем логику
    assert result["found_count"] == expected_found_count

    # Проверяем что файлы создаются (если есть результаты)
    report_files = list(tmp_path.glob(f"*{service_name}*.json"))
    if expected_found_count > 0:
        assert len(report_files) > 0
    else:
        # Для пустых результатов файл может не создаваться
        pass


# -------------------
# ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ
# -------------------
def test_find_phone_numbers_multiple_numbers(mock_report_decorator) -> None:
    """Тест нескольких номеров в одной транзакции."""
    from src.services import find_phone_numbers

    transactions = [{"Описание": "Звоните +7 999 888-77-66 или 8-800-555-35-35"}]
    result = find_phone_numbers(transactions)

    assert result["found_count"] == 1
    assert result["total_phones_found"] == 2
    assert result["transactions"][0]["Количество_найденных_номеров"] == 2
    assert len(result["transactions"][0]["Найденные_телефоны"]) == 2
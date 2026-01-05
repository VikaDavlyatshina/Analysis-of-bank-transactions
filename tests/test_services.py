import json
from typing import List, Dict, Any
from pathlib import Path

import pytest

from src.services import find_phone_numbers, investment_bank, simple_search


@pytest.mark.parametrize(
    "month, limit, expected",
    [
        ("2025-12", 50, 50),
        ("2025-12", 10, 10),
        ("2025-12", 100, 200),
    ],
)
def test_investment_bank(
        transactions: List[Dict[str, Any]],
        month: str,
        limit: int,
        expected: float
) -> None:
    """Тестирует функцию инвестиционного банка с различными лимитами."""
    total: float = investment_bank(month, transactions, limit)
    assert total == expected


@pytest.mark.parametrize(
    "search_string, expected_count",
    [
        ("Покупка", 1),       # поиск по описанию
        ("Еда", 1),           # поиск по категории
        ("", 0),              # пустой поисковый запрос
        ("Не найдено", 0),    # нет совпадений
    ],
)
def test_simple_search(
        transactions: List[Dict[str, Any]],
        search_string: str,
        expected_count: int,
        tmp_path: Path
) -> None:
    """Тестирует простой поиск транзакций по строке."""
    result: Dict[str, Any] = simple_search(transactions, search_string, reports_dir=tmp_path)
    assert result["found_count"] == expected_count

    report_file: Path = tmp_path / "simple_search_report.json"

    if expected_count > 0 or not search_string.strip():
        # Файл должен существовать
        assert report_file.exists()

        with open(report_file, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)

        assert data["found_count"] == result["found_count"]
    else:
        # Файл может отсутствовать
        assert not report_file.exists()


@pytest.mark.parametrize(
    "transactions_input, expected_count",
    [
        ([{"Описание": "Позвоните +7 921 123-45-67"}], 1),  # один телефон
        ([{"Описание": "Никаких телефонов"}], 0),  # нет номеров
        ([], 0),  # пустой список
    ],
)
def test_find_phone_numbers(
        transactions_input: List[Dict[str, Any]],
        expected_count: int,
        tmp_path: Path
) -> None:
    """Тестирует поиск телефонных номеров в описаниях транзакций."""
    result: Dict[str, Any] = find_phone_numbers(transactions_input, reports_dir=tmp_path)
    assert result["found_count"] == expected_count

    # Проверяем, что отчет создался
    report_file: Path = tmp_path / "find_phone_numbers_report.json"
    assert report_file.exists()

    with open(report_file, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    assert data["found_count"] == result["found_count"]
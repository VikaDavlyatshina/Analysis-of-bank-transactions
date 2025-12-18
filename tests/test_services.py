import json
import pytest


from src.services import investment_bank, simple_search, find_phone_numbers


@pytest.mark.parametrize(
    "month, limit, expected",
    [
        ("2025-12", 50, 50),
        ("2025-12", 10, 10),
        ("2025-12", 100, 200),

    ]
)
def test_investment_bank(transactions, month, limit, expected):
    total = investment_bank(month, transactions, limit)
    assert total == expected


@pytest.mark.parametrize(
    "search_string, expected_count",
    [
        ("Покупка", 1),      # поиск по описанию
        ("Еда", 1),          # поиск по категории
        ("", 0),             # пустой поисковый запрос
        ("Не найдено", 0)    # нет совпадений
    ]
)
def test_simple_search(transactions, search_string, expected_count, tmp_path):
    result = simple_search(transactions, search_string, reports_dir=tmp_path)
    assert result["found_count"] == expected_count

    # Проверяем, что отчет создался
    report_file = tmp_path / "simple_search_report.json"
    assert report_file.exists()
    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["found_count"] == result["found_count"]


@pytest.mark.parametrize(
    "transactions_input, expected_count",
    [
        ([{"Описание": "Позвоните +7 921 123-45-67"}], 1),  # один телефон
        ([{"Описание": "Никаких телефонов"}], 0),          # нет номеров
        ([], 0)                                           # пустой список
    ]
)
def test_find_phone_numbers(transactions_input, expected_count, tmp_path):
    result = find_phone_numbers(transactions_input, reports_dir=tmp_path)
    assert result["found_count"] == expected_count

    # Проверяем, что отчет создался
    report_file = tmp_path / "find_phone_numbers_report.json"
    assert report_file.exists()
    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["found_count"] == result["found_count"]

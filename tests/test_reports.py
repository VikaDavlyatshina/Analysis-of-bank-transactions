import json
from src.reports import spending_by_category, report_to_file
import pytest

@pytest.mark.parametrize(
    "category, expected_months, expected_total",
    [
        ("Еда", 3, 950),
        ("Транспорт", 1, 200),
        ("Развлечения", 0, 0)
    ]
)
def test_spending_by_category(sample_data_for_report, category, expected_months, expected_total):
    result = spending_by_category(sample_data_for_report, category=category)


    if expected_months == 0:
        assert "Нет данных за период" in result["Месяц"].values[0]
        assert result["Сумма трат"].iloc[0] == 0
    else:

        actual_months = result.loc[result["Месяц"] != "Общий итог за 3 месяца", "Месяц"].nunique()
        assert actual_months == expected_months

        # Итоговая сумма
        total_row = result.iloc[-1]
        assert total_row["Сумма трат"] == expected_total
        assert total_row["Месяц"] == "Общий итог за 3 месяца"

def test_report_to_file_creates_file(tmp_path):
    @report_to_file(filename=tmp_path / "report.json")
    def dummy_func():
        return [{"a": 1, "b": 2}]

    result = dummy_func()

    # Проверяем результат функции
    assert result == [{"a": 1, "b": 2}]

    # Проверяем, что файл создался и содержит корректные данные
    file_path = tmp_path / "report.json"
    assert file_path.exists()

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data == [{"a": 1, "b": 2}]
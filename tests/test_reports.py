import json
import pandas as pd
from src.reports import spending_by_category, report_to_file
import pytest


def test_spending_by_category_basic():
    # Создаём простой DataFrame с транзакциями
    df = pd.DataFrame({
        "Дата операции": pd.to_datetime([
            "2025-12-01", "2025-12-05", "2025-11-20", "2025-10-15"
        ]),
        "Сумма операции": [-100, -50, -200, -300],
        "Категория": ["Еда", "Еда", "Транспорт", "Еда"]
    })

    # Вызываем функцию
    result = spending_by_category(df, "Еда", date="2025-12-31")

    # Проверяем, что результат содержит только нужные строки
    assert not result.empty
    assert all(result["Категория"] == "Еда")

    # Проверяем, что общий итог присутствует
    assert "Общий итог за 3 месяца" in result["Месяц"].values


def test_spending_by_category_no_data():
    df = pd.DataFrame({
        "Дата операции": pd.to_datetime(["2025-12-01", "2025-12-05"]),
        "Сумма операции": [-100, -50],
        "Категория": ["Транспорт", "Транспорт"]
    })

    result = spending_by_category(df, "Еда", date="2025-12-31")

    # Должна вернуться строка с "Нет данных за период"
    assert result.iloc[0]["Месяц"] == "Нет данных за период"
    assert result.iloc[0]["Сумма трат"] == 0

def test_spending_by_category_ignore_income():
    df = pd.DataFrame({
        "Дата операции": pd.to_datetime(["2025-12-01", "2025-12-05"]),
        "Сумма операции": [1000, -50],  # 1000 это доход
        "Категория": ["Еда", "Еда"]
    })

    result = spending_by_category(df, "Еда", date="2025-12-31")

    # Доходная операция должна быть проигнорирована
    assert result["Сумма трат"].sum() == 100
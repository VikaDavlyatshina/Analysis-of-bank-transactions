from typing import List

import pandas as pd

from src.reports import spending_by_category


def test_basic_functionality(create_test_dataframe) -> None:
    """
    Базовый тест: одна транзакция по категории.
    """
    df = create_test_dataframe(dates=["2024-01-05"], amounts=[-100], categories=["Еда"])

    result = spending_by_category(df, "Еда", date="2024-01-31")

    # Основные проверки
    assert not result.empty, "Результат не должен быть пустым"
    assert "Общий итог за 3 месяца" in result["Месяц"].values, "Должна быть итоговая строка"
    assert result.iloc[-1]["Сумма трат"] == 100.0, "Сумма должна быть абсолютным значением"

    # Дополнительно: проверяем структуру результата
    expected_columns = ["Месяц", "Сумма трат", "Количество операций", "Средний чек", "Категория"]
    assert list(result.columns) == expected_columns, f"Должны быть колонки: {expected_columns}"


def test_multiple_transactions_same_month(create_test_dataframe) -> None:
    """
    Тест нескольких транзакций в одном месяце.

    Что проверяем:
    1. Суммируются все расходы за месяц
    2. Правильно считается количество операций
    3. Корректно вычисляется средний чек
    """
    df = create_test_dataframe(
        dates=["2024-01-05", "2024-01-10", "2024-01-15"], amounts=[-100, -200, -300], categories=["Еда", "Еда", "Еда"]
    )

    result = spending_by_category(df, "Еда", date="2024-01-31")

    total_row = result[result["Месяц"] == "Общий итог за 3 месяца"]

    assert total_row.iloc[0]["Сумма трат"] == 600.0, "Сумма: 100 + 200 + 300 = 600"
    assert total_row.iloc[0]["Количество операций"] == 3, "3 расходные операции"
    assert total_row.iloc[0]["Средний чек"] == 200.0, "Средний чек: 600 / 3 = 200"


def test_no_transactions_for_category(create_test_dataframe) -> None:
    """
    Тест когда нет транзакций по указанной категории.
    """
    df = create_test_dataframe(dates=["2024-01-05"], amounts=[-100], categories=["Транспорт"])  # Не "Еда"

    result = spending_by_category(df, "Еда", date="2024-01-31")

    assert len(result) == 0
    assert result.empty, "Если нет операций по категории, результат должен быть пустым"



def test_empty_dataframe() -> None:
    """
    Тест с пустым DataFrame
    """
    df = pd.DataFrame(columns=["Дата операции", "Сумма операции", "Категория"])

    result = spending_by_category(df, "Еда", date="2024-01-31")
    assert result.empty, "Если нет операций по категории, результат должен быть пустым"



def test_income_transactions_ignored(create_test_dataframe) -> None:
    """
    Тест проверки, что положительные суммы(Доходы) игнорируются

    Что проверяем:
    1. Положительные суммы (доходы) не учитываются
    2. Учитываются только отрицательные суммы (расходы)
    """
    df = create_test_dataframe(
        dates=["2024-01-05", "2024-01-10", "2024-01-15"],
        amounts=[-100, 500, -50],  # 500 - доход, должен игнорироваться
        categories=["Еда", "Еда", "Еда"],
    )

    result = spending_by_category(df, "Еда", date="2024-01-31")

    total_row = result[result["Месяц"] == "Общий итог за 3 месяца"]

    assert total_row.iloc[0]["Сумма трат"] == 150.0, "Только расходы: 100 + 50 = 150"
    assert total_row.iloc[0]["Количество операций"] == 2, "Только 2 расходные операции"


def test_case_insensitive_category_matching(create_test_dataframe) -> None:
    """
    Тест сравнения категорий в разном регистре.

    Что проверяем:
    1. "Еда", "ЕДА", "еда" считаются одной категорией
    2. Поиск работает независимо от регистра
    """
    df = create_test_dataframe(
        dates=["2024-01-05", "2024-01-10"], amounts=[-100, -200], categories=["ЕДА", "еда"]  # Разный регистр
    )

    # Проверяем все варианты регистра
    test_cases = ["Еда", "ЕДА", "еда"]

    for category in test_cases:
        result = spending_by_category(df, category, date="2024-01-31")
        total_row = result[result["Месяц"] == "Общий итог за 3 месяца"]
        assert total_row.iloc[0]["Сумма трат"] == 300.0, f"Категория '{category}' должна найти обе транзакции"


def test_multiple_months_grouping(create_test_dataframe) -> None:
    """
    Тест группировки транзакций по разным месяцам.

    Что проверяем:
    1. Транзакции группируются по месяцам
    2. Суммы считаются отдельно для каждого месяца
    3. Правильный общий итог
    """
    df = create_test_dataframe(
        dates=[
            "2024-01-05",  # Январь
            "2024-01-10",  # Январь
            "2024-02-15",  # Февраль
            "2024-03-20",  # Март
        ],
        amounts=[-100, -50, -200, -300],
        categories=["Еда", "Еда", "Еда", "Еда"],
    )

    result = spending_by_category(df, "Еда", date="2024-03-31")

    # Должно быть: 3 месяца данных + итог = 4 строки
    assert len(result) == 4

    # Проверяем итог
    total_row = result[result["Месяц"] == "Общий итог за 3 месяца"]
    assert total_row.iloc[0]["Сумма трат"] == 650.0, "Общая сумма: 100 + 50 + 200 + 300 = 650"
    assert total_row.iloc[0]["Количество операций"] == 4, "Всего 4 операции"


def test_category_name_stripping(create_test_dataframe) -> None:
    """
    Тест, проверяющий обработку пробелов в названиях категорий.

    Что проверяем:
    1. Пробелы в начале и конце названий обрезаются
    2. Работает с разными типами пробелов
    """
    # Несколько тестовых случаев с разными пробелами
    test_cases = [
        ("  Еда  ", "Еда"),  # Пробелы с обеих сторон
        ("Еда  ", "Еда"),  # Пробелы справа
        ("  Еда", "Еда"),  # Пробелы слева
        ("\tЕда\n", "Еда"),  # Табуляция и переносы строк
    ]

    for df_category, param_category in test_cases:
        df = create_test_dataframe(dates=["2024-01-05"], amounts=[-100], categories=[df_category])

        result = spending_by_category(df, param_category, date="2024-01-31")
        total_row = result[result["Месяц"] == "Общий итог за 3 месяца"]

        assert (
            total_row.iloc[0]["Сумма трат"] == 100.0
        ), f"Должны обрезаться пробелы: '{df_category}' -> '{param_category}'"


def test_invalid_date_format(create_test_dataframe) -> None:
    """
    Тест обработки некорректного формата даты.
    """
    df = create_test_dataframe(dates=["2024-01-05"], amounts=[-100], categories=["Еда"])

    # Некорректный формат даты (не YYYY-MM-DD)
    result = spending_by_category(df, "Еда", date="2024/01/31")

    assert result.empty, "Если нет операций по категории, результат должен быть пустым"


def test_boundary_dates(create_test_dataframe) -> None:
    """
    Тест на граничные даты (первое и последнее число месяца).

    Что проверяем:
    1. Транзакции на 1-е число месяца учитываются
    2. Транзакции на последнее число месяца учитываются
    3. Период расчета работает корректно
    """
    df = create_test_dataframe(
        dates=[
            "2024-01-01",  # Первое января - должно попасть
            "2024-01-31",  # Последнее января - должно попасть
            "2024-02-01",  # Первое февраля - должно попасть
        ],
        amounts=[-100, -200, -300],
        categories=["Еда", "Еда", "Еда"],
    )

    # Отчет на 1 марта (включает январь и февраль)
    result = spending_by_category(df, "Еда", date="2024-03-01")
    total_row = result[result["Месяц"] == "Общий итог за 3 месяца"]

    assert total_row.iloc[0]["Сумма трат"] == 600.0, "Должны учитываться все даты"
    assert total_row.iloc[0]["Количество операций"] == 3, "Должны учитываться все 3 операции"


def test_period_calculation(create_test_dataframe) -> None:
    """
    Тест расчета 3-месячного периода.

    Что проверяем:
    1. Берется только последние 3 полных месяца от указанной даты
    2. Транзакции старше 3 месяцев не учитываются
    3. Транзакции после даты отчета не учитываются
    """
    df = create_test_dataframe(
        dates=[
            "2023-12-31",  # Декабрь - НЕ должен попасть (больше 3 месяцев назад)
            "2024-01-05",  # Январь - должен попасть
            "2024-02-10",  # Февраль - должен попасть
            "2024-03-15",  # Март - должен попасть
            "2024-04-01",  # Апрель - НЕ должен попасть (после даты отчета)
        ],
        amounts=[-400, -100, -200, -300, -500],
        categories=["Еда", "Еда", "Еда", "Еда", "Еда"],
    )

    # Отчет до 31 марта 2024
    result = spending_by_category(df, "Еда", date="2024-03-31")

    total_row = result[result["Месяц"] == "Общий итог за 3 месяца"]

    # Только январь, февраль, март: 100 + 200 + 300 = 600
    assert total_row.iloc[0]["Сумма трат"] == 600.0, "Только последние 3 месяца: 100 + 200 + 300 = 600"
    assert total_row.iloc[0]["Количество операций"] == 3, "Только 3 транзакции попадают в период"

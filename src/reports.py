from datetime import datetime
from functools import wraps
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta


def report_to_file(filename=None):
    """
    Простой декоратор для записи отчетов в файл
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Вызываем оригинальную функцию
            result = func(*args, **kwargs)

            # Создаем имя файла
            if filename is None:
                # Автоматическое имя: функция_дата_время.txt
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{func.__name__}_{current_time}.txt"
            else:
                file_name = filename

            # Записываем результат в файл
            with open(file_name, "w", encoding="utf-8") as f:
                f.write("ОТЧЕТ\n")
                f.write("=" * 40 + "\n")

                if isinstance(result, pd.DataFrame):
                    if result.empty:
                        f.write("Нет данных\n")
                    else:
                        f.write(result.to_string(index=False))
                else:
                    f.write(str(result))

            print(f"Отчет сохранен в файл: {file_name}")
            return result

        return wrapper

    return decorator


@report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Простая версия функции трат по категории
    """
    # Копируем данные
    df = transactions.copy()

    # Преобразуем даты
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    # Определяем дату отчета
    if date is None:
        end_date = datetime.now()
    else:
        end_date = datetime.strptime(date, "%Y-%m-%d")

    # Вычисляем дату 3 месяца назад
    start_date = end_date - relativedelta(months=3)

    # Фильтруем данные
    filtered = df[
        (df["Дата операции"] >= start_date)
        & (df["Дата операции"] <= end_date)
        & (df["Категория"] == category)
        & (df["Сумма операции"] < 0)  # траты
    ]

    if filtered.empty:
        return pd.DataFrame()

    # Группируем по месяцам
    filtered["Месяц"] = filtered["Дата операции"].dt.strftime("%Y-%m")

    result = filtered.groupby("Месяц").agg({"Сумма операции": ["sum", "count"]}).reset_index()

    # Упрощаем названия колонок
    result.columns = ["Месяц", "Сумма трат", "Количество операций"]
    result["Сумма трат"] = result["Сумма трат"].abs()

    return result

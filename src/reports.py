import json
from datetime import datetime
from functools import wraps
from typing import Callable, Optional, Any

import pandas as pd
from dateutil.relativedelta import relativedelta

from config import REPORTS_DIR, setup_reports_logger

# Создаём logger
logger = setup_reports_logger()


def report_to_file(func: Optional[Callable[..., Any]] = None, *, filename: Optional[str] = None) -> Callable[..., Any]:
    """
    Декоратор для сохранения результата отчёта в JSON-файл.
    Может использоваться:
    @report_to_file
    @report_to_file("my_report.json")
    """

    def decorator(inner_func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(inner_func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # Вызываем оригинальную функцию
                result = inner_func(*args, **kwargs)

                # Создаем имя файла
                if filename is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"report_{inner_func.__name__}_{timestamp}.json"
                else:
                    file_name = filename

                file_path = REPORTS_DIR / file_name

                # Сохраняем результат
                try:
                    if isinstance(result, pd.DataFrame):
                        data = result.to_dict(orient="records")
                    else:
                        data = result

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    logger.info(f"Отчет сохранен: {file_path}")

                except Exception as e:
                    logger.error(f"Ошибка сохранения отчёта: {e}")
                    raise

                return result

            except Exception as e:
                logger.error(f"Ошибка в декораторе report_to_file: {e}")
                raise

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator


@report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Функция для анализа трат по указанной категории за последние 3 месяца.
    Возвращает DataFrame с новым форматом для отчета.
    """
    try:
        logger.info(f"Запуск анализа для категории: {category}")

        if transactions is None or not isinstance(transactions, pd.DataFrame):
            logger.error("Передан некорректный DataFrame")
            raise ValueError("Передан некорректный DataFrame")

        category = category.strip()

        df = transactions.copy()
        df["Категория"] = df["Категория"].astype(str).str.strip()

        if date is None:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(date, "%Y-%m-%d")

        # Границы периода
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_date = end_date.replace(day=1) - relativedelta(months=2)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Фильтры
        mask_date = (df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)
        mask_category = df["Категория"].astype(str).str.lower() == category.lower()
        mask_expense = df["Сумма операции"] < 0

        filtered = df[mask_date & mask_category & mask_expense].copy()
        logger.info(f"Количество операций после фильтрации: {len(filtered)}")

        if filtered.empty:
            logger.warning(f"Нет трат по категории '{category}' за период")
            return pd.DataFrame(
                [
                    {
                        "Месяц": "Нет данных за период",
                        "Категория": category,
                        "Сумма трат": 0,
                        "Количество операций": 0,
                        "Средний чек": 0,
                    }
                ]
            )

        filtered["Месяц"] = filtered["Дата операции"].dt.strftime("%Y-%m")
        filtered["Расход"] = filtered["Сумма операции"].abs()

        grouped = filtered.groupby("Месяц", as_index=False).agg({"Расход": ["sum", "count"]})
        grouped.columns = ["Месяц", "Сумма трат", "Количество операций"]

        grouped["Средний чек"] = (grouped["Сумма трат"] / grouped["Количество операций"]).round(2)
        grouped["Сумма трат"] = grouped["Сумма трат"].round(2)
        grouped["Категория"] = category

        grouped = grouped.sort_values("Месяц")

        total_spent = grouped["Сумма трат"].sum()
        total_count = grouped["Количество операций"].sum()
        total_avg = (total_spent / total_count).round(2) if total_count > 0 else 0

        total_row = pd.DataFrame(
            [
                {
                    "Месяц": "Общий итог за 3 месяца",
                    "Категория": category,
                    "Сумма трат": total_spent,
                    "Количество операций": total_count,
                    "Средний чек": total_avg,
                }
            ]
        )

        result = pd.concat([grouped, total_row], ignore_index=True, axis=0)
        result = pd.DataFrame(result)
        return result

    except Exception as e:
        logger.error(f"Ошибка анализа категории '{category}': {e}")
        return pd.DataFrame(
            [
                {
                    "Месяц": f"Ошибка: {str(e)[:50]}...",
                    "Категория": category,
                    "Сумма трат": 0,
                    "Количество операций": 0,
                    "Средний чек": 0,
                }
            ]
        )

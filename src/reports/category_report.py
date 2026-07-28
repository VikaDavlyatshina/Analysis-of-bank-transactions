from datetime import datetime
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

from config import setup_reports_logger
from src.reports.decorator import report_to_file

logger = setup_reports_logger()


@report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
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

        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        start_date = end_date.replace(day=1) - relativedelta(months=2)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        mask_date = (df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)
        mask_category = df["Категория"].astype(str).str.lower() == category.lower()
        mask_expense = df["Сумма операции"] < 0

        filtered = df[mask_date & mask_category & mask_expense].copy()

        logger.info(f"Найдено операций: {len(filtered)}")

        if filtered.empty:
            logger.warning(f"Нет операций по категории '{category}' за период")
            return pd.DataFrame()

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
        return pd.DataFrame()

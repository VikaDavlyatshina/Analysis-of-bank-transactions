from typing import Any, Dict, List

import pandas as pd

from config import setup_views_logger

logger = setup_views_logger()


def get_top_transactions(df: pd.DataFrame, limit: int = 5) -> List[Dict[str, Any]]:
    logger.debug(f"Поиск крупнейших транзакций. Лимит: {limit}, всего транзакций: {len(df)}")

    if df.empty:
        logger.info("DataFrame пустой, возвращаем пустой список")
        return []

    df_sorted = df.copy()
    df_sorted["abs_amount"] = df_sorted["Сумма операции"].abs()
    df_sorted = df_sorted.sort_values("abs_amount", ascending=False)

    top_records = df_sorted.head(limit).to_dict("records")
    logger.debug(f"Отобрано {len(top_records)} крупнейших транзакций")

    result: List[Dict[str, Any]] = []

    for record in top_records:
        date_val = record.get("Дата операции")
        if isinstance(date_val, pd.Timestamp):
            date_str = date_val.strftime("%d.%m.%Y")
        else:
            date_str = str(date_val) if date_val is not None else "Нет даты"

        amount_val = record.get("Сумма операции")
        if isinstance(amount_val, (int, float)):
            amount = round(float(amount_val), 2)
        else:
            amount = 0.0

        transaction_info = {
            "date": date_str,
            "amount": amount,
            "category": str(record.get("Категория", "Не указано")),
            "description": str(record.get("Описание", "Без описания"))[:50],
        }

        result.append(transaction_info)
        logger.debug(f"Транзакция: {date_str}, сумма: {amount}, категория: {transaction_info['category']}")

    logger.info(f"Сформирован список из {len(result)} крупнейших транзакций")
    return result

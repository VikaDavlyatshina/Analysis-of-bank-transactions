from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from config import setup_utils_logger

logger = setup_utils_logger()


def convert_transactions_to_rub(df: pd.DataFrame, currency_rates: Dict[str, float]) -> pd.DataFrame:
    df = df.copy()

    def convert_row(row: pd.Series) -> float:
        currency = str(row["Валюта операции"])
        amount_val = row["Сумма операции"]

        try:
            amount = float(amount_val)
        except (TypeError, ValueError):
            amount = 0.0

        if currency == "RUB":
            return amount

        rate = currency_rates.get(currency)
        if rate is None:
            logger.warning(f"Нет курса для валюты {currency}")
            return amount

        return amount * rate

    df["Сумма операции"] = df.apply(convert_row, axis=1).astype(float)

    return df


def prepare_transactions_for_services(df: pd.DataFrame) -> list[dict]:
    df_copy = df.copy()

    if "Дата операции" in df_copy.columns:
        df_copy["Дата операции"] = df_copy["Дата операции"].apply(
            lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if isinstance(x, (datetime, pd.Timestamp)) else str(x)
        )

    if "Дата платежа" in df_copy.columns:
        df_copy["Дата платежа"] = df_copy["Дата платежа"].apply(
            lambda x: x.strftime("%Y-%m-%d") if isinstance(x, (datetime, pd.Timestamp)) else str(x)
        )

    return df_copy.to_dict(orient="records")

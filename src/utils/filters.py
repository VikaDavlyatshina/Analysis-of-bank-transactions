from datetime import datetime

import pandas as pd

from config import setup_utils_logger

logger = setup_utils_logger()


def filter_transactions_by_date(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    temp_df = df.copy()
    mask = (temp_df["Дата операции"] >= start_date) & (temp_df["Дата операции"] <= end_date)
    filtered_df = temp_df.loc[mask]
    logger.info(f"Отфильтровано по дате: {len(filtered_df)} записей из {len(df)}")
    return filtered_df


def filter_successful_transaction(df: pd.DataFrame) -> pd.DataFrame:
    temp_df = df.copy()
    mask = temp_df["Статус"] == "OK"
    successful_df = temp_df.loc[mask]
    return successful_df

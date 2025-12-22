import pandas as pd

from config import setup_file_readers_logger

# Создаём logger
logger = setup_file_readers_logger()


def load_transactions_from_excel(file_path: str) -> pd.DataFrame:
    """Загружает данные из Excel и выполняет базовое преобразование"""

    # 1. Загружаем данные
    df = pd.read_excel(file_path)
    logger.info(f"Загружено строк: {len(df)}, колонок: {len(df.columns)}")

    # 2. Преобразуем даты
    # Дата операции с временем
    df["Дата операции"] = pd.to_datetime(
        df["Дата операции"], dayfirst=True, errors="coerce"
    )

    failed_dates = df["Дата операции"].isna().sum()
    if failed_dates > 0:
        logger.warning(f"Не удалось распарсить {failed_dates} дат операции")

    # Дата платежа (без времени)
    if "Дата платежа" in df.columns:
        df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], dayfirst=True, errors="coerce")

    # 3. Заполняем пропуски
    df["Кэшбэк"] = df.get("Кэшбэк", 0.0).fillna(0.0)
    df["Номер карты"] = df.get("Номер карты", "****").fillna("****")
    df["Описание"] = df.get("Описание", "Без описания").fillna("Без описания").str.strip()
    df["Категория"] = df.get("Категория", "Не указано").fillna("Не указано").str.strip()
    df["MCC"] = df.get("MCC", "Не указано").fillna("Не указано").str.strip()


    # 4. Преобразуем колонки в category
    for col in ["Категория", "Статус", "Валюта операции", "Валюта платежа", "MCC"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    logger.info(f"Обработка завершена. Колонок: {len(df.columns)}")

    return df

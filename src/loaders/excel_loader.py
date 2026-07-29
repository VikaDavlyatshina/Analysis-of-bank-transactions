import pandas as pd

from config import setup_file_readers_logger

logger = setup_file_readers_logger()


def load_transactions_from_excel(file_path: str) -> pd.DataFrame:
    logger.info("Чтение Excel файла...")
    df = pd.read_excel(file_path)

    logger.info(f"Загружено строк: {len(df)}, колонок: {len(df.columns)}")
    logger.info(f"Колонки в исходном файле: {list(df.columns)}")
    logger.info(f"Типы данных колонок:\n{df.dtypes}")

    logger.info("Обработка колонок с датами...")

    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True, errors="coerce")

    failed_dates = df["Дата операции"].isna().sum()
    if failed_dates > 0:
        logger.warning(f"Не удалось распарсить {failed_dates} дат операции")

    if "Дата платежа" in df.columns:
        df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], dayfirst=True, errors="coerce")
        df["Дата платежа"] = df["Дата платежа"].fillna("Не указано")
    else:
        logger.info("Колонка 'Дата платежа' отсутствует в данных")
        df["Дата платежа"] = "Не указано"

    expected_columns = ["Кэшбэк", "Номер карты", "Описание", "Категория", "MCC"]
    for col in expected_columns:
        if col not in df.columns:
            logger.warning(f"Колонка '{col}' отсутствует, создаем с пустыми значениями")
            df[col] = None

    if "Кэшбэк" in df.columns:
        df["Кэшбэк"] = df["Кэшбэк"].fillna(0.0)

    if "Номер карты" in df.columns:
        df["Номер карты"] = df["Номер карты"].fillna("****")

    if "Описание" in df.columns:
        df["Описание"] = df["Описание"].fillna("Без описания").str.strip()

    if "Категория" in df.columns:
        df["Категория"] = df["Категория"].fillna("Не указано").str.strip()

    if "MCC" in df.columns:
        df["MCC"] = df["MCC"].fillna("Не указано")
        df["MCC"] = df["MCC"].astype(str).str.strip()
        df["MCC"] = df["MCC"].apply(lambda x: x[:-2] if x.endswith(".0") and x.replace(".", "").isdigit() else x)

    for col in ["Категория", "Статус", "Валюта операции", "Валюта платежа", "MCC"]:
        if col in df.columns:
            try:
                df[col] = df[col].astype("category")
                logger.info(f"Преобразовано в category: {col}")
            except Exception as e:
                logger.warning(f"Не удалось преобразовать {col} в category: {e}")

    logger.info(f"Обработка завершена. Колонок: {len(df.columns)}")

    return df

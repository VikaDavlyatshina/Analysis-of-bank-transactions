import pandas as pd

from config import setup_file_readers_logger

# Создаём logger
logger = setup_file_readers_logger()


def load_transactions_from_excel(file_path: str) -> pd.DataFrame:
    """Загружает данные из Excel и выполняет базовое преобразование"""

    # 1. Загружаем данные
    logger.info("Чтение Excel файла...")
    df = pd.read_excel(file_path)

    logger.info(f"Загружено строк: {len(df)}, колонок: {len(df.columns)}")
    logger.info(f"Колонки в исходном файле: {list(df.columns)}")
    logger.info(f"Типы данных колонок:\n{df.dtypes}")

    # 2. Преобразуем даты
    logger.info("Обработка колонок с датами...")

    # Дата операции с временем
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True, errors="coerce")

    failed_dates = df["Дата операции"].isna().sum()
    if failed_dates > 0:
        logger.warning(f"Не удалось распарсить {failed_dates} дат операции")

    # Дата платежа (без времени)
    if "Дата платежа" in df.columns:
        # Преобразуем в datetime
        df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], dayfirst=True, errors="coerce")

        # Заменяем все NaT на "Не указано"
        df["Дата платежа"] = df["Дата платежа"].fillna("Не указано")
    else:
        logger.info("Колонка 'Дата платежа' отсутствует в данных")
        df["Дата платежа"] = "Не указано"

    # 3. Заполняем пропуски

    # Проверяем и создаем недостающие колонки
    expected_columns = ["Кэшбэк", "Номер карты", "Описание", "Категория", "MCC"]
    for col in expected_columns:
        if col not in df.columns:
            logger.warning(f"Колонка '{col}' отсутствует, создаем с пустыми значениями")
            df[col] = None

    # Заполняем пропуски
    if "Кэшбэк" in df.columns:
        df["Кэшбэк"] = df["Кэшбэк"].fillna(0.0)

    if "Номер карты" in df.columns:
        df["Номер карты"] = df["Номер карты"].fillna("****")

    if "Описание" in df.columns:
        df["Описание"] = df["Описание"].fillna("Без описания").str.strip()

    if "Категория" in df.columns:
        df["Категория"] = df["Категория"].fillna("Не указано").str.strip()

    # Обработка MCC
    if "MCC" in df.columns:
        # Заполняем пропуски
        df["MCC"] = df["MCC"].fillna("Не указано")
        # Преобразуем в строку, чистим и убираем .0
        df["MCC"] = df["MCC"].astype(str).str.strip()
        # Простая замена: если оканчивается на ".0" и состоит из цифр и точки
        df["MCC"] = df["MCC"].apply(lambda x: x[:-2] if x.endswith(".0") and x.replace(".", "").isdigit() else x)
    # 4. Преобразуем колонки в category
    for col in ["Категория", "Статус", "Валюта операции", "Валюта платежа", "MCC"]:
        if col in df.columns:
            try:
                df[col] = df[col].astype("category")
                logger.info(f"Преобразовано в category: {col}")
            except Exception as e:
                logger.warning(f"Не удалось преобразовать {col} в category: {e}")

    logger.info(f"Обработка завершена. Колонок: {len(df.columns)}")

    return df

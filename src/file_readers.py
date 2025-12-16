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
    # Дата операции(со временем)
    df["Дата операции"] = pd.to_datetime(
        df["Дата операции"], format="%d.%m.%Y %H:%M:%S", dayfirst=True, errors="coerce"
    )
    # Проверяем сколько дат не распарсилось
    failed_dates = df["Дата операции"].isna().sum()
    if failed_dates > 0:
        logger.warning(f"Не удалось распарсить {failed_dates} дат операции")

    # Дата платежа
    if "Дата платежа" in df.columns:
        df["Дата платежа"] = pd.to_datetime(df["Дата платежа"], format="%d.%m.%Y", dayfirst=True, errors="coerce")

    # 3. Обрабатываем пустые значения

    if "Кэшбэк" in df.columns:
        df["Кэшбэк"] = df["Кэшбэк"].fillna(0.0)
    else:
        df["Кэшбэк"] = 0.0
        logger.info("Колонка 'Кэшбэк' отсутствует, установлено 0.0")

    df["Номер карты"] = df["Номер карты"].fillna("****")

    # Убираем лишние пробелы у текстовых полей
    if "Описание" in df.columns:
        df["Описание"] = df["Описание"].fillna("Без описания")
        df["Описание"] = df["Описание"].str.strip()

    if "Категория" in df.columns:
        df["Категория"] = df["Категория"].fillna("Не указано")
        df["Категория"] = df["Категория"].str.strip()

    # 4. Преобразуем в Category
    columns_to_category = ["Категория", "Статус", "Валюта операции", "Валюта платежа", "MCC"]
    for col in columns_to_category:
        if col in df.columns:
            # Проверяем, что столбец не пустой
            if not df[col].empty:
                # Преобразуем в category
                df[col] = df[col].astype("category")
                logger.info(f" {col} -> category ({df[col].nunique()} уникальных значений)")
            else:
                logger.warning(f"  Столбец {col} пустой, пропускаем")

    logger.info(f"Обработка завершена. Колонок: {len(df.columns)}")

    return df

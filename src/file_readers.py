from datetime import datetime
import pandas as pd

from config import setup_file_readers_logger

# Создаём logger
logger = setup_file_readers_logger()


def load_transactions_from_excel(file_path):
    """Загружает данные из Excel и выполняет базовое преобразование"""

    # 1. Загружаем данные
    df = pd.read_excel(file_path)
    logger.info(f"Загружено строк: {len(df)}, колонок: {len(df.columns)}")
    logger.info(f"Колонки в файле: {list(df.columns)}")

    # 2. Создаём копию для безопасной работы
    df_processed = df.copy()

    # 3. Преобразуем даты
    # Дата операции(со временем)
    df_processed['Дата операции'] = pd.to_datetime(
        df_processed['Дата операции'],
        format='%d.%m.%Y %H:%M:%S',
        dayfirst=True,
        errors='coerce'
    )

    # Проверяем сколько дат не распарсилось
    failed_dates = df_processed['Дата операции'].isna().sum()
    if failed_dates > 0:
        logger.warning(f"Не удалось распарсить {failed_dates} дат операции")

    # Дата платежа
    if 'Дата платежа' in df_processed.columns:
        df_processed['Дата платежа'] = pd.to_datetime(
            df_processed['Дата платежа'],
            format='%d.%m.%Y',
            dayfirst=True,
            errors='coerce'
        )

    # 4. Обрабатываем пустые значения

    df_processed['Кэшбэк'] = df_processed['Кэшбэк'].fillna(0.0)  # Кэшбэк = 0 если пусто
    df_processed['Номер карты'] = df_processed['Номер карты'].fillna('')  # Номер карты = пустая строка если пусто

    # Убираем лишние пробелы у текстовых полей
    if 'Описание' in df_processed.columns:
        df_processed['Описание'] = df_processed['Описание'].fillna('Без описания')
        df_processed['Описание'] = df_processed['Описание'].str.strip()

    if 'Категория' in df_processed.columns:
        df_processed['Категория'] = df_processed['Категория'].fillna('Не указано')
        df_processed['Категория'] = df_processed['Категория'].str.strip()


    # 5. Последние 4 цифры карты
    df_processed['Последние цифры карты'] = df_processed['Номер карты'].apply(
        lambda x: x[-4:] if isinstance(x, str) and x.startswith('*') else '0000'
    )


    # 6. Используем абсолютную сумму для сортировки Топ-транзакций
    # abs() делает отрицательные положительными: -100 → 100, 100 → 100
    df_processed['Абсолютная сумма'] = df_processed['Сумма операции'].abs()

    # 7. Расход по карте
    # Если сумма отрицательная → берём модуль, если положительная → 0
    df_processed['Расход по карте'] = df_processed['Сумма операции'].apply(
        lambda x: abs(x) if x < 0 else 0
    )

    # 8. Тип операции (опционально, но полезно)
    df_processed['Тип операции'] = df_processed['Сумма операции'].apply(
        lambda x: 'Расход' if x < 0 else 'Доход'
    )

    # 9. Месяц для группировки
    df_processed['Месяц'] = df_processed['Дата операции'].dt.strftime('%Y-%m')


    # Логируем итоги
    logger.info(f"Обработка завершена. Колонок: {len(df_processed.columns)}")
    logger.info(f"Добавлены колонки: 'Абсолютная сумма', 'Расход по карте', 'Тип операции', 'Месяц'")

    return df_processed


def filter_transactions_by_date_range(
    df:pd.DataFrame, start_date: datetime, end_date: datetime
) -> pd.DataFrame:
    """Фильтрует транзакции по диапазону дат"""

    mask = (df['Дата операции'] >= start_date) & (df['Дата операции'] <= end_date)
    filtered_df = df.loc[mask].copy()

    logger.info(f"Отфильтровано по дате: {len(filtered_df)}")
    return filtered_df


def filter_successful_transactions(df:pd.DataFrame) -> pd.DataFrame:
    """ Фильтрует успешные транзакции со статусом OK"""

    # Создаем булеву маску
    mask = df['Статус'].str.upper().str.strip() == "OK"
    successful_df = df.loc[mask].copy()
    logger.info(f"Успешных транзакций: {len(successful_df)}")
    return successful_df

from src.file_readers import load_transactions_from_excel
import pandas as pd
from unittest.mock import patch, Mock


def test_load_transactions_basic(sample_transactions_df):
    """
    Проверяем, что функция работает с нормальным DataFrame,
    преобразования выполняются, NaN заменены
    """
    with (patch("src.file_readers.pd.read_excel", return_value=sample_transactions_df), \
          patch("src.file_readers.logger") as mock_logger):

          df = load_transactions_from_excel("fake.xlsx")

    # Проверка результатов
    # 1. Пропуски заполнены
    assert df["Кэшбэк"].isna().sum() == 0
    assert df["Номер карты"].isna().sum() == 0
    assert df["Описание"].isna().sum() == 0
    assert df["Категория"].isna().sum() == 0

    # 2. Проверяем strip()
    assert all(df["Описание"] == df["Описание"].str.strip())
    assert all(df["Категория"] == df["Категория"].str.strip())

    # 3. Проверяем dtype категорий
    for col in ["Категория", "Статус", "Валюта операции", "Валюта платежа", "MCC"]:
        if col in df.columns:
            assert str(df[col].dtype) == "category"

        # 4. Проверяем, что logger был вызван
    mock_logger.info.assert_any_call(
        f"Загружено строк: {len(sample_transactions_df)}, колонок: {len(sample_transactions_df.columns)}")
    mock_logger.info.assert_any_call(f"Обработка завершена. Колонок: {len(df.columns)}")


def test_load_transactions_logs_warning_for_bad_dates():
    raw_df = pd.DataFrame({
        "Дата операции": ["bad_date", "01.01.2024 10:10"],
        "MCC": [1234, 5678],
    })

    with (patch("src.file_readers.pd.read_excel", return_value=raw_df), \
     patch("src.file_readers.logger") as mock_logger):

     load_transactions_from_excel("fake.xlsx")

     # Проверяем, что логгер был warning
     mock_logger.warning.assert_called_once()
     assert "Не удалось распарсить" in mock_logger.warning.call_args[0][0]

def test_fill_missing_values_and_strip():
    raw_df = pd.DataFrame({
        "Дата операции": ["01.01.2024 10:10", "02.01.2024 12:00"],
        "Кэшбэк": [None, 5.0],
        "Номер карты": [None, "1234"],
        "Описание": [" Покупка ", None],
        "Категория": [" Еда ", None],
        "MCC": [5411, None],
    })

    with patch("src.file_readers.pd.read_excel", return_value=raw_df):
        df = load_transactions_from_excel("fake.xlsx")

    # Проверка заполнения
    assert df["Кэшбэк"].iloc[0] == 0.0
    assert df["Номер карты"].iloc[0] == "****"
    assert df["Описание"].iloc[1] == "Без описания"
    assert df["Категория"].iloc[1] == "Не указано"
    assert df["MCC"].iloc[1] == "Не указано"

    # Проверка strip
    assert df["Описание"].iloc[0] == "Покупка"
    assert df["Категория"].iloc[0] == "Еда"
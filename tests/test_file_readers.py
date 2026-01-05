from unittest.mock import patch, MagicMock
from typing import Dict, Any, List
from pathlib import Path

import pandas as pd
import pytest

from src.file_readers import load_transactions_from_excel


# 1. Тест успешного чтения и преобразования дат
def test_load_transactions_date(temp_excel_file: Any) -> None:
    """Тестирует корректное чтение и преобразование дат из Excel файла."""
    with patch("src.file_readers.logger") as mock_logger:
        # Подготавливаем данные
        raw_data: Dict[str, List[Any]] = {
            "Дата операции": ["01.01.2026 12:00:00", "invalid_date"],
            "Дата платежа": ["02.01.2026", None],
            "Валюта операции": ["RUB", "USD"],
        }

        path: Path = temp_excel_file(raw_data)   # Создаём временный файл
        df: pd.DataFrame = load_transactions_from_excel(str(path))

        # Проверяем распознавание корректной даты (Дата имеет тип datetime)
        assert pd.api.types.is_datetime64_any_dtype(df["Дата операции"])
        assert df["Дата операции"].iloc[0].year == 2026
        # Проверяем, что некорректная дата стала NaT
        assert pd.isna(df["Дата операции"].iloc[1])

        assert mock_logger.info.called
        assert mock_logger.warning.called


# 2. Тест заполнения пропусков
def test_fill_missing_values_and_strip(temp_excel_file: Any) -> None:
    """Тестирует заполнение пропущенных значений и удаление пробелов."""
    with patch("src.file_readers.logger") as mock_logger:
        # Подготавливаем данные
        raw_data: pd.DataFrame = pd.DataFrame(
            {
                "Дата операции": ["01.01.2024 10:10", "02.01.2024 12:00"],
                "Кэшбэк": [None, 5.0],
                "Номер карты": [None, "1234"],
                "Описание": [" Покупка ", None],
                "Категория": [" Еда ", None],
                "MCC": [5411, None],
            }
        )

        path: Path = temp_excel_file(raw_data)   # Создаём временный файл
        df: pd.DataFrame = load_transactions_from_excel(str(path))

        # Проверка заполнения
        assert df["Кэшбэк"].iloc[0] == 0.0
        assert df["Номер карты"].iloc[0] == "****"
        assert df["Описание"].iloc[1] == "Без описания"
        assert df["Категория"].iloc[1] == "Не указано"
        assert df["MCC"].iloc[1] == "Не указано"
        assert df["MCC"].iloc[0] == "5411"

        # Проверка strip
        assert df["Описание"].iloc[0] == "Покупка"
        assert df["Категория"].iloc[0] == "Еда"

        mock_logger.info.assert_any_call("Обработка колонок с датами...")
        info_calls: List[MagicMock] = mock_logger.info.call_args_list
        assert any("Обработка завершена" in str(call[0][0]) for call in info_calls)


# 3. Тест создания отсутствующих колонок
def test_missing_columns_creation(temp_excel_file: Any) -> None:
    """Тестирует создание отсутствующих обязательных колонок."""
    with patch("src.file_readers.logger") as mock_logger:
        # Создаем файл без нужных колонок
        raw_data: Dict[str, List[str]] = {"Дата операции": ["01.01.2025"]}

        path: Path = temp_excel_file(raw_data)  # Создаём временный файл

        df: pd.DataFrame = load_transactions_from_excel(str(path))

        expected_cols: List[str] = ["Кэшбэк", "Номер карты", "Описание", "Категория", "MCC"]
        for col in expected_cols:
            assert col in df.columns
            if col == "Кэшбэк":
                assert df[col].iloc[0] == 0.0

        assert mock_logger.info.called
        assert mock_logger.warning.called


# 4. Тест типов данных (category)
def test_column_types(temp_excel_file: Any) -> None:
    """Тестирует правильность типов данных в колонках."""
    with patch("src.file_readers.logger") as mock_logger:
        raw_data: Dict[str, List[str]] = {
            "Дата операции": ["01.01.2025"],
            "Статус": ["OK"],
            "Валюта операции": ["RUB"]
        }
        path: Path = temp_excel_file(raw_data)

        df: pd.DataFrame = load_transactions_from_excel(str(path))

        assert isinstance(df["Статус"].dtype, pd.CategoricalDtype)
        assert isinstance(df["Валюта операции"].dtype, pd.CategoricalDtype)

        warning_calls: List[str] = [call[0][0] for call in mock_logger.warning.call_args_list]
        missing_cols: List[str] = ["Кэшбэк", "Номер карты", "Описание", "Категория", "MCC"]
        for col in missing_cols:
            col_warnings = [msg for msg in warning_calls if col in str(msg) and "отсутствует" in str(msg)]
            assert len(col_warnings) >= 1, f"Не найдено warning для отсутствующей колонки {col}"
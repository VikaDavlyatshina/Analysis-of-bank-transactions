import json
from datetime import datetime
from functools import wraps
from typing import Optional, Callable

import pandas as pd
from dateutil.relativedelta import relativedelta

from config import REPORTS_DIR, setup_reports_logger

# Создаём logger
logger = setup_reports_logger()


def report_to_file(func: Optional[Callable] = None, *, filename: Optional[str] = None):
    """
    Декоратор для сохранения результата отчёта в JSON-файл.
    Может использоваться:
    @report_to_file
    @report_to_file("my_report.json")
        """

    def decorator(inner_func: Callable):
        @wraps(inner_func)    # Сохраняем имя и описание оригинальной функции
        def wrapper(*args, **kwargs):
            """
            Обертка, которая выполняет функцию и сохраняет результат
            """
            try:
                # 1. Вызываем оригинальную функцию
                result = inner_func(*args, **kwargs)

                # 2. Создаем имя файла
                if filename is None:
                    # Автоматическое имя: функция_дата_время.json
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_name = f"report_{inner_func.__name__}_{timestamp}.json"
                else:
                    # Используем указанное имя
                    file_name = filename

                # 3. Добавляем папку reports
                file_path = REPORTS_DIR / file_name


                # 4. Сохраняем результат
                try:
                    if isinstance(result, pd.DataFrame):
                        data = result.to_dict(orient="records")

                    else:
                        data = result

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    logger.info(f"Отчет сохранен: {file_path}")

                except Exception as e:
                    logger.error(f"Ошибка сохранения отчёта: {e}")
                    raise

                return result

            except Exception as e:
                logger.error(f"Ошибка в декораторе report_to_file: {e}")
                raise

        return wrapper

    # Поддержка декоратора без параметров
    if func is not None:
        return decorator(func)

    return decorator


@report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Функция для анализа трат по указанной категории за последние 3 месяца.
    Возвращает DataFrame с новым форматом для отчета.
    """
    try:
        logger.info(f"Запуск анализа для категории: {category}")

        # Проверка, если передан не DataFrame
        if transactions is None or not isinstance(transactions, pd.DataFrame):
            logger.error("Передан некорректный DataFrame")
            raise ValueError("Передан некорректный DataFrame")

        # Проверка обязательных колонок
        required_columns = ["Дата операции", "Категория", "Сумма операции"]
        for col in required_columns:
            if col not in transactions.columns:
                logger.error(f"В DataFrame отсутствует колонка '{col}'")
                raise KeyError(f"В DataFrame отсутствует колонка '{col}'")

        # 1. -- Определяем период с использованием relativedelta --
        if date is None:
            end_date = datetime.now()  # если дата не указана - берем сегодня
        else:
            try:
                end_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                logger.error(f"Дата должна быть в формате 'YYYY-MM-DD', получено: {date}")
                raise ValueError(f"Дата должна быть в формате 'YYYY-MM-DD', получено: {date}")

        start_date = end_date - relativedelta(months=3)  # последние 3 месяца
        # Начало дня для start_date, конец дня для end_date
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        logger.info(f"Период анализа: {start_date.date()} - {end_date.date()}")

        # 2. -- Фильтруем данные --
        # По дате
        mask_date = (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= end_date)

        # По категории
        mask_category = transactions["Категория"] == category

        # Только расходы
        mask_expense = transactions["Сумма операции"] < 0

        # Итоговый фильтр
        filtered = transactions[mask_date & mask_category & mask_expense].copy()
        logger.info(f"Количество операций после фильтрации: {len(filtered)}")

        # 3. -- Проверяем пустой результат --
        if filtered.empty:
            logger.warning(f"Нет трат по категории '{category}' за период")
            return pd.DataFrame(
                [ {
                    "Месяц": "Нет данных за период",
                    "Категория": category,
                    "Сумма трат": 0,
                    "Количество операций": 0,
                    "Средний чек": 0,
                    }]
            )

        # -- 4. Добавляем колонку Месяц для группировки --
        filtered["Месяц"] = filtered["Дата операции"].dt.strftime("%Y-%m")
        months = filtered["Месяц"].unique()
        logger.info(f"Месяцы для анализа: {', '.join(months)}")

        # -- 5. Рассчитываем сумму расходов по модулю --
        filtered["Расход"] = filtered["Сумма операции"].abs()

        # -- 6. Группировка по месяцу --
        grouped = filtered.groupby("Месяц", as_index=False).agg(
            {"Расход": ["sum", "count"]}
        )
        grouped.columns = ["Месяц", "Сумма трат", "Количество операций"]

        # -- 7. Добавляем средний чек --
        grouped["Средний чек"] = (grouped["Сумма трат"] / grouped["Количество операций"]).round(2)
        grouped["Сумма трат"] = grouped["Сумма трат"].round(2)
        grouped["Категория"] = category
        logger.info(f"Группировка по месяцам завершена. Итоговые суммы по месяцам:\n{grouped[['Месяц', 'Сумма трат']]}")

        # ---8. Сортируем по Месяц --
        grouped = grouped.sort_values("Месяц")

        # -- 9. Итог за 3 месяца --
        total_spent = grouped["Сумма трат"].sum()
        total_count = grouped["Количество операций"].sum()
        total_avg = (total_spent / total_count).round(2) if total_count > 0 else 0

        total_row = pd.DataFrame([{
            "Месяц": "Общий итог за 3 месяца",
            "Категория": category,
            "Сумма трат": total_spent,
            "Количество операций": total_count,
            "Средний чек": total_avg
        }])

        result = pd.concat([grouped, total_row], ignore_index=True)
        return result

    except Exception as e:
        logger.error(f"Ошибка анализа категории '{category}': {e}")
        return pd.DataFrame([{
            "Месяц": f"Ошибка: {str(e)[:50]}...",
            "Категория": category,
            "Сумма трат": 0,
            "Количество операций": 0,
            "Средний чек": 0,
        }])
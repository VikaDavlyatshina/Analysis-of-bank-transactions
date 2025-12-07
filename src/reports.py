from datetime import datetime
from functools import wraps
from typing import Optional
import json
import pandas as pd
from dateutil.relativedelta import relativedelta
from config import REPORTS_DIR

from config import setup_reports_logger

# Создаём logger
logger = setup_reports_logger()

def report_to_file(filename: Optional[str] = None):
    """ Декоратор для автоматического сохранения отчетов в файл """

    def decorator(func):  # Сохраняем имя и описание оригинальной функции
        """Внутренняя функция декоратор"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Обертка, которая выполняет функцию и сохраняет результат
            """
            try:
               # 1. Вызываем оригинальную функцию
               result = func(*args, **kwargs)

               # 2. Создаем имя файла
               if filename is None:
                   # Автоматическое имя: функция_дата_время.json
                   timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                   file_name = f"report_{func.__name__}_{timestamp}.json"
               else:
                   # Используем указанное имя
                   file_name = filename

               # 3. Добавляем папку reports
               file_path = REPORTS_DIR / file_name

               # 4. Создаём папку, если её нет
               REPORTS_DIR.mkdir(parents=True, exist_ok=True)

               # 5. Сохраняем результат
               with open(file_path, 'w', encoding='utf-8') as f:
                   if isinstance(result, pd.DataFrame):
                       if result.empty:
                           data_to_save = {"status": "empty", "message": "Нет данных"}
                       else:
                           data_to_save = {
                               "report_name": func.__name__,
                               "generated_at": datetime.now().isoformat(),
                               "period": "За последние 3 месяца",
                               "data": result.to_dict(orient='records')
                           }
                   elif isinstance(result, (dict, list)):
                       data_to_save = result
                   else:
                       data_to_save = {"result": str(result)}

                   json.dump(data_to_save, f, indent=2, ensure_ascii=False)

               logger.info(f"Отчет сохранен: {file_path}")

               return result

            except Exception as e:
               logger.error(f"Ошибка в декораторе report_to_file: {e}")
               raise

        return wrapper

    return decorator


@report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Функция для анализа трат по указанной категории за последние 3 месяца.
    Возвращает DataFrame с новым форматом для отчета.
    """
    try:
        logger.info(f"Запуск анализа для категории: {category}")

        if transactions.empty:
            logger.warning("Получен пустой DataFrame")
            return pd.DataFrame(columns=[
                'Месяц', 'Категория', 'Сумма трат', 'Количество операций', 'Средний чек'
            ])

        # Определяем период с использованием relativedelta
        if date is None:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(date, "%Y-%m-%d")

        start_date = end_date - relativedelta(months=3)

        # Начало дня для start_date, конец дня для end_date
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        logger.info(f"Период анализа: {start_date.date()} - {end_date.date()}")

        # ФИЛЬТРАЦИЯ данных
        # 1. По дате
        date_filter = (transactions['Дата операции'] >= start_date) & \
                      (transactions['Дата операции'] <= end_date)

        # 2. По категории
        category_filter = (transactions['Категория'] == category)

        # 3. Только расходы
        if 'Тип операции' in transactions.columns:
            expense_filter = (transactions['Тип операции'] == 'Расход')
        else:
            expense_filter = (transactions['Сумма операции'] < 0)

        # Объединяем фильтры
        mask = date_filter & category_filter & expense_filter
        filtered = transactions[mask].copy()

        # Проверяем результат
        if filtered.empty:
            logger.info(f"Нет трат по категории '{category}' за период")
            # Возвращаем DataFrame с информацией
            message_df = pd.DataFrame([{
                'Месяц': f'Нет данных за период',
                'Категория': category,
                'Сумма трат': 0,
                'Количество операций': 0,
                'Средний чек': 0
            }])
            return message_df

        logger.info(f"Найдено операций: {len(filtered)}")

        # Группировка по месяцам
        if 'Месяц' not in filtered.columns:
            filtered['Месяц'] = filtered['Дата операции'].dt.strftime('%Y-%m')

        # Используем 'Расход по карте' которая содержит положительные значения расходов
        if 'Расход по карте' in filtered.columns:
            amount_column = 'Расход по карте'
        else:
            # Если нет - используем модуль отрицательных сумм
            filtered['Расход'] = filtered['Сумма операции'].abs()
            amount_column = 'Расход'

        # Группируем и считаем статистику
        grouped = filtered.groupby('Месяц', as_index=False).agg({
            amount_column: ['sum', 'count']
        })

        # Упрощаем названия колонок
        grouped.columns = ['Месяц', 'Сумма трат', 'Количество операций']

        # Добавляем средний чек
        grouped['Средний чек'] = (grouped['Сумма трат'] / grouped['Количество операций']).round(2)
        grouped['Сумма трат'] = grouped['Сумма трат'].round(2)

        grouped['Категория'] = category

        # Сортируем по месяцам
        result_df = grouped.sort_values('Месяц')

        if not result_df.empty:
            # Вычисляем общие итоги
            total_spent = result_df['Сумма трат'].sum()
            total_count = result_df['Количество операций'].sum()
            total_avg = (total_spent / total_count).round(2) if total_count > 0 else 0

            # Создаем строку с итогами
            total_row = pd.DataFrame([{
                'Месяц': 'Общий итог за 3 месяца:',
                'Категория': category,
                'Сумма трат': total_spent,
                'Количество операций': int(total_count),
                'Средний чек': total_avg
            }])

            # Объединяем с основными данными
            result_df = pd.concat([result_df, total_row], ignore_index=True)

        logger.info(f"Анализ завершен. Результат: {len(result_df)} строк")
        return result_df

    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        # Возвращаем DataFrame с ошибкой
        error_df = pd.DataFrame([{
            'Месяц': f'Ошибка: {str(e)[:50]}...',
            'Категория': category,
            'Сумма трат': 0,
            'Количество операций': 0,
            'Средний чек': 0
        }])
        return error_df


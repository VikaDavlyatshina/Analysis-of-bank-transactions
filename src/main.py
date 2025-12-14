import json
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any

from src.file_readers import load_transactions_from_excel
from src.reports import spending_by_category
from src.services import investment_bank, simple_search, find_phone_numbers
from src.views import generate_financial_report
from src.utils import get_greeting, load_user_settings
from config import EXCEL_FILE, USER_SETTINGS


def parse_datetime_input(datetime_str: str) -> str:
    """Парсит ввод пользователя в формат YYYY-MM-DD HH:MM:SS"""
    if not datetime_str.strip():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Пробуем разные форматы
    formats = [
        "%Y-%m-%d %H:%M:%S",  # Полная дата-время
        "%Y-%m-%d %H:%M",  # Дата-время без секунд
        "%Y-%m-%d",  # Только дата
        "%Y-%m",  # Только месяц
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(datetime_str, fmt)
            # Добавляем недостающие части
            if fmt == "%Y-%m-%d":
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            elif fmt == "%Y-%m":
                return dt.strftime("%Y-%m-01 %H:%M:%S")
            elif fmt == "%Y-%m-%d %H:%M":
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            return datetime_str  # Уже в правильном формате
        except ValueError:
            continue

    # Если ни один формат не подошел, используем текущее время
    print(f"Не удалось распознать формат даты '{datetime_str}'. Использую текущее время.")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    """Отвечает за основную логику проекта и связывает функциональности между собой"""

    print("Привет, добро пожаловать в программу 'Приложение для анализа банковских операций'")
    print("Выберите необходимый пункт в меню:")
    print("1. Веб-страницы")
    print("2. Сервисы")
    print("3. Отчеты")

    while True:
        try:
            user_choice = int(input("Введите нужную цифру: "))
            if user_choice in [1, 2, 3]:
                break
            else:
                print("Пожалуйста введите 1, 2 или 3")
        except ValueError:
            print("Это должно быть число! Попробуйте снова.")

    # 1. Загружаем данные
    try:
        print(f"\nЗагружаем данные из: {EXCEL_FILE}")
        transactions_df = load_transactions_from_excel(str(EXCEL_FILE))
        print(f"Успешно загружено {len(transactions_df)} транзакций")

        # Показываем базовую информацию о данных
        if len(transactions_df) > 0:
            print(
                f"Период данных: {transactions_df['Дата операции'].min().date()} - {transactions_df['Дата операции'].max().date()}")
    except Exception as e:
        print(f"Не удалось загрузить данные из файла: {e}")
        print("Убедитесь, что файл находится в правильной папке и имеет правильный формат.")
        return

    # 2. Загружаем настройки
    user_settings = {}
    try:
        user_settings = load_user_settings(str(USER_SETTINGS))
        print(f"Настройки пользователя загружены")
        if user_settings:
            if 'user_currencies' in user_settings:
                print(f"   Валюты: {', '.join(user_settings['user_currencies'])}")
            if 'user_stocks' in user_settings:
                print(f"   Акции: {', '.join(user_settings['user_stocks'])}")
    except Exception as e:
        print(f"Не удалось загрузить настройки: {e}")
        print("Продолжаем работу с настройками по умолчанию.")

    # Главное меню
    while True:
        print("\n" + "=" * 50)
        print("ГЛАВНОЕ МЕНЮ")
        print("=" * 50)
        print("1. Веб-страницы")
        print("2. Сервисы")
        print("3. Отчеты")
        print("4. Статистика данных")
        print("5. Выход")

        try:
            choice = int(input("\nВведите номер пункта (1-5): "))
        except ValueError:
            print("Это должно быть число! Попробуйте снова.")
            continue

        if choice == 1:
            # Веб-страницы
            print("\n" + "-" * 30)
            print("ВЕБ-СТРАНИЦЫ")
            print("-" * 30)
            print("1. Главная страница (полный отчет)")
            print("2. Назад")

            try:
                sub_choice = int(input("Введите номер пункта: "))
            except ValueError:
                print("Это должно быть число!")
                continue

            if sub_choice == 2:
                continue

            # Главная страница
            print("\n" + "=" * 50)
            print("ГЛАВНАЯ СТРАНИЦА - ГЕНЕРАЦИЯ ОТЧЕТА")
            print("=" * 50)
            print("Форматы даты, которые можно использовать:")
            print("  - YYYY-MM-DD HH:MM:SS (полная дата и время)")
            print("  - YYYY-MM-DD (только дата)")
            print("  - YYYY-MM (только месяц)")
            print("  - Оставьте пустым для текущего момента\n")

            datetime_str = input("Введите дату (или оставьте пустым): ").strip()

            # Парсим дату
            parsed_datetime = parse_datetime_input(datetime_str)

            print(f"\nГенерирую отчет для {parsed_datetime}...")

            try:
                report = generate_financial_report(parsed_datetime)
                print(f"\nОтчет сгенерирован успешно!")
                print(f"Дата анализа: {parsed_datetime}")
                print(f"Основные показатели:")
                print(f"   Приветствие: {report.get('greeting', 'Не указано')}")
                print(f"   Карт: {len(report.get('cards', []))}")
                print(f"   Топ операций: {len(report.get('top_transactions', []))}")
                print(f"   Валюты: {len(report.get('currency_rates', []))}")
                print(f"   Акции: {len(report.get('stock_prices', []))}")

                show_details = input("\nПоказать полный отчет? (да/нет): ").strip().lower()
                if show_details in ["да", "д", "yes", "y", "1"]:
                    print("\n" + "=" * 50)
                    print("ПОЛНЫЙ ОТЧЕТ")
                    print("=" * 50)
                    print(json.dumps(report, ensure_ascii=False, indent=2))

                    # Предлагаем сохранить отчет
                    save_report = input("\nСохранить отчет в файл? (да/нет): ").strip().lower()
                    if save_report in ["да", "д", "yes", "y", "1"]:
                        filename = f"report_{parsed_datetime.replace(':', '-').replace(' ', '_')}.json"
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(report, f, ensure_ascii=False, indent=2)
                        print(f"Отчет сохранен в файл: {filename}")
            except Exception as e:
                print(f"Ошибка при генерации отчета: {e}")

        elif choice == 2:
            # Сервисы
            print("\n" + "-" * 30)
            print("СЕРВИСЫ")
            print("-" * 30)
            print("1. Инвесткопилка")
            print("2. Простой поиск")
            print("3. Поиск по телефонным номерам")
            print("4. Назад")

            try:
                sub_choice = int(input("Введите номер пункта: "))
            except ValueError:
                print("Это должно быть число!")
                continue

            if sub_choice == 4:
                continue

            # Преобразуем DataFrame в список словарей
            try:
                transactions_list = transactions_df.to_dict('records')
            except Exception as e:
                print(f"Ошибка преобразования данных: {e}")
                continue

            if sub_choice == 1:
                # Инвесткопилка
                print("\n" + "=" * 50)
                print("ИНВЕСТКОПИЛКА")
                print("=" * 50)
                print("Автоматическое округление трат и накопление мелочи\n")

                month_str = input("Введите месяц (YYYY-MM или оставьте пустым для текущего): ").strip()

                if not month_str:
                    month_str = datetime.now().strftime("%Y-%m")
                else:
                    # Проверяем формат месяца
                    try:
                        datetime.strptime(month_str + "-01", "%Y-%m-%d")
                    except ValueError:
                        print(f"Неверный формат месяца. Использую текущий месяц.")
                        month_str = datetime.now().strftime("%Y-%m")

                while True:
                    try:
                        limit = int(input("Введите шаг округления (10, 50 или 100 рублей): "))
                        if limit in [10, 50, 100]:
                            break
                        else:
                            print("Шаг должен быть 10, 50 или 100")
                    except ValueError:
                        print("Введите число!")

                print(f"\nРассчитываю сумму для копилки за {month_str}...")

                try:
                    result = investment_bank(month_str, transactions_list, limit)
                    print(f"\nРезультат расчета:")
                    print(f"Месяц: {month_str}")
                    print(f"Шаг округления: {limit} руб")
                    print(f"Сумма для копилки: {result:.2f} руб")

                    if result > 0:
                        print(f"Совет: Эту сумму можно отложить на инвестиции!")
                    else:
                        print("В этом месяце не было трат для округления.")
                except Exception as e:
                    print(f"Ошибка расчета: {e}")

            elif sub_choice == 2:
                # Простой поиск
                print("\n" + "=" * 50)
                print("ПРОСТОЙ ПОИСК ПО ТРАНЗАКЦИЯМ")
                print("=" * 50)
                print("Ищет по всем текстовым полям транзакций\n")

                search_string = input("Введите текст для поиска: ").strip()

                if not search_string:
                    print("Строка поиска не может быть пустой")
                    continue

                print(f"\nИщу транзакции по запросу: '{search_string}'...")

                try:
                    results = simple_search(transactions_list, search_string)
                    print(f"\nНайдено транзакций: {len(results)}")

                    if results:
                        print("\nПервые 5 найденных транзакций:")
                        for i, item in enumerate(results[:5], 1):
                            print(f"\n  {i}. {item.get('Дата операции', 'Нет даты')}")
                            print(f"     Описание: {item.get('Описание', 'Нет описания')}")
                            print(f"     Сумма: {item.get('Сумма операции', '0')} руб")
                            print(f"     Категория: {item.get('Категория', 'Не указана')}")

                        if len(results) > 5:
                            print(f"\n  ... и еще {len(results) - 5} транзакций")

                        show_all = input("\nПоказать все результаты? (да/нет): ").strip().lower()
                        if show_all in ["да", "д", "yes", "y", "1"]:
                            for i, item in enumerate(results, 1):
                                print(f"\n  {i}. {item.get('Дата операции', 'Нет даты')}")
                                print(f"     Описание: {item.get('Описание', 'Нет описания')}")
                                print(f"     Сумма: {item.get('Сумма операции', '0')} руб")
                                print(f"     Категория: {item.get('Категория', 'Не указана')}")
                    else:
                        print("По вашему запросу ничего не найдено")
                except Exception as e:
                    print(f"Ошибка поиска: {e}")

            elif sub_choice == 3:
                # Поиск по телефонным номерам
                print("\n" + "=" * 50)
                print("ПОИСК ТРАНЗАКЦИЙ С ТЕЛЕФОННЫМИ НОМЕРАМИ")
                print("=" * 50)

                print("\nИщу транзакции с телефонными номерами...")

                try:
                    results = find_phone_numbers(transactions_list)
                    print(f"\nНайдено транзакций с номерами: {len(results)}")

                    if results:
                        print("\nТранзакции с телефонными номерами:")
                        for i, item in enumerate(results[:10], 1):
                            print(f"\n  {i}. {item.get('Дата операции', 'Нет даты')}")
                            print(f"     Описание: {item.get('Описание', 'Нет описания')}")
                            print(f"     Найденные номера: {item.get('phone_numbers', [])}")
                            print(f"     Сумма: {item.get('Сумма операции', '0')} руб")

                        if len(results) > 10:
                            print(f"\n  ... и еще {len(results) - 10} транзакций")
                    else:
                        print("Телефонные номера не найдены в транзакциях")
                except Exception as e:
                    print(f"Ошибка поиска номеров: {e}")

        elif choice == 3:
            # Отчеты
            print("\n" + "-" * 30)
            print("ОТЧЕТЫ")
            print("-" * 30)
            print("1. Траты по категории")
            print("2. Назад")

            try:
                sub_choice = int(input("Введите номер пункта: "))
            except ValueError:
                print("Это должно быть число!")
                continue

            if sub_choice == 2:
                continue

            # Траты по категории
            print("\n" + "=" * 50)
            print("ОТЧЕТ: ТРАТЫ ПО КАТЕГОРИИ")
            print("=" * 50)

            # Показываем доступные категории
            if 'Категория' in transactions_df.columns:
                categories = transactions_df['Категория'].unique()
                print(f"\nДоступные категории ({len(categories)}):")
                for i, cat in enumerate(sorted(categories)[:15], 1):
                    print(f"  {i}. {cat}")
                if len(categories) > 15:
                    print(f"  ... и еще {len(categories) - 15} категорий")
            else:
                print("В данных нет колонки 'Категория'")
                continue

            category = input("\nВведите название категории: ").strip()

            if not category:
                print("Категория не может быть пустой")
                continue

            # Проверяем, существует ли такая категория
            if 'Категория' in transactions_df.columns:
                if category not in transactions_df['Категория'].values:
                    print(f"Категория '{category}' не найдена в данных")
                    continue

            date_input = input("Введите дату (YYYY-MM-DD или оставьте пустым для текущей): ").strip()

            if not date_input:
                date_input = datetime.now().strftime("%Y-%m-%d")
            else:
                # Проверяем формат даты
                try:
                    datetime.strptime(date_input, "%Y-%m-%d")
                except ValueError:
                    print(f"Неверный формат даты. Использую текущую дату.")
                    date_input = datetime.now().strftime("%Y-%m-%d")

            print(f"\nСоздаю отчет по категории '{category}'...")

            try:
                result = spending_by_category(transactions_df, category, date_input)

                if result is not None and not result.empty:
                    print(f"\nОтчет создан успешно!")
                    print(f"Сохранен в папке 'reports/'")

                    # Показываем результат
                    total_spent = result['Сумма'].sum()
                    print(f"\nИтоги по категории '{category}':")
                    print(f"   Дата анализа: {date_input}")
                    print(f"   Количество транзакций: {len(result)}")
                    print(f"   Общая сумма: {total_spent:.2f} руб")
                    print(f"   Средняя трата: {total_spent / len(result):.2f} руб")

                    print("\nДетали транзакций:")
                    print("-" * 60)
                    for _, row in result.iterrows():
                        print(f"{row['Дата']}: {row['Сумма']:.2f} руб - {row.get('Описание', 'Нет описания')}")
                else:
                    print(f"Нет данных для категории '{category}' за {date_input}")
            except Exception as e:
                print(f"Ошибка при создании отчета: {e}")

        elif choice == 4:
            # Статистика данных
            print("\n" + "=" * 50)
            print("СТАТИСТИКА ДАННЫХ")
            print("=" * 50)

            print(f"Общая статистика:")
            print(f"   Всего транзакций: {len(transactions_df)}")
            print(
                f"   Период: {transactions_df['Дата операции'].min().date()} - {transactions_df['Дата операции'].max().date()}")

            if 'Категория' in transactions_df.columns:
                categories_count = transactions_df['Категория'].nunique()
                print(f"\nКатегории:")
                print(f"   Уникальных категорий: {categories_count}")

                # Топ категорий
                print(f"\nТоп-10 категорий по количеству операций:")
                top_categories = transactions_df['Категория'].value_counts().head(10)
                for cat, count in top_categories.items():
                    percentage = (count / len(transactions_df)) * 100
                    print(f"   {cat}: {count} операций ({percentage:.1f}%)")

            if 'Тип операции' in transactions_df.columns:
                expenses = len(transactions_df[transactions_df['Тип операции'] == 'Расход'])
                income = len(transactions_df[transactions_df['Тип операции'] == 'Доход'])
                print(f"\nТипы операций:")
                print(f"   Расходов: {expenses}")
                print(f"   Доходов: {income}")

            if 'Сумма операции' in transactions_df.columns:
                print(f"\nФинансовые показатели:")
                if expenses > 0:
                    avg_expense = transactions_df[transactions_df['Тип операции'] == 'Расход']['Сумма операции'].mean()
                    print(f"   Средний расход: {avg_expense:.2f} руб")
                if income > 0:
                    avg_income = transactions_df[transactions_df['Тип операции'] == 'Доход']['Сумма операции'].mean()
                    print(f"   Средний доход: {avg_income:.2f} руб")

        elif choice == 5:
            print("\n" + "=" * 50)
            print("Спасибо за использование программы!")
            print("До новых встреч!")
            print("=" * 50)
            break

        else:
            print("Пожалуйста введите цифру от 1 до 5")

        # Пауза перед возвратом в меню
        if choice != 5:
            input("\nНажмите Enter чтобы продолжить...")


if __name__ == "__main__":
    main()


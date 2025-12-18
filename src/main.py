import json
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from config import EXCEL_FILE, REPORTS_DIR
from src.file_readers import load_transactions_from_excel
from src.reports import spending_by_category
from src.services import find_phone_numbers, investment_bank, simple_search
from src.utils import get_greeting, load_user_settings, save_report
from src.views import generate_financial_report


def parse_user_date(user_input: str) -> str:
    """
    Преобразует формат DD-MM-YYYY или DD.MM.YYYY
    в 'YYYY-MM-DD 12:00:00' для генерации отчета.
    """
    for fmt in ("%d-%m-%Y", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(user_input, fmt)
            return dt.replace(hour=12, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    raise ValueError(f"Неподдерживаемый формат даты: {user_input}")


def main() -> None:
    print("Привет, добро пожаловать в приложение для анализа банковских операций")

    # Загружаем транзакции
    try:
        transactions_df = load_transactions_from_excel(EXCEL_FILE)
        print(f"Успешно загружено {len(transactions_df)} транзакций")
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return

    while True:
        # Главное меню
        print("\nВыберите пункт меню:")
        print("1. Веб-страницы")
        print("2. Сервисы")
        print("3. Отчеты")
        print("4. Выход")

        try:
            user_choice = int(input("Введите число (1-4): "))
        except ValueError:
            print("Ошибка: введите число от 1 до 4")
            continue

        if user_choice == 1:
            # Веб-страницы
            print("1. Главная страница - Генерация финансового отчета")
            print("2. Назад")
            try:
                sub_choice = int(input("Выберите пункт: "))
            except ValueError:
                print("Ошибка: введите число")
                continue

            if sub_choice == 2:
                continue

            while True:
                try:
                    date_input = input("Введите дату для анализа (ДД.MM.ГГГГ): ")
                    target_date = parse_user_date(date_input)
                    break
                except ValueError as e:
                    print(e)

            try:
                report = generate_financial_report(transactions_df, target_date)
                report_file = REPORTS_DIR / f"financial_report_{target_date}.json"
                save_report(report, filename=report_file.name, reports_dir=REPORTS_DIR)
                print(f"Отчет создан и сохранен в {report_file}")
            except Exception as e:
                print(f"Ошибка при генерации отчета: {e}")

        elif user_choice == 2:
            # Сервисы
            print("1. Инвесткопилка")
            print("2. Простой поиск")
            print("3. Поиск по номерам")
            print("4. Назад")
            try:
                service_choice = int(input("Выберите сервис: "))
            except ValueError:
                print("Ошибка: введите число")
                continue

            if service_choice == 4:
                continue

            transactions_list = transactions_df.to_dict('records')

            if service_choice == 1:
                month = input("Введите месяц для Инвесткопилки (MM-YYYY): ")
                limit = int(input("Введите лимит округления (10, 50 или 100): "))
                total = investment_bank(month, transactions_list, limit)
                print(f"Сумма для Инвесткопилки: {total} руб")

            elif service_choice == 2:
                search_str = input("Введите строку для поиска транзакций: ")
                result = simple_search(transactions_list, search_str)
                print(f"Найдено {result['found_count']} транзакций")

            elif service_choice == 3:
                result = find_phone_numbers(transactions_list)
                print(f"Найдено {result['found_count']} транзакций с телефонными номерами")

        elif user_choice == 3:
            # Отчеты
            print("1. Траты по категории")
            print("2. Назад")
            try:
                report_choice = int(input("Выберите пункт: "))
            except ValueError:
                print("Ошибка: введите число")
                continue

            if report_choice == 2:
                continue

            category = input("Введите категорию для отчета: ")
            date_input = input("Введите дату (ДД.MM.ГГГГ) или оставьте пустым для текущей: ")
            if not date_input:
                date_input = datetime.now().strftime("%d.%m.%Y")

            try:
                target_date = parse_user_date(date_input)
                result_df = spending_by_category(transactions_df, category, target_date)
                print(result_df)
            except Exception as e:
                print(f"Ошибка при создании отчета: {e}")

        elif user_choice == 4:
            print("Выход из программы. До встречи!")
            break

        else:
            print("Введите число от 1 до 4")


if __name__ == "__main__":
    main()





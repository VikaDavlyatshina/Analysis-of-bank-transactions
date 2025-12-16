import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from config import EXCEL_FILE, REPORTS_DIR
from src.file_readers import load_transactions_from_excel
from src.reports import spending_by_category
from src.services import find_phone_numbers, investment_bank, simple_search
from src.utils import get_greeting, load_user_settings, save_report
from src.views import generate_financial_report

def parse_user_date(user_input: str) -> str:
    """
    Преобразует удобный формат даты DD-MM-YYYY или DD.MM.YYYY
    в строку формата 'YYYY-MM-DD 12:00:00' для функции generate_financial_report
    """
    for fmt in ("%d-%m-%Y", "%d.%m.%Y"):
        try:
            dt = datetime.strptime(user_input, fmt)
            return dt.replace(hour=12, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    raise ValueError(f"Неподдерживаемый формат даты: {user_input}")


def main() -> None:
    """
    Главная функция консольного приложения.
    Отвечает за основную логику проекта и связывает функциональности между собой
    """

    print("Привет, добро пожаловать в программу 'Приложение для анализа банковских операций'")


    print("Выберите необходимый пункт в меню:")
    print("1. Веб-страницы")
    print("2. Сервисы")
    print("3. Отчеты")
    print("4. Выход")

    try:
        user_choice = int(input("Выберите пункт меню (1-4): "))
    except ValueError:
        print("Это должно быть число! Попробуйте снова.")
        print("Введите число от 1 до 4")
        continue


    if user_choice == 1:
        print("Вы выбрали 'Веб-страницы'")
        print("1. Главная страница - Генерация финансового отчета")
        print("2. Назад")

        while True:
            try:
                date_input = input("Введите дату для анализа в формате 'ДД.ММ.ГГГГ'")
                target_date = parse_user_date(date_input)
                break
            except ValueError as e:
                print(e)

        try:
            transactions_df = load_transactions_from_excel(EXCEL_FILE)
            report = generate_financial_report(transactions_df, target_date)
            report_file = REPORTS_DIR / f"financial_report_{target_date}.json"
            save_report(report, filename=report_file.name, reports_dir=REPORTS_DIR)
            print(f"Отчет успешно создан и сохранен в {report_file}")
        except Exception as e:
            print(f"Ошибка при генерации отчета: {e}")

    elif user_choice == 2:
        print("Вы выбрали 'Сервисы'")
        print("1. Инвесткопилка")
        print("2. Простой поиск")
        print("3. Поиск по номерам")
        print("4. Назад")

    try:
        service_choice = int(input("Введите сервис: "))
    except ValueError:
                print("Это должно быть число")
                services_choice = None

            if service_choice == 1:
                month = input("Введите месяц для Инвесткопилки в формате - '12-2019'")
                limit = int(input("Введите лимит округления '10, 50 или 100': "))

                total = investment_bank(month, transactions.to_dict('records'), limit)
                print(f"Сумма для Инвесткопилки: {total} руб")

            elif service_choice == 2:
                print("Ищет транзакции по строке в описании и категории")
                search_str = input("Введите строку для поиска транзакций: ")
                result = simple_search(transactions_df.to_dict('records'), search_str)
                print(f"Найдено {result['found_count']} транзакций")

            elif service_choice == 3:
                result = find_phone_numbers(transactions_df.to_dict('records'))
                print(f"Найдено {result['found_count']} транзакций с телефонными номерами")


    elif user_choice == 3:
        print("Вы выбрали 'Отчеты'")
        print("1. Отчеты - 'Траты по категории'")
        print("2. Назад")
        while True:
            try:
                report_choice = int(input("Введите число для генерации отчета или выхода в Меню: "))
            except ValueError:
                print("Это должно быть число")
                services_choice = None

    elif user_choice == 4:
        print("Вы выбрали 'Выход'. Программа завершает работу.")
        break

    else:
        print("Это должно быть число! Попробуйте снова")
        print("Выберите число от 1 до 4: ")






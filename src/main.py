from datetime import datetime

from config import EXCEL_FILE, REPORTS_DIR, setup_main_logger
from src.file_readers import load_transactions_from_excel
from src.reports import spending_by_category
from src.services import find_phone_numbers, investment_bank, simple_search
from src.utils import save_report, prepare_transactions_for_services
from src.views import generate_financial_report


# Создаём logger
logger = setup_main_logger()


def parse_user_date(date_input: str) -> str:
    """
    Функция преобразования даты ввода
    Принимает:
    - ДД.ММ.ГГГГ
    - ДД-ММ-ГГГГ
    - пусто

    Возвращает:
    - YYYY-MM-DD (строка)
    """
    if not date_input.strip():
        return datetime.now().strftime("%Y-%m-%d")

    for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_input, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    raise ValueError("Неверный формат даты. Используйте ДД.ММ.ГГГГ")


def adapt_for_investment(date_str: str) -> str:
    """YYYY-MM-DD → YYYY-MM"""
    return date_str[:7]


def main() -> None:
    """Главная функция приложения для Анализа банковских транзакций.
     Связывает между собой все функциональности"""

    print("Привет, добро пожаловать в Приложение для анализа банковских операций")

    # Загружаем транзакции
    try:
        transactions_df = load_transactions_from_excel(EXCEL_FILE)
        logger.info(f"Успешно загружено {len(transactions_df)} транзакций из {EXCEL_FILE}")
        print(f"Успешно загружено {len(transactions_df)} транзакций")
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из {EXCEL_FILE}: {e}")
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
            logger.warning("Некорректный ввод главного меню")
            continue

        logger.debug(f"Пользователь выбрал пункт меню: {user_choice}")

        if user_choice == 1:
            # Веб-страницы
            print("1. Главная страница - Генерация финансового отчета")
            print("2. Назад")
            try:
                sub_choice = int(input("Выберите пункт: "))
            except ValueError:
                print("Ошибка: введите число")
                logger.warning("Некорректный ввод подменю веб-страниц")
                continue

            if sub_choice == 2:
                continue

            while True:
                try:
                    date_input = input("Введите дату для анализа (ДД.MM.ГГГГ): ")
                    target_date_str = parse_user_date(date_input)
                    target_date_for_report = target_date_str + " 12:00:00"
                    logger.info(f"Дата для анализа финансового отчета: {target_date_for_report}")
                    break

                except ValueError as e:
                    logger.warning(f"Некорректная дата! Ошибка: {e}")
                    print(e)

            try:
                report = generate_financial_report(transactions_df, target_date_for_report)
                logger.info(f"Генерация финансового отчета для даты: {target_date_for_report}")

                safe_date_str = target_date_for_report.replace(":", "-").replace(" ", "_")
                report_file = REPORTS_DIR / f"financial_report_{safe_date_str}.json"

                save_report(report, filename=report_file.name, reports_dir=REPORTS_DIR)
                logger.info(f"Отчет успешно сохранен в {report_file}")
                print(f"Отчет создан и сохранен в {report_file}")
            except Exception as e:
                logger.error(f"Ошибка генерации финансового отчета {target_date_for_report}: {e}")
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
                logger.warning("Некорректный ввод сервиса")
                continue

            logger.debug(f"Пользователь выбрал сервис: {service_choice}")

            if service_choice == 4:
                continue

            transactions_list = prepare_transactions_for_services(transactions_df)

            if service_choice == 1:
                date_input = input("Введите дату (ДД.ММ.ГГГГ) или пусто: ")

                try:
                    base_date = parse_user_date(date_input)  # YYYY-MM-DD
                    month = adapt_for_investment(base_date)  # YYYY-MM
                    logger.info(f"Выбран месяц для Инвесткопилки: {month}")
                except ValueError as e:
                    logger.warning(f"Некорректная дата для Инвесткопилки: {e}")
                    print(e)
                    continue

                limit_input = input("Введите лимит (10, 50, 100): ").strip()

                try:
                    limit = int(limit_input)
                    if limit not in (10, 50, 100):
                        print("Некорректный лимит, используем 10 по умолчанию")
                        logger.warning(f"Некорректный лимит: {limit}, используем 10")
                        limit = 10
                except ValueError:
                    logger.warning(f"Некорректный ввод лимита: {limit_input}, используем 10")
                    print("Некорректный ввод, используем 10 по умолчанию")
                    limit = 10

                total = investment_bank(month, transactions_list, limit)
                logger.info(f"Сумма для Инвесткопилки: {total:.2f} руб.")
                print(f"Сумма для Инвесткопилки: {total:.2f} руб.")

            elif service_choice == 2:
                search_str = input("Введите строку для поиска транзакций: ")
                result = simple_search(transactions_list, search_str, REPORTS_DIR)
                logger.info(f"Найдено {result['found_count']} транзакций по поиску '{search_str}'")
                print(f"Найдено {result['found_count']} транзакций")

            elif service_choice == 3:
                result = find_phone_numbers(transactions_list, REPORTS_DIR)
                logger.info(f"Найдено {result['found_count']} транзакций с телефонными номерами")
                print(f"Найдено {result['found_count']} транзакций с телефонными номерами")

        elif user_choice == 3:
            # Отчеты
            print("1. Траты по категории")
            print("2. Назад")

            try:
                report_choice = int(input("Выберите пункт: "))
            except ValueError:
                print("Ошибка: введите число")
                logger.warning("Некорректный ввод отчета")
                continue

            logger.debug(f"Пользователь выбрал отчет: {report_choice}")

            if report_choice == 2:
                continue

            # Показываем пользователю категории
            available_categories = transactions_df["Категория"].astype(str).unique()
            print("\nДоступные категории для анализа:")
            for cat in available_categories[:20]:
                print("-", cat)

            while True:
                category_input = input("\nВведите название категории для отчета: ").strip()
                matches = [c for c in available_categories if c.lower() == category_input.lower()]
                if matches:
                    category_corrected = matches[0]
                    logger.info(f"Выбрана категория для отчета: {category_corrected}")
                    break
                else:
                    logger.warning(f"Категория '{category_input}' не найдена в данных")
                    print(f"Ошибка: категория '{category_input}' не найдена в данных. Попробуйте еще раз.")

            date_input = input("Введите дату окончания периода (ДД.MM.ГГГГ) или оставьте пустым для текущей даты: ").strip()
            try:
                target_date_str = parse_user_date(date_input)
                end_date = datetime.strptime(target_date_str, "%Y-%m-%d")
                logger.info(f"Дата окончания периода для отчета: {end_date.strftime('%d.%m.%Y')}")
                print(f"Дата распознана: {end_date.strftime('%d.%m.%Y')}")
            except ValueError as e:
                logger.warning(f"Некорректная дата для отчета: {e}")
                print(f"Ошибка: {e}")
                continue

            print(f"\nАнализ трат по категории: '{category_corrected}'")
            print(f"Период: последние 3 месяца до {end_date.strftime('%d.%m.%Y')}")

            result_df = spending_by_category(transactions_df, category_corrected, target_date_str)
            if not result_df.empty:
                logger.info(f"Отчет по категории '{category_corrected}' сформирован в папку {REPORTS_DIR}")
                print(f"Отчет сформирован в папку {REPORTS_DIR}.")
            else:
                logger.info(f"Нет данных для отображения по категории '{category_corrected}'")
                print("Нет данных для отображения")

        elif user_choice == 4:
            logger.info("Программа завершает свою работу")
            print("Выход из программы. До встречи!")
            break

        else:
            print("Введите число от 1 до 4")
            logger.warning(f"Некорректный пункт меню: {user_choice}")


if __name__ == "__main__":
    main()



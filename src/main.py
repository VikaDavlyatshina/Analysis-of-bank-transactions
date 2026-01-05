from datetime import datetime

from config import EXCEL_FILE, REPORTS_DIR, setup_main_logger
from src.file_readers import load_transactions_from_excel
from src.reports import spending_by_category
from src.services import find_phone_numbers, investment_bank, simple_search
from src.utils import prepare_transactions_for_services, save_report
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


def main() -> None: # pragma: no cover
    """Главная функция приложения для Анализа банковских транзакций.
    Связывает между собой все функциональности"""

    print("═" * 50)
    print("🎉 Привет, добро пожаловать в Анализатор банковских операций!")
    print("═" * 50)

    # Загружаем транзакции
    try:
        transactions_df = load_transactions_from_excel(str(EXCEL_FILE))
        logger.info(f"Успешно загружено {len(transactions_df)} транзакций из {EXCEL_FILE}")
        print(f"✅ Успешно загружено {len(transactions_df)} транзакций")
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из {EXCEL_FILE}: {e}")
        print(f"❌ Ошибка при загрузке: {e}")
        return

    while True:
        # Главное меню
        print("\n" + "─" * 50)
        print("📋 ГЛАВНОЕ МЕНЮ")
        print("─" * 50)
        print("1. 🌐 Веб-страницы")
        print("2. 🔧 Сервисы")
        print("3. 📊 Отчеты")
        print("4. 🚪 Выход")
        print("─" * 50)

        try:
            user_choice = int(input("👉 Ваш выбор (1-4): "))
        except ValueError:
            print("❌ Пожалуйста, введите число от 1 до 4")
            logger.warning("Некорректный ввод главного меню")
            continue

        logger.debug(f"Пользователь выбрал пункт меню: {user_choice}")

        if user_choice == 1:
            # Веб-страницы
            print("\n" + "─" * 50)
            print("🌐 ВЕБ-СТРАНИЦЫ")
            print("─" * 50)
            print("1. 📈 Генерация финансового отчета")
            print("2. ↩️ Назад")
            print("─" * 50)

            try:
                sub_choice = int(input("👉 Выберите пункт: "))
            except ValueError:
                print("❌ Пожалуйста, введите число")
                logger.warning("Некорректный ввод подменю веб-страниц")
                continue

            if sub_choice == 2:
                continue

            target_date_for_report = None

            while True:
                try:
                    date_input = input("📅 Введите дату для анализа (ДД.MM.ГГГГ): ")
                    target_date_str = parse_user_date(date_input)
                    target_date_for_report = target_date_str + " 12:00:00"

                    logger.info(f"Дата для анализа финансового отчета: {target_date_for_report}")
                    break

                except ValueError as e:
                    logger.warning(f"Некорректная дата! Ошибка: {e}")
                    print(f"❌ {e}")

                    print("\nЧто вы хотите сделать?")
                    print("1. - Ввести дату еще раз")
                    print("2. - Вернуться в меню")

                    choice = input("👉 Ваш выбор: ").strip()

                    if choice == "2":
                        break
                    elif choice != "1":
                        print("⚠️ Неверный выбор. Возвращаемся в меню.")
                        break

            if target_date_for_report is None:
                continue

            try:
                report = generate_financial_report(transactions_df, target_date_for_report)
                logger.info(f"Генерация финансового отчета для даты: {target_date_for_report}")

                safe_date_str = target_date_for_report.replace(":", "-").replace(" ", "_")
                report_file = REPORTS_DIR / f"financial_report_{safe_date_str}.json"

                save_report(report, filename=report_file.name, reports_dir=REPORTS_DIR)
                logger.info(f"Отчет успешно сохранен в {report_file}")

                # Красивый вывод результата
                print("\n" + "✨" * 50)
                print("✅ ОТЧЕТ УСПЕШНО СОЗДАН!")
                print("✨" * 50)

                # Краткая статистика
                if "cards" in report and report["cards"]:
                    cards_count = len(report["cards"])
                    total_spent = sum(card.get("total_spent", 0) for card in report["cards"])
                    print(f"💳 Карт проанализировано: {cards_count}")
                    print(f"💰 Общая сумма расходов: {total_spent:,.2f} ₽")

                if "top_transactions" in report and report["top_transactions"]:
                    print(f"🏆 Крупнейших операций: {len(report['top_transactions'])}")

                print(f"\n📁 Файл: {report_file.name}")
                print("📂 Папка: reports/")
                print("─" * 50)
                print()

            except Exception as e:
                logger.error(f"Ошибка генерации финансового отчета {target_date_for_report}: {e}")
                print(f"\n❌ Ошибка при генерации отчета: {e}\n")

        elif user_choice == 2:
            # Сервисы
            print("\n" + "─" * 50)
            print("🔧 СЕРВИСЫ")
            print("─" * 50)
            print("1. 💰 Инвесткопилка")
            print("2. 🔍 Простой поиск")
            print("3. 📱 Поиск по номерам")
            print("4. ↩️ Назад")
            print("─" * 50)

            try:
                service_choice = int(input("👉 Выберите сервис: "))
            except ValueError:
                print("❌ Пожалуйста, введите число")
                logger.warning("Некорректный ввод сервиса")
                continue

            logger.debug(f"Пользователь выбрал сервис: {service_choice}")

            if service_choice == 4:
                continue


            transactions_list = prepare_transactions_for_services(transactions_df)

            if service_choice == 1:
                month = None

                while True:
                    date_input = input("📅 Введите дату (ДД.ММ.ГГГГ) или пусто: ")

                    try:
                        base_date = parse_user_date(date_input)
                        month = adapt_for_investment(base_date)
                        print(f"📊 Анализируем месяц: {month}")
                        break

                    except ValueError as e:
                        print(f"❌ {e}")

                        print("\nЧто вы хотите сделать?")
                        print("1. - Ввести дату еще раз")
                        print("2. - Вернуться в меню")

                        choice = input("👉 Ваш выбор: ").strip()

                        if choice == "2":
                            break
                        elif choice != "1":
                            print("⚠️ Неверный выбор. Возвращаемся в меню.")
                            break

                if month is None:
                    continue

                limit_input = input("💰 Введите лимит (10, 50, 100): ").strip()

                try:
                    limit = int(limit_input)
                    if limit not in (10, 50, 100):
                        print("⚠️ Некорректный лимит, используем 10")
                        limit = 10
                except ValueError:
                    print("⚠️ Неверный формат, используем 10")
                    limit = 10

                total = investment_bank(month, transactions_list, limit)

                # Красивый вывод результата
                print("\n" + "─" * 50)
                print("💰 РЕЗУЛЬТАТ: ИНВЕСТКОПИЛКА")
                print("─" * 50)
                print(f"📅 Месяц: {month}")
                print(f"💰 Лимит округления: {limit} ₽")
                print(f"💎 Итого накоплено: {total:.2f} ₽")
                print("─" * 50)
                print()


            elif service_choice == 2:

                while True:

                    search_str = input("🔍 Введите строку для поиска транзакций: ")

                    result = simple_search(transactions_list, search_str, REPORTS_DIR)
                    found_count = result["found_count"]

                    logger.info(f"Найдено {result['found_count']} транзакций по поиску '{search_str}'")

                    print("\n" + "─" * 50)
                    print("🔍 РЕЗУЛЬТАТЫ ПОИСКА")
                    print("─" * 50)
                    print(f"✨ Найдено транзакций: {found_count}")

                    if found_count > 0 or not search_str:
                        print(
                            "📁 Отчет сохранен в папке reports/")

                    print("─" * 50)
                    print()

                    if found_count > 0:
                        break

                    # Если ничего не найдено
                    print("❌ Ничего не найдено.")
                    print("\nЧто вы хотите сделать?")
                    print("1 — Попробовать ещё раз")
                    print("2 — Вернуться в меню")

                    choice = input("👉 Ваш выбор: ").strip()

                    if choice == "2":
                        break
                    elif choice != "1":
                        print("⚠️ Неверный выбор. Возвращаемся в меню сервисов.")
                        break


            elif service_choice == 3:

                result = find_phone_numbers(transactions_list, REPORTS_DIR)
                logger.info(f"Найдено {result['found_count']} транзакций с телефонными номерами")

                print("\n" + "─" * 50)
                print("📱 РЕЗУЛЬТАТЫ ПОИСКА")
                print("─" * 50)
                print(f"✨ Найдено транзакций с телефонными номерами: {result['found_count']}")
                print("📁 Отчет сохранен в папке reports/")
                print("─" * 50)
                print()

        elif user_choice == 3:
            # --- Блок отчетов ---
            while True:
                print("\n" + "─" * 50)
                print("📊 ОТЧЕТЫ")
                print("─" * 50)
                print("1. 💸 Траты по категории")
                print("2. ↩️ Назад")
                print("─" * 50)

                try:
                    report_choice = int(input("👉 Выберите пункт: "))
                except ValueError:
                    print("❌ Пожалуйста, введите число")
                    logger.warning("Некорректный ввод отчета")
                    continue

                if report_choice == 2:
                    break  # Возврат в главное меню
                elif report_choice != 1:
                    print("⚠️ Некорректный пункт. Попробуйте снова.")
                    continue

                # --- Выбор категории ---
                available_categories = sorted(transactions_df["Категория"].astype(str).unique())
                category_corrected = None  # Инициализация заранее

                while True:
                    print(f"\n📂 Доступные категории ({len(available_categories)}):")
                    print("─" * 50)
                    for i in range(0, len(available_categories), 4):
                        row = available_categories[i:i + 4]
                        print("  " + "  ".join(cat.ljust(20) for cat in row))

                    category_input = input("\n📝 Введите название категории (или 0 для выхода): ").strip()
                    if category_input == "0":
                        break  # Выход в меню отчетов

                    matches = [c for c in available_categories if c.lower() == category_input.lower()]
                    if matches:
                        category_corrected = matches[0]
                        print(f"✅ Выбрана категория: {category_corrected}")
                        break
                    else:
                        print(f"❌ Категория '{category_input}' не найдена. Попробуйте еще раз.")

                if category_corrected is None:
                    continue  # Пользователь вышел — возвращаемся к выбору отчета

                # --- Выбор даты ---
                target_date_str = None
                while True:
                    date_input = input("📅 Введите дату (ДД.MM.ГГГГ) или Enter для текущей даты: ").strip()
                    try:
                        target_date_str = parse_user_date(date_input)
                        end_date = datetime.strptime(target_date_str, "%Y-%m-%d")
                        print(f"📆 Анализируем период до: {end_date.strftime('%d.%m.%Y')}")
                        break
                    except ValueError as e:
                        print(f"❌ {e}")
                        print("1 — Ввести дату еще раз")
                        print("2 — Вернуться в меню отчетов")
                        choice = input("👉 Ваш выбор: ").strip()
                        if choice == "2":
                            break
                        elif choice != "1":
                            print("⚠️ Неверный выбор. Возвращаемся в меню отчетов.")
                            break

                if target_date_str is None:
                    continue  # Пользователь вышел из выбора даты — возвращаемся к выбору отчета

                # --- Генерация отчета ---
                print("\n" + "─" * 50)
                print(f"📊 АНАЛИЗ КАТЕГОРИИ: {category_corrected}")
                print("📅 Период: последние 3 месяца")
                print("─" * 50)

                result_df = spending_by_category(transactions_df, category_corrected, target_date_str)

                if not result_df.empty:
                    logger.info(f"Отчет по категории '{category_corrected}' сформирован в папку {REPORTS_DIR}")
                    print("\n✅ Отчет сформирован в папке reports/")
                else:
                    logger.info(f"Нет данных для отображения по категории '{category_corrected}'")
                    print("\n📭 Нет данных для отображения")

                print()

                # После генерации отчета предлагаем снова выбрать категорию
                retry = input("Хотите выбрать другую категорию? (д/н): ").strip().lower()
                if retry != "д":
                    break  # Возврат в главное меню

        elif user_choice == 4:
            print("\n" + "═" * 50)
            print("👋 Спасибо за использование программы!")
            print("   До новых встреч! 🎉")
            print("═" * 50)
            break

        else:
            print("❌ Пожалуйста, введите число от 1 до 4")
            logger.warning(f"Некорректный пункт меню: {user_choice}")


if __name__ == "__main__":
    main()

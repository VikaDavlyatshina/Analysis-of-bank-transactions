from datetime import datetime
from pathlib import Path

from config import EXCEL_FILE, REPORTS_DIR, setup_main_logger
from src.file_readers import load_transactions_from_excel
from src.reports import spending_by_category
from src.services import find_phone_numbers, investment_bank, simple_search
from src.utils import prepare_transactions_for_services, save_json_directly
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
        logger.debug("Получена пустая дата - используется текущая дата")
        return datetime.now().strftime("%Y-%m-%d")

    for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            result = datetime.strptime(date_input, fmt).strftime("%Y-%m-%d")
            logger.debug(f"Дата '{date_input}' успешно преобразована в '{result}' с форматом '{fmt}'")
            return result

        except ValueError:
            continue

    logger.error(f"Не удалось распознать формат даты: '{date_input}'")
    raise ValueError("Неверный формат даты. Используйте ДД.ММ.ГГГГ")


def adapt_for_investment(date_str: str) -> str:
    """YYYY-MM-DD → YYYY-MM"""

    result = date_str[:7]
    logger.debug(f"Дата '{date_str}' адаптирована для инвестиций: '{result}'")
    return result


def main() -> None:  # pragma: no cover
    """Главная функция приложения для Анализа банковских транзакций.
    Связывает между собой все функциональности"""

    logger.info("Запуск Анализатора банковских операций")

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
            logger.info(f"Пользователь выбрал пункт главного меню: {user_choice}")

        except ValueError:
            print("❌ Пожалуйста, введите число от 1 до 4")
            logger.warning("Пользователь ввел некорректное значение в главном меню (не число)")
            continue

        if user_choice == 1:
            logger.info("Пользователь выбрал раздел 'Веб-страницы'")
            # Веб-страницы
            print("\n" + "─" * 50)
            print("🌐 ВЕБ-СТРАНИЦЫ")
            print("─" * 50)
            print("1. 📈 Генерация финансового отчета")
            print("2. ↩️ Назад")
            print("─" * 50)

            try:
                sub_choice = int(input("👉 Выберите пункт: "))
                logger.info(f"В подменю 'Веб-страницы' выбран пункт: {sub_choice}")
            except ValueError:
                logger.warning("Некорректный ввод подменю веб-страниц")
                print("❌ Пожалуйста, введите число")
                continue

            if sub_choice == 2:
                logger.info("Возврат в главное меню из раздела 'Веб-страницы'")
                continue

            target_date_for_report = None

            while True:
                try:
                    date_input = input("📅 Введите дату для анализа (ДД.MM.ГГГГ): ")
                    logger.debug(f"Пользователь ввел дату для финансового отчета: '{date_input}'")

                    target_date_str = parse_user_date(date_input)
                    target_date_for_report = target_date_str + " 12:00:00"

                    logger.info(f"Дата для анализа финансового отчета: {target_date_for_report}")
                    break

                except ValueError as e:
                    logger.warning(f"Некорректная дата в финансовом отчете! Ошибка: {e}")
                    print(f"❌ {e}")

                    print("\nЧто вы хотите сделать?")
                    print("1. - Ввести дату еще раз")
                    print("2. - Вернуться в меню")

                    choice = input("👉 Ваш выбор: ").strip()

                    if choice == "2":
                        logger.info("Пользователь отменил ввод даты, возврат в меню")
                        break
                    elif choice != "1":
                        logger.warning(f"Неизвестный выбор после ошибки даты: '{choice}'")
                        print("⚠️ Неверный выбор. Возвращаемся в меню.")
                        break

            if target_date_for_report is None:
                continue

            try:
                # Генерируем отчет
                report = generate_financial_report(transactions_df, target_date_for_report)
                logger.info(f"Генерация финансового отчета для даты: {target_date_for_report}")

                # Создаем имя файла
                safe_date_str = target_date_for_report.replace(":", "-").replace(" ", "_")
                report_file = REPORTS_DIR / f"financial_report_{safe_date_str}.json"

                # Сохраняем напрямую (без save_report)
                save_json_directly(report, report_file)

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
                service_choice = int(input("👉 Ваш выбор (1-4): "))
                logger.info(f"Пользователь выбрал сервис: {service_choice}")
            except ValueError:
                logger.warning("Некорректный ввод номера сервиса")
                print("❌ Пожалуйста, введите число")
                continue

            if service_choice == 4:
                logger.info("Возврат в главное меню из раздела 'Сервисы'")
                continue

            transactions_list = prepare_transactions_for_services(transactions_df)

            if service_choice == 1:
                logger.info("Запуск сервиса 'Инвесткопилка'")
                month = None

                while True:
                    date_input = input("📅 Введите дату (ДД.ММ.ГГГГ) или пусто: ")
                    logger.debug(f"Ввод даты для инвесткопилки: '{date_input}'")

                    try:
                        base_date = parse_user_date(date_input)
                        month = adapt_for_investment(base_date)
                        logger.info(f"Выбран месяц для анализа инвесткопилки: {month}")
                        print(f"📊 Анализируем месяц: {month}")
                        break

                    except ValueError as e:
                        logger.warning(f"Ошибка парсинга даты для инвесткопилки: {e}")
                        print(f"❌ {e}")

                        print("\nЧто вы хотите сделать?")
                        print("1. - Ввести дату еще раз")
                        print("2. - Вернуться в меню")

                        choice = input("👉 Ваш выбор: ").strip()

                        if choice == "2":
                            logger.info("Отмена ввода даты для инвесткопилки")
                            break
                        elif choice != "1":
                            logger.warning(f"Неизвестный выбор в инвесткопилке: '{choice}'")
                            print("⚠️ Неверный выбор. Возвращаемся в меню.")
                            break

                if month is None:
                    continue

                limit_input = input("💰 Введите лимит (10, 50, 100): ").strip()
                logger.debug(f"Ввод лимита для инвесткопилки: '{limit_input}'")

                try:
                    limit = int(limit_input)
                    if limit not in (10, 50, 100):
                        logger.warning(f"Некорректный лимит {limit}, используется 10")
                        print("⚠️ Некорректный лимит, используем 10")
                        limit = 10

                except ValueError:
                    logger.warning(f"Неверный формат лимита '{limit_input}', используется 10")
                    print("⚠️ Неверный формат, используем 10")
                    limit = 10

                logger.info(f"Вызов investment_bank с параметрами: month={month}, limit={limit}")
                total = investment_bank(month, transactions_list, limit)
                logger.info(f"Результат инвесткопилки: накоплено {total:.2f}")

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
                logger.info("Запуск сервиса 'Простой поиск'")

                while True:
                    search_str = input("🔍 Введите строку для поиска транзакций: ")
                    logger.info(f"Поиск транзакций по строке: '{search_str}'")

                    # Декоратор @report_to_file сам сохранит файл
                    result = simple_search(transactions_list, search_str, REPORTS_DIR)
                    found_count = result["found_count"]

                    # Декоратор добавляет информацию о файле в результат
                    report_file = result.get("report_file", "")
                    report_filename = Path(report_file).name if report_file else ""

                    logger.info(f"Найдено {found_count} транзакций по поиску '{search_str}'")

                    print("\n" + "─" * 50)
                    print("🔍 РЕЗУЛЬТАТЫ ПОИСКА")
                    print("─" * 50)
                    print(f"✨ Найдено транзакций: {found_count}")

                    if found_count > 0 and report_file:
                        print(f"📁 Отчет сохранен: {report_filename}")
                    elif found_count > 0:
                        print("📁 Отчет сохранен в папке reports/")
                    elif not search_str.strip():
                        print("ℹ️  Поиск не выполнялся (пустая строка)")
                    else:
                        print("📭 Отчет не сохранен (нет результатов)")

                    print("─" * 50)
                    print()

                    if found_count > 0:
                        break

                    # Если ничего не найдено
                    logger.warning(f"По запросу '{search_str}' ничего не найдено")
                    print("❌ Ничего не найдено.")
                    print("\nЧто вы хотите сделать?")
                    print("1 — Попробовать ещё раз")
                    print("2 — Вернуться в меню")

                    choice = input("👉 Ваш выбор: ").strip()

                    if choice == "2":
                        logger.info("Выход из простого поиска в меню")
                        break
                    elif choice != "1":
                        logger.warning(f"Неизвестный выбор в простом поиске: '{choice}'")
                        print("⚠️ Неверный выбор. Возвращаемся в меню сервисов.")
                        break

            elif service_choice == 3:
                logger.info("Запуск сервиса 'Поиск по номерам'")

                # Декоратор @report_to_file сам сохранит файл
                result = find_phone_numbers(transactions_list, REPORTS_DIR)
                found_count = result["found_count"]

                # Декоратор добавляет информацию о файле в результат
                report_file = result.get("report_file", "")
                report_filename = "find_phone_numbers_report.json"

                logger.info(f"Найдено {found_count} транзакций с телефонными номерами")

                print("\n" + "─" * 50)
                print("📱 РЕЗУЛЬТАТЫ ПОИСКА")
                print("─" * 50)
                print(f"✨ Найдено транзакций с телефонными номерами: {found_count}")

                if found_count > 0 and report_file:
                    print(f"📁 Отчет сохранен: {report_filename}")
                elif found_count > 0:
                    print(f"📁 Отчет сохранен: {report_filename}")
                else:
                    print("📭 Отчет не сохранен (нет результатов)")

                print("─" * 50)
                print()

        elif user_choice == 3:
            logger.info("Пользователь выбрал раздел 'Отчеты'")
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
                    logger.info(f"Выбор в меню отчетов: {report_choice}")
                except ValueError:
                    logger.warning("Некорректный ввод отчета")
                    print("❌ Пожалуйста, введите число")
                    continue

                if report_choice == 2:
                    logger.info("Возврат из меню отчетов в главное меню")
                    break  # Возврат в главное меню
                elif report_choice != 1:
                    logger.info("Возврат из меню отчетов в главное меню")
                    print("⚠️ Некорректный пункт. Попробуйте снова.")
                    continue

                # --- Выбор категории ---
                available_categories = sorted(transactions_df["Категория"].astype(str).unique())
                category_corrected = None  # Инициализация

                logger.info(f"Доступно категорий для анализа: {len(available_categories)}")
                logger.debug(f"Список категорий: {available_categories[:10]}...")

                while True:
                    print(f"\n📂 Доступные категории ({len(available_categories)}):")
                    print("─" * 50)
                    for i in range(0, len(available_categories), 4):
                        row = available_categories[i : i + 4]
                        print("  " + "  ".join(cat.ljust(20) for cat in row))

                    category_input = input("\n📝 Введите название категории (или 0 для выхода): ").strip()

                    logger.debug(f"Пользователь ввел категорию: '{category_input}'")

                    if category_input == "0":
                        logger.info("Пользователь выбрал выход из выбора категории")
                        break  # Выход в меню отчетов

                    matches = [c for c in available_categories if c.lower() == category_input.lower()]
                    if matches:
                        category_corrected = matches[0]
                        logger.info(f"Выбрана категория: {category_corrected}")
                        print(f"✅ Выбрана категория: {category_corrected}")
                        break
                    else:
                        logger.warning(f"Категория '{category_input}' не найдена среди доступных")
                        print(f"❌ Категория '{category_input}' не найдена. Попробуйте еще раз.")

                if category_corrected is None:
                    logger.info("Категория не выбрана, возврат к выбору отчета")
                    continue  # Пользователь вышел — возвращаемся к выбору отчета

                # --- Выбор даты ---
                target_date_str = None
                while True:
                    date_input = input("📅 Введите дату (ДД.MM.ГГГГ) или Enter для текущей даты: ").strip()
                    logger.debug(f"Ввод даты для отчета по категории: '{date_input}'")

                    try:
                        target_date_str = parse_user_date(date_input)
                        end_date = datetime.strptime(target_date_str, "%Y-%m-%d")
                        logger.info(f"Установлена дата для отчета по категории: {target_date_str}")
                        print(f"📆 Анализируем период до: {end_date.strftime('%d.%m.%Y')}")
                        break
                    except ValueError as e:
                        print(f"❌ {e}")

                        print("1 — Ввести дату еще раз")
                        print("2 — Вернуться в меню отчетов")
                        choice = input("👉 Ваш выбор: ").strip()
                        if choice == "2":
                            logger.info("Отмена ввода даты для отчета по категории")
                            break
                        elif choice != "1":
                            logger.warning(f"Неизвестный выбор после ошибки даты: '{choice}'")
                            print("⚠️ Неверный выбор. Возвращаемся в меню отчетов.")
                            break

                if target_date_str is None:
                    logger.info("Дата не установлена, возврат к выбору отчета")
                    continue  # Пользователь вышел из выбора даты — возвращаемся к выбору отчета

                # --- Генерация отчета ---
                logger.info(f"Генерация отчета по категории '{category_corrected}' на дату '{target_date_str}'")

                print("\n" + "─" * 50)
                print(f"📊 АНАЛИЗ КАТЕГОРИИ: {category_corrected}")
                print("📅 Период: последние 3 месяца")
                print("─" * 50)

                result_df = spending_by_category(transactions_df, category_corrected, target_date_str)

                if not result_df.empty:
                    # Декоратор уже сохранил файл, мы только информируем пользователя
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
            logger.info("Завершение работы Анализатора банковских операций")
            break

        else:
            print("❌ Пожалуйста, введите число от 1 до 4")
            logger.warning(f"Некорректный пункт меню: {user_choice}")


if __name__ == "__main__":
    main()

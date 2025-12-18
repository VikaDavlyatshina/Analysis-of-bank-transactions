import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

from config import setup_utils_logger, REPORTS_DIR

# Создаем логгер
logger = setup_utils_logger()

# Загрузка переменных из .env файла
load_dotenv()

API_KEY_Freecurrencyapi = os.getenv("API_KEY_Freecurrencyapi")  # Получение токена API для валют
API_KEY_twelvedata = os.getenv("API_KEY_twelvedata")  # Получение токена API для валют


def filter_transactions_by_date(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Фильтрует транзакции по диапазону дат"""

    temp_df = df.copy()  # Создаём копию

    mask = (temp_df["Дата операции"] >= start_date) & (temp_df["Дата операции"] <= end_date)
    filtered_df = temp_df.loc[mask]

    logger.info(f"Отфильтровано по дате: {len(filtered_df)}")
    return filtered_df


def filter_successful_transaction(df: pd.DataFrame) -> pd.DataFrame:
    """Фильтрация успешных транзакций"""

    temp_df = df.copy()

    mask = temp_df["Статус"] == "OK"
    successful_df = temp_df.loc[mask]

    return successful_df


def get_greeting(now: Optional[datetime] = None) -> str:
    """
    Возвращает приветствие в зависимости от текущего времени.
    Аргумент now: datetime (если None — возьмёт текущее время).
    """
    try:
        if now is None:
            now = datetime.now()
        hour = now.hour
        if 5 <= hour < 12:
            return "Доброе утро"
        if 12 <= hour < 17:
            return "Добрый день"
        if 17 <= hour < 22:
            return "Добрый вечер"
        return "Доброй ночи"
    except Exception:
        logger.exception("Ошибка при формировании приветствия")
        return "Добрый день"


def get_currency_rates(
    apikey: str, base_currency: str = "RUB", currencies: List[str] = None
) -> Dict[str, float] | None:
    """Получает актуальные курсы валют от Freecurrencyapi.com."""

    # Проверка API ключа
    if not apikey:
        logger.error("API ключ для Freecurrencyapi отсутствует!")
        return None

    url = "https://api.freecurrencyapi.com/v1/latest"

    params = {"apikey": apikey, "base_currency": base_currency}

    # Добавляем валюты только если они указаны
    if currencies:
        params["currencies"] = ",".join(currencies)  # Преобразуем список в строку

    try:
        # Используем Freecurrencyapi
        response = requests.get(url, params=params, timeout=10)

        response.raise_for_status()  # Проверяет HTTP ошибки
        data = response.json()

        # Извлекаем курсы из ответа
        rates = data.get("data", {})
        logger.info(f"Получены сырые курсы: {rates}")

        # Инвертируем курсы для отображения стоимости 1 единицы иностранной валюты в рублях
        inverted_rates = {}
        for currency, rate in rates.items():
            if rate > 0:  # защита от деления на ноль
                inverted_rates[currency] = round(1 / rate, 2)
            else:
                inverted_rates[currency] = 0.0
                logger.info(f"Нулевой курс для {currency}")

        logger.info(f"Инвертированные курсы: {inverted_rates}")
        return inverted_rates

    except requests.exceptions.HTTPError as e:
        logger.exception(f" Ошибка HTTP: {e}")
        return None

    except requests.exceptions.RequestException as e:
        logger.exception(f" Ошибка при запросе к API: {e}")
        return None

    except ZeroDivisionError:
        logger.exception(" Ошибка: деление на ноль при инверсии курсов")
        return None


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """
    Получает цены акций через Twelve Data API
    """
    # Проверка API ключа
    if not API_KEY_twelvedata:
        logger.error("API ключ для Twelve Data отсутствует!")
        return []

    logger.info(f"Начало запроса цен для {len(stocks)} акций")
    results = []

    # Запасные цены для популярных акций
    fallback_prices = {
        "AAPL": 150.0,  # Apple
        "GOOGL": 130.0,  # Google
        "MSFT": 300.0,  # Microsoft
        "AMZN": 120.0,  # Amazon
        "TSLA": 200.0,  # Tesla
        "META": 250.0,  # Meta (Facebook)
        "NVDA": 400.0,  # NVIDIA
        "NFLX": 500.0,  # Netflix
    }

    for symbol in stocks:
        try:
            # Запрос к API
            url = "https://api.twelvedata.com/price"
            params = {"symbol": symbol, "apikey": API_KEY_twelvedata}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # Проверяет HTTP ошибки
            data = response.json()

            # Проверяем что цена есть в ответе
            if "price" in data and data["price"]:
                price = float(data["price"])
                results.append({"stock": symbol, "price": round(price, 2), "source": "twelvedata"})

                logger.info(f"Цена {symbol}: ${price:.2f} (реальные данные)")

            else:
                # Если нет цены в ответе - используем заглушку
                fallback_price = fallback_prices.get(symbol, 100.0)
                results.append({"stock": symbol, "price": fallback_price, "source": "fallback_no_data"})
                logger.warning(f"Цена {symbol}: ${fallback_price:.2f} (заглушка - нет данных в API)")

        except requests.exceptions.HTTPError:
            # Ошибка HTTP
            fallback_price = fallback_prices.get(symbol, 100.0)
            results.append({"stock": symbol, "price": fallback_price, "source": "fallback_http_error"})
            logger.warning(f"Цена {symbol}: ${fallback_price:.2f} (заглушка - ошибка HTTP)")

        except (requests.exceptions.RequestException, Exception):
            # Другие ошибки(сеть, таймаут и т.д)
            fallback_price = fallback_prices.get(symbol, 100.0)
            results.append({"stock": symbol, "price": fallback_price, "source": "fallback_error"})
            logger.warning(f"Цена {symbol}: ${fallback_price:.2f} (заглушка - ошибка подключения)")

    # Статистика
    real_data_count = sum(1 for stock in results if stock["source"] == "twelvedata")
    fallback_count = len(results) - real_data_count

    logger.info(f"Итог: {real_data_count}/{len(stocks)} реальных данных, {fallback_count} заглушек")

    return results


def load_user_settings(file_name: str) -> Dict[str, Any]:
    """Загружает пользовательские настройки из user_settings.json"""

    # 1. Настройки по умолчанию
    default_settings = {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]}

    # 2. Проверяем существование файла
    settings_path = Path(file_name)

    if not settings_path.exists():
        logger.warning(f"Файл настроек '{file_name}' не найден. Используем настройки по умолчанию.")
        return default_settings

    # 3. Пытаемся прочитать файл
    try:
        with open(settings_path, "r", encoding="utf-8") as file:
            user_settings = json.load(file)

        # 4. Проверяем структуру данных
        if not isinstance(user_settings, dict):
            logger.error(f"Файл '{file_name}' должен содержать словарь (dict), а не {type(user_settings).__name__}")
            return default_settings

        # 5. Проверяем наличие обязательных полей
        # Если каких-то полей нет — дополняем значениями по умолчанию
        result = default_settings.copy()  # Копируем defaults

        for key in default_settings:
            if key in user_settings:
                result[key] = user_settings[key]
            else:
                logger.info(f"В настройках отсутствует поле '{key}', используем значение по умолчанию")

        logger.info(f"Настройки загружены из файла '{file_name}'")
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка JSON в файле '{file_name}': {e}. Используем настройки по умолчанию.")
        return default_settings

    except Exception as e:
        logger.error(f"Неизвестная ошибка при чтении файла '{file_name}': {e}")
        return default_settings


def convert_transactions_to_rub(df: pd.DataFrame, currency_rates: Dict[str, float]) -> pd.DataFrame:
    """Конвертирует все сумму операций в рубли"""

    df = df.copy()

    def convert_row(row):
        currency = row["Валюта операции"]
        amount = row["Сумма операции"]

        if currency == "RUB":
            return amount

        rate = currency_rates.get(currency)

        if rate is None:
            logger.warning(f"Нет курса для валюты {currency}")
            return amount  # или 0, или выбросить строку

        return amount * rate

    df["Сумма операции"] = df.apply(convert_row, axis=1)

    return df


def save_report(report: dict, filename: str = "report.json", reports_dir: Path = None) -> bool:
    """Сохраняет отчет в JSON файл в указанной папке"""
    if reports_dir is None:
        reports_dir = REPORTS_DIR

    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
        file_path = reports_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"Отчет сохранен в {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения отчета: {e}")
        return False


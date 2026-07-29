import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

from config import setup_utils_logger

# Создаем логгер
logger = setup_utils_logger()

# Загрузка переменных из .env файла
load_dotenv()

API_KEY_Freecurrencyapi = os.getenv("API_KEY_Freecurrencyapi")  # Получение токена API для валют
API_KEY_twelvedata = os.getenv("API_KEY_twelvedata")  # Получение токена API для валют


def filter_transactions_by_date(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
       Фильтрует транзакции по заданному диапазону дат включительно

    Параметры:
         df:DataFrame - DataFrame, содержащий столбец 'Дата операции'
        start_date: datetime - Начальная дата диапазона
        end_date: datetime - Конечная дата диапазона
    Возвращает: Отфильтрованную копию DataFrame только с транзакциями в указанном диапазоне
    """

    temp_df = df.copy()  # Создаём копию, чтобы не повредить исходные данные

    # Создаем булеву маску для фильтрации
    # Даты транзакций должна быть больше или равны end_date(Дате начала) и меньше или равны end_date (Дате окончания)
    mask = (temp_df["Дата операции"] >= start_date) & (temp_df["Дата операции"] <= end_date)
    filtered_df = temp_df.loc[mask]

    logger.info(f"Отфильтровано по дате: {len(filtered_df)} записей из {len(df)}")
    return filtered_df


def filter_successful_transaction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Фильтрует транзакции, оставляя только успешные (со статусом 'OK')
    Параметры:
        Принимает DataFrame, содержащий столбец 'Статус'
    Возвращает:
        Отфильтрованную копию DataFrame только с успешными транзакциями (OK)

    """

    temp_df = df.copy()  # Создаём копию, чтобы не повредить исходные данные

    # Критерий фильтрации
    mask = temp_df["Статус"] == "OK"
    # Применение фильтра
    successful_df = temp_df.loc[mask]

    return successful_df


def get_greeting(now: Optional[datetime] = None) -> str:
    """
    Генерирует текстовое приветствие в зависимости от времени суток.

    Параметр:
          Now: datetime|None - Принимает Дату со временем. Если Дата со временем не указана - возьмёт текущее время
    """

    try:
        if now is None:
            now = datetime.now()
        hour = now.hour

        # Определяем приветствие по времени суток
        if 5 <= hour < 12:
            return "Доброе утро"
        if 12 <= hour < 17:
            return "Добрый день"
        if 17 <= hour < 22:
            return "Добрый вечер"
        return "Доброй ночи"

    except Exception as e:
        if isinstance(e, (AttributeError, TypeError)):
            logger.error(f"Некорректный объект времени: {e}")
        elif isinstance(e, ValueError):
            logger.error(f"Некорректное значение времени: {e}")
        else:
            # Неожиданные ошибки логируем полностью
            logger.exception(f"Неожиданная ошибка при формировании приветствия: {e}")

        return "Добрый день"


def get_currency_rates(
    apikey: str, base_currency: str = "RUB", currencies: Optional[List[str]] = None
) -> Optional[Dict[str, float]]:
    """
    Получает актуальные курсы валют от Freecurrencyapi.com.

    Функция делает запрос к API и возвращает курсы валют, инвертированные
    для отображения стоимости 1 единицы иностранной валюты в рублях."""

    # Проверка наличия API ключа
    if not apikey:
        logger.error("API ключ для Freecurrencyapi отсутствует!")
        return None

    url = "https://api.freecurrencyapi.com/v1/latest"

    params = {"apikey": apikey, "base_currency": base_currency}

    # Добавляем валюты только если они указаны
    # API ожидает строку с валютами через запятую: "USD, EUR, GBP"
    if currencies:
        params["currencies"] = ",".join(currencies)  # Преобразуем список в строку

    try:
        #  # Используем Freecurrencyapi с таймаутом 10 секунд для избежания зависаний
        response = requests.get(url, params=params, timeout=10)

        response.raise_for_status()  # Проверяет HTTP ошибки
        data = response.json()

        #  Извлекаем курсы из ответа
        # API возвращает данные в формате {"data": {"USD": 0.011, "EUR": 0.010}}
        rates = data.get("data", {})
        logger.info(f"Получены сырые курсы: {rates}")

        # Инвертируем курсы для отображения стоимости 1 единицы иностранной валюты в рублях
        # API возвращает: 1 RUB = 0.011 USD (1 рубль = 0.011 доллара)
        # Нам нужно: 1 USD = X RUB (1 доллар = X рублей)
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
        logger.exception(f"Ошибка HTTP при запросе курсов валют: {e}")
        return None

    except requests.exceptions.RequestException as e:
        # Сетевые ошибки: таймаут, проблемы с соединением и т.д.
        logger.exception(f" Ошибка сети при запросе к API валют: {e}")
        return None

    except ZeroDivisionError:
        logger.exception("Критическая ошибка: деление на ноль при инверсии курсов")
        return None

    except (KeyError, ValueError, TypeError) as e:
        # Ошибки парсинга JSON или неожиданная структура ответа
        logger.exception(f"Ошибка обработки ответа API: {e}")
        return None


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """
    Получает актуальные цены акций через Twelve Data API.

    Особенность: функция использует систему fallback (запасных значений) для
    обеспечения работы даже при сбоях API. Если API недоступно или возвращает
    ошибку, используются заранее заданные резервные цены

    Параметры:
        stocks: List[str] - Список тикеров акций

    Возвращает: List[Dict[str, Any]] - Список словарей с ценами акций
    """
    # Проверка API ключа
    if not API_KEY_twelvedata:
        logger.error("API ключ для Twelve Data отсутствует!")
        return []

    if not stocks:  # Если список акций пустой
        logger.warning("Получен пустой список акций")
        return []

    logger.info(f"Начало запроса цен для {len(stocks)} акций")
    results = []

    # Запасные цены для популярных акций
    fallback_prices = {
        "AAPL": 270.0,  # Apple
        "GOOGL": 142.0,  # Google
        "MSFT": 470.0,  # Microsoft
        "AMZN": 225.0,  # Amazon
        "TSLA": 245.0,  # Tesla
        "META": 355.0,  # Meta
        "NVDA": 188.0,  # NVIDIA
        "NFLX": 615.0,  # Netflix
        "SBER": 280.0,  # Сбербанк
        "GAZP": 120.0,  # Газпром
    }

    for symbol in stocks:
        if not symbol or not isinstance(symbol, str):
            continue  # Пропускаем некорректные значения

        symbol_upper = symbol.strip().upper()  # Приводим к верхнему регистру

        try:
            # Запрос к API
            url = "https://api.twelvedata.com/price"
            params = {"symbol": symbol_upper, "apikey": API_KEY_twelvedata}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # Проверяет HTTP ошибки
            data = response.json()

            # Проверяем что цена есть в ответе
            if "price" in data and data["price"]:
                price = float(data["price"])
                results.append({"stock": symbol_upper, "price": round(price, 2)})
                logger.info(f"Цена {symbol_upper}: ${price:.2f} (реальные данные)")

            else:
                # Если нет цены в ответе - используем заглушку
                fallback_price = fallback_prices.get(symbol_upper, 100.0)
                results.append({"stock": symbol_upper, "price": fallback_price})
                logger.warning(f"Цена {symbol_upper}: ${fallback_price:.2f} (заглушка - нет данных в API)")

        except requests.exceptions.HTTPError:
            # Ошибка HTTP (404, 429, 500 и т.д.)
            fallback_price = fallback_prices.get(symbol_upper, 100.0)
            results.append({"stock": symbol_upper, "price": fallback_price})
            logger.warning(f"Цена {symbol_upper}: ${fallback_price:.2f} (заглушка - ошибка HTTP)")

        except (requests.exceptions.RequestException, Exception):
            # Другие ошибки(сеть, таймаут и т.д)
            fallback_price = fallback_prices.get(symbol_upper, 100.0)
            results.append({"stock": symbol_upper, "price": fallback_price})
            logger.warning(f"Цена {symbol_upper}: ${fallback_price:.2f} (заглушка - ошибка подключения)")

    # Статистика - считаем сколько реальных данных получили
    logger.info(f"Итог: получены цены для {len(results)} акций")

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
    """Конвертирует все суммы операций в рубли"""

    df = df.copy()

    def convert_row(row: pd.Series) -> float:
        currency = str(row["Валюта операции"])  # явно str
        amount_val = row["Сумма операции"]

        # явно float
        try:
            amount = float(amount_val)
        except (TypeError, ValueError):
            amount = 0.0

        if currency == "RUB":
            return amount

        rate = currency_rates.get(currency)
        if rate is None:
            logger.warning(f"Нет курса для валюты {currency}")
            return amount

        return amount * rate

    df["Сумма операции"] = df.apply(convert_row, axis=1).astype(float)

    return df


def save_json_directly(data: dict, file_path: Path) -> bool:
    """Прямое сохранение JSON файла (альтернатива save_report)."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f" Файл сохранен: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения файла {file_path}: {e}")
        return False


def prepare_transactions_for_services(df: pd.DataFrame) -> list[dict]:
    """Возвращает список словарей для сервисов с датами в строковом формате"""
    df_copy = df.copy()

    if "Дата операции" in df_copy.columns:
        # Безопасное преобразование datetime в строку
        df_copy["Дата операции"] = df_copy["Дата операции"].apply(
            lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if isinstance(x, (datetime, pd.Timestamp)) else str(x)
        )

    if "Дата платежа" in df_copy.columns:
        # Безопасное преобразование datetime в строку
        df_copy["Дата платежа"] = df_copy["Дата платежа"].apply(
            lambda x: x.strftime("%Y-%m-%d") if isinstance(x, (datetime, pd.Timestamp)) else str(x)
        )

    return df_copy.to_dict(orient="records")

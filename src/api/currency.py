import os
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

from config import setup_utils_logger

load_dotenv()
API_KEY_Freecurrencyapi = os.getenv("API_KEY_Freecurrencyapi")

logger = setup_utils_logger()


def get_currency_rates(
    apikey: str, base_currency: str = "RUB", currencies: Optional[List[str]] = None
) -> Optional[Dict[str, float]]:
    if not apikey:
        logger.error("API ключ для Freecurrencyapi отсутствует!")
        return None

    url = "https://api.freecurrencyapi.com/v1/latest"
    params = {"apikey": apikey, "base_currency": base_currency}

    if currencies:
        params["currencies"] = ",".join(currencies)

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        rates = data.get("data", {})
        logger.info(f"Получены сырые курсы: {rates}")

        inverted_rates = {}
        for currency, rate in rates.items():
            if rate > 0:
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
        logger.exception(f"Ошибка сети при запросе к API валют: {e}")
        return None
    except ZeroDivisionError:
        logger.exception("Критическая ошибка: деление на ноль при инверсии курсов")
        return None
    except (KeyError, ValueError, TypeError) as e:
        logger.exception(f"Ошибка обработки ответа API: {e}")
        return None

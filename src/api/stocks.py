import os
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from config import setup_utils_logger

load_dotenv()
API_KEY_twelvedata = os.getenv("API_KEY_twelvedata")

logger = setup_utils_logger()

fallback_prices = {
    "AAPL": 270.0,
    "GOOGL": 142.0,
    "MSFT": 470.0,
    "AMZN": 225.0,
    "TSLA": 245.0,
    "META": 355.0,
    "NVDA": 188.0,
    "NFLX": 615.0,
    "SBER": 280.0,
    "GAZP": 120.0,
}


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    if not API_KEY_twelvedata:
        logger.error("API ключ для Twelve Data отсутствует!")
        return []

    if not stocks:
        logger.warning("Получен пустой список акций")
        return []

    logger.info(f"Начало запроса цен для {len(stocks)} акций")
    results = []

    for symbol in stocks:
        if not symbol or not isinstance(symbol, str):
            continue

        symbol_upper = symbol.strip().upper()

        try:
            url = "https://api.twelvedata.com/price"
            params = {"symbol": symbol_upper, "apikey": API_KEY_twelvedata}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "price" in data and data["price"]:
                price = float(data["price"])
                results.append({"stock": symbol_upper, "price": round(price, 2)})
                logger.info(f"Цена {symbol_upper}: ${price:.2f} (реальные данные)")
            else:
                fallback_price = fallback_prices.get(symbol_upper, 100.0)
                results.append({"stock": symbol_upper, "price": fallback_price})
                logger.warning(f"Цена {symbol_upper}: ${fallback_price:.2f} (заглушка - нет данных в API)")

        except requests.exceptions.HTTPError:
            fallback_price = fallback_prices.get(symbol_upper, 100.0)
            results.append({"stock": symbol_upper, "price": fallback_price})
            logger.warning(f"Цена {symbol_upper}: ${fallback_price:.2f} (заглушка - ошибка HTTP)")

        except (requests.exceptions.RequestException, Exception):
            fallback_price = fallback_prices.get(symbol_upper, 100.0)
            results.append({"stock": symbol_upper, "price": fallback_price})
            logger.warning(f"Цена {symbol_upper}: ${fallback_price:.2f} (заглушка - ошибка подключения)")

    logger.info(f"Итог: получены цены для {len(results)} акций")
    return results

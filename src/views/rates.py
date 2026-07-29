from typing import Any, Dict, List, Optional

from config import setup_views_logger

logger = setup_views_logger()


def format_currency_rates(raw_rates: Optional[Dict[str, float]]) -> List[Dict[str, Any]]:
    logger.debug(f"Форматирование курсов валют. Получено курсов: {len(raw_rates) if raw_rates else 0}")

    if not raw_rates:
        logger.info("Нет данных о курсах валют, возвращаем пустой список")
        return []

    formatted_rates = [{"currency": cur, "rate": rate} for cur, rate in raw_rates.items()]
    logger.debug(f"Отформатировано {len(formatted_rates)} курсов валют")

    return formatted_rates


def format_stock_prices(raw_stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    logger.debug(f"Форматирование цен акций. Получено акций: {len(raw_stocks)}")

    if not raw_stocks:
        logger.info("Нет данных о ценах акций, возвращаем пустой список")
        return []

    formatted_stocks = []
    for stock in raw_stocks:
        try:
            formatted_stock = {
                "stock": stock.get("stock", ""),
                "price": float(stock.get("price", 0.0)),
            }
            formatted_stocks.append(formatted_stock)
        except Exception as e:
            logger.warning(f"Ошибка форматирования данных акции {stock}: {e}")

    logger.debug(f"Отформатировано {len(formatted_stocks)} цен акций")
    return formatted_stocks
